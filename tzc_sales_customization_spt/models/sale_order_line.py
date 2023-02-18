from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    # display_type = fields.Selection([
    #     ('line_section', "Section"),
    #     ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    is_reward_line = fields.Boolean('Is a program reward line')

    is_virtual = fields.Boolean('Virtual Product')
    virtual_source = fields.Char('Virtual Source')
    redeem_points = fields.Float('Redeem Virtual Points')
    reward_amount = fields.Float('Redeem Amount ')

    b2b_currency_rate = fields.Float('Currency Rate ')
    
    sh_sale_barcode_scanner_is_last_scanned = fields.Boolean(string = "Last Scanned?")

    package_id = fields.Many2one('kits.package.product','Package')
    is_pack_order_line = fields.Boolean('Package order line')
    package_line_id = fields.Many2one('kits.package.order.line',"Package Line",ondelete='cascade')

    state = fields.Selection([('draft', 'Quotation'),('sent', 'Quotation Sent'),('received', 'Quotation Received'),('sale', 'Order Confirmed'),('in_scanning','In Scanning'),('scanned','Scanning Completed'),('scan', 'Ready to Ship'),('shipped', 'Shipped'),('draft_inv', 'Draft Invoice'),('open_inv', 'Invoiced'),('cancel', 'Cancelled'),('merged', 'Merged'),('done', 'Locked')], related='order_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')

    price_unit = fields.Float(track_visibility=True)
    is_global_discount = fields.Boolean("Is Additional Discount",related="product_id.is_global_discount", store=True)
    is_shipping_product = fields.Boolean("Is Shipping Product",related="product_id.is_shipping_product", store=True)
    is_admin = fields.Boolean("Is Admin Product",related="product_id.is_admin", store=True)
    fix_discount_price = fields.Float('Discount')    
    is_fs = fields.Boolean("Is FS?")
    sale_type = fields.Selection([('clearance','Clearance'),('on_sale','On Sale')],'Sale Type')
    unit_discount_price = fields.Float('Our Price')
    product_categ_id = fields.Many2one('product.category',related="product_id.categ_id", string='Category ', readonly=True)
    is_promotion_applied = fields.Boolean("Is promotion applied?")
    picked_qty = fields.Integer('Delivered',compute='_compute_picked_qty',store=True)
    picked_qty_subtotal = fields.Float('Subtotal',compute="_compute_picked_qty",store=True)
    is_special_discount = fields.Boolean("Is Special Discount",help="This is flag for check product is in special discount or not.")

    def _get_virtual_sources(self):
        return []

    @api.onchange('product_id')
    def _onchange_product_id_spt(self):
        for record in range(len(self)):
            record = self[record]
            record.product_uom_qty = record.product_uom_qty
            if record.product_id and record.product_id.is_global_discount:
                record.product_uom_qty = -record.product_uom_qty
            if record.product_id.sale_type:
                record.sale_type = record.product_id.sale_type

    # @api.onchange('product_id')
    # def product_id_change_eto(self):
    #     for record in range(len(self)):
    #         record = self[record]
    #         price_unit = record.price_unit
    #         unit_discount_price = 0
            
    #         if record.order_id:
    #             if record.sale_type and record.order_id.partner_id and record.order_id.partner_id.property_product_pricelist :
    #                 if record.order_id.partner_id.property_product_pricelist.currency_id.name == 'CAD':
    #                    price_unit = record.product_id.on_sale_cad
    #                 else:
    #                    price_unit = record.product_id.on_sale_usd
    #         unit_discount_price = price_unit
    #         if record.discount:
    #         	unit_discount_price = price_unit - (price_unit * record.discount)* 0.01
    #             record.update({'price_unit':price_unit,'unit_discount_price': unit_discount_price})


    @api.depends('product_id','price_unit','unit_discount_price','picked_qty','product_uom_qty','discount','tax_id','move_ids','move_ids.quantity_done')
    def _compute_picked_qty(self):
        move_obj = self.env['stock.move']
        for record in range(len(self)):
            record = self[record]
            picked_qty_subtotal = 0.0
            move_ids = move_obj.search([('id','in',record.move_ids.ids),('state','!=','cancel')])
            record.picked_qty = sum(move_ids.mapped('quantity_done')) if move_ids else 0
            if record.order_id.state not in ['sale', 'done','in_scanning','scanned','scan','shipped','draft_inv','open_inv']:
                picked_qty_subtotal = round( record.price_subtotal,2)
            else:  
                if record.picked_qty and record.product_id.type != 'service': 
                    picked_qty_subtotal = picked_qty_subtotal + (record.picked_qty * record.unit_discount_price)
                if record.product_id.type == 'service': 
                    picked_qty_subtotal =picked_qty_subtotal + (record.product_uom_qty * record.unit_discount_price)
            record.picked_qty_subtotal = round(picked_qty_subtotal,2)

    @api.onchange('product_id',"product_uom_qty",'price_unit','tax_id','unit_discount_price','discount','picked_qty','fix_discount_price')
    def _onchange_price_total_compute(self):
        self._compute_amount()
    
    @api.depends('product_id',"product_uom_qty",'price_unit','tax_id','unit_discount_price','discount','picked_qty','fix_discount_price')
    def _compute_amount(self):
        res = super(SaleOrderLine,self)._compute_amount()
        for record in range(len(self)):
            record = self[record]
            if record.unit_discount_price:
                record.price_subtotal = round(record.unit_discount_price * record.product_uom_qty,2)
        return res
    
    @api.constrains('price_subtotal')
    def _check_pricesubtotal_spt(self):
        for record in range(len(self)):
            record = self[record]
            if record.price_subtotal < 0.0 and not record.product_id.is_global_discount:
                raise UserError(_('Subtotal amount should not be in negative.'))
            
    @api.onchange('discount','price_unit')
    def _onchange_discount_spt(self):
        for record in range(len(self)):
            record = self[record]
            unit_discount_price =round( record.price_unit - ((record.discount *0.01) * record.price_unit),2)
            fix_discount_price = round((record.price_unit*record.discount)/100,2)
            
            record.unit_discount_price = round(unit_discount_price,2)
            record.fix_discount_price = round(fix_discount_price,2)

    @api.onchange('fix_discount_price','price_unit')
    def _onchange_fix_discount_price_spt(self):
        for record in range(len(self)):
            record = self[record]
            unit_discount_price = round(record.price_unit - record.fix_discount_price,2)
            
            try:
                discount = round((record.fix_discount_price*100/record.price_unit),2)
            except:
                discount = 0.0
            
            record.unit_discount_price = round(unit_discount_price,2)
            record.discount = round(discount,2)

    @api.onchange('unit_discount_price','price_unit')
    def _onchange_unit_discounted_price_spt(self):
        for record in range(len(self)):
            record = self[record]
            try:
                discount = round(100-(record.unit_discount_price*100/record.price_unit),2)
            except:
                discount = 0.0
            
            fix_discount_price = round((record.price_unit*discount/100),2)
            
            record.fix_discount_price = round(fix_discount_price,2)
            record.discount = round(discount,2)


    @api.onchange('product_uom','product_uom_qty')
    def product_uom_change_spt(self):
        for record in range(len(self)):
            record = self[record]
            record.product_uom_qty = record.product_uom_qty
            if record.product_id and record.product_id.is_global_discount:
                record.product_uom_qty = -record.product_uom_qty
    
    @api.onchange('product_id')
    def product_id_change(self):
        # res = super(SaleOrderLine, self).product_id_change()
        for record in range(len(self)):
            record = self[record]
            if record.product_id:
                update_dict = {'price_unit':round(record.price_unit,2),
                               'unit_discount_price': round(record.unit_discount_price,2), 
                               'fix_discount_price':round(record.fix_discount_price,2),
                               'sale_type':record.product_id.sale_type if record.product_id.sale_type else ''}

                active_inflation = self.env['kits.inflation'].search([('is_active','=',True)])
                inflation_rule_ids = self.env['kits.inflation.rule'].search([('country_id','in',self.env.user.country_id.ids),('brand_ids','in',record.product_id.brand.ids),('inflation_id','=',active_inflation.id)])
                inflation_rule = inflation_rule_ids[-1] if inflation_rule_ids else False
                if inflation_rule:
                    is_inflation = False
                    if active_inflation.from_date and active_inflation.to_date :
                        if active_inflation.from_date <= datetime.now().date() and active_inflation.to_date >= datetime.now().date():
                            is_inflation = True
                    elif active_inflation.from_date:
                        if active_inflation.from_date <= datetime.now().date():
                            is_inflation = True
                    elif active_inflation.to_date:
                        if active_inflation.to_date >= datetime.now().date():
                            is_inflation = True
                    else:
                        if not active_inflation.from_date:
                            is_inflation = True
                        if not active_inflation.to_date:
                            is_inflation = True
                        
                    if is_inflation:
                        product_price = round(product_price+(product_price*inflation_rule.inflation_rate /100),2)
                        unit_discount_price = round(unit_discount_price+(unit_discount_price*inflation_rule.inflation_rate /100),2)
                        update_dict.update({'price_unit':product_price,'unit_discount_price':unit_discount_price})

                active_fest_id = self.env['tzc.fest.discount'].search([('is_active','=',True)])
                special_disocunt_id = self.env['kits.special.discount'].search([('country_id','in',self.env.user.partner_id.country_id.ids),('brand_ids','in',record.product_id.brand.ids)]) #,('tzc_fest_id','=',active_fest_id.id)
                price_rule_id = special_disocunt_id[-1] if special_disocunt_id else False
                if price_rule_id:
                    applicable = False 
                    if active_fest_id.from_date and active_fest_id.to_date :
                        if active_fest_id.from_date <= datetime.now().date() and active_fest_id.to_date >= datetime.now().date():
                            applicable = True
                    elif active_fest_id.from_date:
                        if active_fest_id.from_date <= datetime.now().date():
                            applicable = True
                    elif active_fest_id.to_date:
                        if active_fest_id.to_date >= datetime.now().date():
                            applicable = True
                    else:
                        if not active_fest_id.from_date:
                            applicable = True
                        if not active_fest_id.to_date:
                            applicable = True
                        
                    if applicable: 
                        special_discount_price = round((update_dict.get('unit_discount_price') - update_dict.get('unit_discount_price') * price_rule_id.discount / 100),2)
                        fix_discount_price_spt = round(product_price - special_discount_price,2)
                        update_dict.update({'fix_discount_price':fix_discount_price_spt,'unit_discount_price': special_discount_price}) #,'is_special_discount':applicable

                record.write(update_dict)
                # record._onchange_fix_discount_price_spt()
                record._onchange_unit_discounted_price_spt()
                # record._onchange_discount_spt()

            if record.order_id.partner_id and not record.order_id.partner_id.country_id:
                record.tax_id = False
        # return res

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        # res = super(SaleOrderLine, self).product_id_change()
        for record in range(len(self)):
            record = self[record]
            if record.product_id:
                product_price = record.product_id.lst_price
                price_unit = record.product_id.lst_price
                if record.order_id.pricelist_id and record.order_id.partner_id:
                    price_unit = record.order_id.pricelist_id._get_product_price(record.product_id, record.product_uom_qty)
                    product_price = record.product_id.lst_price if record.order_id.pricelist_id.currency_id.name == 'USD' else product_price
                unit_discount_price = 0
                if record.order_id and record.order_id:
                    if record.sale_type == 'on_sale' and record.order_id.partner_id and record.order_id.partner_id.property_product_pricelist :
                        if record.order_id.partner_id.property_product_pricelist.currency_id.name == 'CAD':
                            price_unit = record.product_id.on_sale_cad
                            product_price = record.product_id.lst_price
                        else:
                            price_unit = record.product_id.on_sale_usd
                            product_price = record.product_id.lst_price

                
                    if record.sale_type == 'clearance' and record.order_id.partner_id and record.order_id.partner_id.property_product_pricelist :
                        if record.order_id.partner_id.property_product_pricelist.currency_id.name == 'CAD':
                            price_unit = record.product_id.clearance_cad
                            product_price = record.product_id.lst_price

                        else:
                            price_unit = record.product_id.clearance_usd
                            product_price = record.product_id.lst_price

                unit_discount_price = price_unit
                if (record.discount or record.discount == 0.0) and not record._context.get('partner_change'):
                    unit_discount_price = round(product_price - (product_price * record.discount)* 0.01,2)

                record.update({'price_unit':round(product_price,2),'unit_discount_price': round(unit_discount_price,2), 'sale_type':record.product_id.sale_type if record.product_id.sale_type else ''})
                record._onchange_unit_discounted_price_spt()
        # return res

    def _compute_qty_at_date(self):
        res = super(SaleOrderLine, self)._compute_qty_at_date()

        for rec in range(len(self)):
            rec = self[rec]
            rec.free_qty_today = rec.product_id.available_qty_spt

        return res

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty', 'order_id.state')
    def _compute_qty_to_invoice(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in range(len(self)):
            line = self[line]
            if line.order_id.state in ['sale', 'done','in_scanning','scanned','scan','shipped','draft_inv','open_inv']:
                if line.product_id.invoice_policy == 'order':
                    line.qty_to_invoice = line.product_uom_qty - line.qty_invoiced
                else:
                    line.qty_to_invoice = line.qty_delivered - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.model
    def _prepare_add_missing_fields(self, values):
        """ Deduce missing required fields from the onchange """
        res = {}
        onchange_fields = ['name', 'price_unit', 'product_uom', 'tax_id']
        if values.get('order_id') and values.get('product_id') and any(f not in values for f in onchange_fields):
            line = self.new(values)
            line.product_id_change()
            for field in onchange_fields:
                if field not in values:
                    res[field] = line._fields[field].convert_to_write(line[field], line)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('display_type', self.default_get(['display_type'])['display_type']):
                values.update(product_id=False, price_unit=0, product_uom_qty=0, product_uom=False, customer_lead=0)
            values.update(self._prepare_add_missing_fields(values))

        lines = super().create(vals_list)
        for line in range(len(lines)):
            line = lines[line]
            if line.product_id and line.order_id.state in ['sale', 'done','in_scanning','scanned','scan','shipped','draft_inv','open_inv']:
                msg = _("Extra line with %s ") % (line.product_id.display_name,)
                line.order_id.message_post(body=msg)
                # create an analytic account if at least an expense product
                if line.product_id.expense_policy not in [False, 'no'] and not line.order_id.analytic_account_id:
                    line.order_id._create_analytic_account()
        return lines
