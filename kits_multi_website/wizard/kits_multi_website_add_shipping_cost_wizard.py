from odoo import api, fields, models, _

class kits_multi_website_add_shipping_cost_wizard(models.TransientModel):
    _name = "kits.multi.website.add.shipping.cost.wizard"
    _description = "Kits Add Shipping Cost Wizard"

    def _get_domian(self):
        shipping_ids = self.env['kits.free.shipping.rule'].search([('country_ids','=',self._context.get('default_country_id'))])
        if shipping_ids:
            return [('id','=',self.env['kits.paid.shipping.rule.line'].search([('shipping_rule_id','in',shipping_ids.ids)]).ids)]
        else:
            return []
    paid_shipping_cost_id = fields.Many2one('kits.paid.shipping.rule.line','Delivey Days',domain=_get_domian)
    unit_price = fields.Float("Shipping Cost",related='paid_shipping_cost_id.amount')
    sale_order_id_kits = fields.Many2one('kits.multi.website.sale.order','Sale Order')

    def action_precess(self):
        product_id = self.env['product.product'].search([('is_shipping_product','=',True)],limit=1)
        shipping_cost_line = self.sale_order_id_kits.sale_order_line_ids.filtered(lambda x: x.product_id == product_id)
        if not shipping_cost_line:
            sale_order_line_ids = [(0,0,{
                'product_id':product_id.id,
                'quantity':1.0,
                'unit_price':self.unit_price,
                'discounted_unit_price':self.unit_price,
                'state': 'ready_to_ship'
            })]
            self.sale_order_id_kits.write({'sale_order_line_ids':sale_order_line_ids})
        else:
            shipping_cost_line.write({
                'unit_price':self.unit_price,
                'discounted_unit_price':self.unit_price,
                'discount':0,
                })
        self.sale_order_id_kits.write({'paid_shipping_cost_id':self.paid_shipping_cost_id.id})
        