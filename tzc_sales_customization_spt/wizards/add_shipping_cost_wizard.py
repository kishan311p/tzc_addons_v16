from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class add_shipping_cost_wizard(models.TransientModel):
    _name = "add.shipping.cost.wizard"
    _description = "Shipping Cost Wizard"

    unit_price = fields.Float("Shipping Cost")
    sale_order_id_kits = fields.Many2one('sale.order','Sale Order')

    def action_precess(self):
        product_id = self.env['product.product'].search([('is_shipping_product','=',True)],limit=1)
        shipping_cost_line = self.sale_order_id_kits.order_line.filtered(lambda x: x.product_id == product_id)
        if not shipping_cost_line:
            order_line = [(0,0,{
                'product_id':product_id.id,
                'name':product_id.name,
                'product_uom_qty':1.0,
                'price_unit':self.unit_price,
                'unit_discount_price':self.unit_price,
                'is_shipping_product':True,
            })]
            self.sale_order_id_kits.write({'order_line':order_line})
        else:
            shipping_cost_line.write({
                'price_unit':self.unit_price,
                'unit_discount_price':self.unit_price,
                'is_shipping_product':True,
                'fix_discount_price':0,
                'discount':0,
                })
        self.sale_order_id_kits._amount_all()
