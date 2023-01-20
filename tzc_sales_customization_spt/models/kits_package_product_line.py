from odoo import models,fields,api,_

class kits_package_product_lines(models.Model):
    _name = 'kits.package.product.lines'
    _description = 'Package Product lines'

    combo_product_id = fields.Many2one('kits.package.product','Package')
    product_id = fields.Many2one('product.product','Product Name')
    image_variant_1920 = fields.Binary('Image', related='product_id.image_variant_1920')
    image_secondary_1920 = fields.Binary('Secondary Image', related='product_id.image_secondary')
    image_product_url = fields.Char(' Primary Image',related='product_id.image_url')
    image_product_secondary_url = fields.Char('Secondary Image ',related='product_id.image_secondary_url')
    qty = fields.Integer('Qty',default=1)
    product_price = fields.Float('Unit Price')
    usd_price = fields.Float('USD Price')
    cad_price = fields.Float('CAD Price',compute="_get_product_price_cad",store=True,compute_sudo=True)
    subtotal = fields.Float('Subtotal',compute="_calc_subtotal",store=True,compute_sudo=True)
    sale_type = fields.Selection([('on_sale','On Sale'),('clearance','Clearance')],string="Sale Type",compute='_get_default_sale_type',store=True,compute_sudo=True)

    discount = fields.Float('Discount (%)')
    fix_discount_price = fields.Float('Discount Amount')

    @api.depends('product_id','product_id.sale_type')
    def _get_default_sale_type(self):
        for rec in self:
            rec.sale_type = rec.product_id.sale_type
    
    @api.onchange('usd_price')
    def _onchange_usd_price(self):
        for record in self:
            # price = record.usd_price
            # if self.env.user.partner_id.property_product_pricelist.currency_id.name == 'CAD':
            #     price = record.cad_price
            try:
                record.discount = round(((record.product_price-record.usd_price) * 100) / record.product_price , 2)
            except:
                record.discount = 0.00
            record.fix_discount_price = record.product_price - record.usd_price
    
    @api.onchange('discount')
    def _onchange_discount(self):
        for record in self:
            discount_amount = (record.product_price * record.discount * 0.01)
            record.usd_price = round(record.product_price - discount_amount,2)
            record.fix_discount_price = round(discount_amount,2)
    
    @api.onchange('fix_discount_price')
    def _onchange_fix_discount_price(self):
        for record in self:
            unit_discount_price = record.product_price - record.fix_discount_price
            try:
                record.discount = round((record.fix_discount_price*100/record.product_price),2)
            except:
                record.discount = 0.00
            record.usd_price = unit_discount_price

    @api.depends('qty','usd_price','product_id')
    def _calc_subtotal(self):
        for rec in self:
            subtotal = 0.0
            rec.subtotal =  rec.usd_price * rec.qty

    @api.onchange('product_id')
    def _compute_pro_price(self):
        user_currency = self.env.user.partner_id.property_product_pricelist.currency_id.name
        for rec in self:
            # without sale_type price
            product_price = rec.product_id.lst_price_usd
            if user_currency == 'CAD':
                product_price = rec.product_id.lst_price
            rec.product_price = product_price
            # regular/on_sale/clearance price
            unit_price = product_price
            if rec.product_id.sale_type:
                if rec.product_id.sale_type == 'on_sale':
                    if user_currency == 'CAD':
                        unit_price =  rec.product_id.on_sale_cad
                    else:
                        unit_price = rec.product_id.on_sale_usd
                if rec.product_id.sale_type == 'clearance':
                    if user_currency == 'CAD':
                        unit_price = rec.product_id.clearance_cad
                    else:
                        unit_price =  rec.product_id.clearance_usd
            rec.usd_price = unit_price

    @api.depends('usd_price')
    def _get_product_price_cad(self):
        cad_rate  = float(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.on_sale_cad_spt', default=0))
        for rec in self:
            line_cad_price = 0.0
            if rec.usd_price:
                line_cad_price = round(rec.usd_price * cad_rate,2)
            rec.cad_price = line_cad_price
    
