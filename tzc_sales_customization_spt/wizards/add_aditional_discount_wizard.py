from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class add_aditional_discount_wizard(models.TransientModel):
    _name = "add.aditional.discount.wizard"
    _description = "Additional Discount Wizard"

    discount_price = fields.Float("Discount Amount")
    sale_order_id = fields.Many2one('sale.order','Sale Order')

    def action_add_discount_precess(self):
        product_id = self.env['product.product'].search([('is_global_discount','=',True)],limit=1)
        discount_line = self.sale_order_id.order_line.filtered(lambda x: x.product_id == product_id)
        if not discount_line:
            order_line = [(0,0,{
                'product_id':product_id.id,
                'name':product_id.name,
                'product_uom_qty': -1.0,
                'price_unit':self.discount_price,
                'unit_discount_price':self.discount_price,
                'is_global_discount':True,
            })]
            self.sale_order_id.write({'order_line':order_line})
        else:
            discount_line.write({'price_unit':self.discount_price,'unit_discount_price':self.discount_price,'is_global_discount':True})
        self.sale_order_id._amount_all()
