# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class sale_catalog_line(models.Model):
    _name = 'sale.catalog.line'
    _description = 'Sale Catalog Line' 
    _order = "product_pro_id"

    catalog_id = fields.Many2one('sale.catalog', ondelete='cascade', string='Catalog', copy=False)
    product_pro_id = fields.Many2one('product.product', ondelete='cascade', string='Product', required=True)
    name = fields.Char('Name', related='product_pro_id.display_name')
    variant_name = fields.Char('Description', related='product_pro_id.variant_name')
    image_variant_1920 = fields.Binary('Image', related='product_pro_id.image_variant_1920', readonly=True)
    image_secondary_1920 = fields.Binary('Secondary Image', related='product_pro_id.image_secondary', readonly=True)
    image_catalog_product_url = fields.Char('Primary Image  ',related="product_pro_id.image_url",readonly=True)
    image_catalog_product_secondary_url = fields.Char('Primary Image ',related="product_pro_id.image_secondary_url",readonly=True)
    
    product_price = fields.Float('Price')   # this price pull from product list price, but can be modified
    product_price_msrp = fields.Float("MSRP")
    product_price_wholesale = fields.Float("Wholesale")
    product_uom_id = fields.Many2one('uom.uom', related='product_pro_id.uom_id', readonly=True)
    product_qty = fields.Float('Qty', digits='Product Unit of Measure', default=1)
    product_qty_available = fields.Float('Qty On Hand', related='product_pro_id.qty_available', readonly=True)
    qty_available_spt = fields.Integer('Available QTY', related='product_pro_id.available_qty_spt', readonly=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency",default=lambda self: self.env.company.currency_id.id)
    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal')
    sale_type = fields.Selection([('clearance','Clearance'),('on_sale','On Sale')],'Sale Type')
    
    unit_discount_price = fields.Float('Our Price')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    # fix_discount_price = fields.Float('Discount')
    product_categ_id = fields.Many2one('product.category',related="product_pro_id.categ_id", string='Category', readonly=True)
    actual_available_qty = fields.Float('Available Qty',related="product_pro_id.actual_stock")
    is_special_discount = fields.Boolean("Is Special Discount",help="This is flag for check product is in special discount or not.",)

    @api.onchange('product_pro_id',"product_qty",'product_price','unit_discount_price','discount')
    def _onchange_price_total_compute(self):
        self._compute_amount()

    def _compute_amount(self):
        for record in self:
            price_subtotal = 0.0
            if record.unit_discount_price:
                price_subtotal = round(round(record.product_price - ((record.discount *0.01) * record.product_price),2)* record.product_qty,2)
            record.price_subtotal = price_subtotal
    @api.onchange('unit_discount_price')
    def _onchange_fix_discount_price(self):
        for record in self:
            try:
                discount = round(100-(record.unit_discount_price*100/record.product_price),2)
            except:
                discount = 0.0
            record.discount = discount

    @api.onchange('discount')
    def _onchange_discount(self):
        for record in self:
            unit_discount_price = record.product_price
            try:
                unit_discount_price = round(record.product_price - (record.product_price * record.discount)*0.01,2)
            except:
                unit_discount_price = 0.0
            record.unit_discount_price = unit_discount_price
    
    def get_pending_order_line_qty(self,partner):
        line = self.env['pending.order.line.spt'].search([('pending_order_id.customer_id','=',partner.id),('cataog_line_id','=',self.id)],limit=1)
        return int(line.qty)

    @api.onchange('product_pro_id')
    def _onchange_product_pro_id_spt(self):
        for record in self:
            currency_id = record.currency_id.id
            product_price= record.product_pro_id.lst_price
            if record.currency_id and record.currency_id.name == 'USD':
                product_price = record.product_pro_id.lst_price_usd

            if record.sale_type:
                if record.sale_type == 'on_sale':
                    if record.currency_id and record.currency_id.name == 'USD':
                        product_price =  record.product_pro_id.on_sale_usd
                    else:
                        product_price = record.product_pro_id.on_sale_cad
                if record.sale_type == 'clearance':
                    if record.currency_id and record.currency_id.name == 'CAD':
                        product_price = record.product_pro_id.clearance_cad
                    else:
                        product_price =  record.product_pro_id.clearance_usd
            
            if record.product_pro_id:
                record.update({
                'product_price' : product_price,
                'product_price_msrp' : record.product_pro_id.price_msrp,
                'product_price_wholesale' : record.product_pro_id.price_wholesale,
                'sale_type' : record.product_pro_id.sale_type,
                'currency_id': currency_id
                })
            if record.catalog_id and record.catalog_id.pricelist_id and record.catalog_id.pricelist_id.currency_id:
               record.catalog_id._onchange_pricelist_id()
            
