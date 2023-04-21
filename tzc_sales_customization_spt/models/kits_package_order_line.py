from odoo import fields,models,api,_

class kits_package_order_line(models.Model):
    _name = 'kits.package.order.line'
    _description = 'To create package order line in sale order.'

    order_id = fields.Many2one('sale.order','Order')
    product_id = fields.Many2one('kits.package.product','Package Product',required="1")
    pack_image= fields.Char('Package Image',related="product_id.pack_product_image")
    qty = fields.Integer('Qty',default="1")
    sale_price = fields.Float('Sale Price')
    discount_amount = fields.Float('Discount Amount')
    subtotal = fields.Float('Subtotal',compute="_compute_subtotal",store=True,compute_sudo=True)
    pack_price = fields.Float('Package Price')
    backup_order = fields.Many2one('sale.order.backup.spt','Backup Order')
    availability = fields.Selection([('available','Available'),('out_of_stock','Out Of Stock')],string="Availability",compute='_compute_availability')
    
    discount = fields.Float('Discount (%)')

    @api.onchange('product_id','discount','qty','sale_price')
    def _onchange_discount(self):
        for record in self:
            amount = record.sale_price - (record.sale_price * record.discount * 0.01)
            record.pack_price = round(amount,2)
            record.discount_amount = round(record.sale_price - amount,2)
    
    @api.onchange('product_id','qty','discount_amount','sale_price')
    def _onchange_discounted_price(self):
        for record in self:
            try:
                record.discount = round(record.discount_amount * 100 /record.sale_price,2)
            except:
                record.discount = 0.00
            record.pack_price = round(record.sale_price - record.discount_amount,2)
    
    @api.onchange('product_id','qty','pack_price','sale_price')
    def _onchange_pack_price(self):
        for record in self:
            record.discount_amount = round(record.sale_price-record.pack_price,2)
            try:
                record.discount = round(((record.sale_price -  record.pack_price)*100)/record.sale_price,2)
            except:
                record.discount = 0.00

    @api.depends('qty','product_id','pack_price')
    def _compute_subtotal(self):
        for rec in self:
            rec.subtotal = round(rec.pack_price * rec.qty,2)

    @api.depends('product_id','product_id.product_line_ids')
    def _compute_availability(self):
        orders = self.mapped('backup_order') if all([each.backup_order for each in self]) else self.mapped('order_id')
        countries = orders.mapped('partner_id').mapped('country_id').ids
        restricted_products = self.env['product.product'].search([('geo_restriction','in',countries)])
        for record in self:
            for product in record.product_id.product_line_ids:
                if product.product_id.available_qty_spt <= 0 or product.product_id.available_qty_spt < (record.qty*product.qty) or product.product_id in restricted_products:
                    record.availability = 'out_of_stock'
                    break
                else:
                    record.availability = 'available'

    def action_check_package_products(self):
        for record in self:
            products = record.product_id.product_line_ids.mapped('product_id')
            restricted = products.filtered(lambda x: record.order_id.partner_id.country_id.id in x.geo_restriction.ids)
            unpublished = products.filtered(lambda prod: not prod.is_published_spt or prod.available_qty_spt <= 0 or prod.available_qty_spt < record.product_id.product_line_ids.filtered(lambda x: x.product_id == prod).qty*record.qty)
            message = []
            if restricted:
                message.append('Restricted products :-\n%s'%('\n'.join(['[{}] {}'.format(product.barcode,product.variant_name) for product in restricted])))
            if unpublished:
                message.append('Unavailable products :-\n%s'%('\n'.join(['[{}] {}'.format(product.barcode,product.variant_name) for product in unpublished])))
            if message:
                return {
                    'name':_('Unavailable/Restricted Products'),
                    'type':'ir.actions.act_window',
                    'res_model':'kits.warning.wizard',
                    'view_mode':'form',
                    'view_id':self.env.ref('kits_package_product.kits_warning_wizard_form_view').id,
                    'context':{'default_message':'\n\n'.join(message)},
                    'target' : 'new',
                }
