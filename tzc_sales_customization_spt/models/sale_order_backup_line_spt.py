from odoo import models, fields, api, _

class sale_order_backup_line_spt(models.Model):
    _name = 'sale.order.backup.line.spt'
    _description = "Sale Order Backup Line"

    order_backup_id = fields.Many2one('sale.order.backup.spt','Order')
    product_id = fields.Many2one('product.product','Product')
    categ_id = fields.Many2one('product.category','Category',related="product_id.categ_id")
    product_uom_qty = fields.Integer('Quantity')
    price_unit = fields.Float('Unit Pirce')
    unit_discount_price = fields.Float('Our Pirce')
    fix_discount_price = fields.Float('Discount')
    discount = fields.Float('Disc.%')
    name = fields.Char('Name')
    subtotal = fields.Float('Subtotal',compute="_compute_sutotal")
    tax_id = fields.Many2many('account.tax','sale_order_backup_line_tax_real','backup_id','tax_id','Taxes')
    is_global_discount = fields.Boolean("Is Additional Discount",related="product_id.is_global_discount", store=True)
    is_shipping_product = fields.Boolean("Is Shipping Product",related="product_id.is_shipping_product", store=True)
    is_admin = fields.Boolean("Is Admin Product",related="product_id.is_admin", store=True)
    # is_promotion_applied = fields.Boolean("Is promotion applied?")
    # is_fs = fields.Boolean("Is FS?")
    sale_type = fields.Selection([('clearance','Clearance'),('on_sale','On Sale')],'Sale Type')
    is_pack_order_line = fields.Boolean('Backup Pack Order Line')
    package_id = fields.Many2one('kits.package.product','Package')
    is_included_case = fields.Boolean('Included Case?',help='Help to differentiate extra case and included case.')    

    def _compute_sutotal(self):
        for record in self:
            record.subtotal = record.product_uom_qty * record.unit_discount_price

    @api.onchange('discount','price_unit')
    def _onchange_discount_spt(self):
        for record in self:
            unit_discount_price = record.price_unit - ((record.discount *0.01) * record.price_unit)
            fix_discount_price = (record.price_unit*record.discount)/100
            
            record.unit_discount_price = unit_discount_price
            record.fix_discount_price = fix_discount_price

    @api.onchange('fix_discount_price','price_unit')
    def _onchange_fix_discount_price_spt(self):
        for record in self:
            unit_discount_price = record.price_unit - record.fix_discount_price
            
            try:
                discount = round((record.fix_discount_price*100/record.price_unit),2)
            except:
                discount = 0.0
            
            record.unit_discount_price = unit_discount_price
            record.discount = discount

    @api.onchange('unit_discount_price','price_unit')
    def _onchange_unit_discounted_price_spt(self):
        for record in self:
            try:
                discount = round(100-(record.unit_discount_price*100/record.price_unit),2)
            except:
                discount = 0.0
            
            fix_discount_price = (record.price_unit*discount/100)
            
            record.fix_discount_price = fix_discount_price
            record.discount = discount
