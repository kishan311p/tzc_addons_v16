from odoo import models, fields, api, _

class sale_catalog_order_line(models.Model):
    _name = 'sale.catalog.order.line'
    _description = 'Catalog Order Line'
    _order = "product_pro_id"

    catalog_order_id = fields.Many2one('sale.catalog.order', ondelete='cascade', string='Catalog', copy=False)
    product_pro_id = fields.Many2one('product.product', ondelete='cascade', string='Product', required=True)
    name = fields.Char('Description', related='product_pro_id.variant_name')
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

    def _compute_amount(self):
        for record in self:
            record.price_subtotal = 0
    
class sale_catalog_order(models.Model):
    _name = 'sale.catalog.order'
    _description = 'Catalog Order'

    name = fields.Char('Name',required=True)
    catalog_id = fields.Many2one('sale.catalog', string='catalog')
    state = fields.Selection(selection=[('draft', 'Draft'),('sent', 'Sent'),('pending', 'Pending'),('done', 'Done'),('reject', 'reject'),('cancel', 'Cancel'),], string='Status', required=True, readonly=True, copy=False, default='draft')
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    catalog_total = fields.Char(string="Total Amount",compute='_compute_catalog_total',store=True)
    expiry_date = fields.Datetime(string="Expiry Date")
    customer_id = fields.Many2one('res.partner')
    accept_decline_flag = fields.Boolean('Accept/Decline Flag')
    decline_description = fields.Text('Decline Description ',states={'reject': [('readonly', False)]})
    line_ids = fields.One2many('sale.catalog.order.line', 'catalog_order_id', states={'draft': [('readonly', False)]},copy=True,string='Catalog Order Lines')

    def _compute_catalog_total(self):
        self.catalog_total = 0