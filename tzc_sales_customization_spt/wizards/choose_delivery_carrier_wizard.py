from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta

class choose_delivery_carrier_wizard(models.TransientModel):
    _inherit = 'choose.delivery.carrier'

    shipping_id = fields.Many2one('shipping.provider.spt','Shipping Provider')
    carrier_id = fields.Many2one(
        'delivery.carrier',required=False,
        string="Shipping Method")
    
    def update_price(self):
        for rec in self:
            rec.display_price = 0
            compare_date = self.create_date - relativedelta(years=1)
            domain = [('date_order','>=',compare_date),('state','in',['shipped','open_inv','draft_inv']),('shipping_id','=',rec.shipping_id.id),('country_id','=',rec.partner_id.country_id.id)]
            # domain = [('state','in',['shipped','open_inv']),('shipping_id','=',rec.shipping_id.id),('country_id','=',rec.partner_id.country_id.id)]
            qty_to_take = "picked_qty" if rec.order_id.picked_qty else "product_uom_qty"
            total_order_qty = sum(rec.order_id.order_line.filtered(lambda x : not x.product_id.is_admin and not x.product_id.is_shipping_product and not x.product_id.is_global_discount and not x.product_id.is_case_product).mapped(qty_to_take))
            sale_order_ids = self.env['sale.order'].search(domain)
            if rec.partner_id.state_id:
                domain.append(('state_id','=',rec.partner_id.state_id.id))
                # If no order found in state then we will get data from country.
                sale_order_ids = self.env['sale.order'].search(domain) or sale_order_ids
            try:
                order_qty_range = int(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.nearest_shipping_qty_range'))
            except:
                order_qty_range= 0
            near_range_order_ids = sale_order_ids.filtered(lambda x : x.picked_qty>=total_order_qty-order_qty_range and x.picked_qty<=total_order_qty+order_qty_range)
            if near_range_order_ids:
                nearest_order = near_range_order_ids[0]
                nearest_qty = abs(nearest_order.picked_qty - total_order_qty)
                for so_id in near_range_order_ids:
                    curr_diff_qty = abs(so_id.picked_qty - total_order_qty)
                    if curr_diff_qty < nearest_qty:
                        nearest_order = so_id
                        nearest_qty = curr_diff_qty
                rec.display_price = nearest_order.eto_shipping_cost
            else:
                total_shipping_cost = sum(sale_order_ids.mapped('eto_shipping_cost'))
                total_picked_qty = sum(sale_order_ids.mapped('picked_qty'))
                if total_shipping_cost and total_order_qty and total_picked_qty:
                    rec.display_price = (total_shipping_cost / total_picked_qty) * total_order_qty
                    # rec.display_price = (total_shipping_cost / total_picked_qty)
            return {
                'name': _('Add a shipping method'),
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'choose.delivery.carrier',
                'res_id': rec.id,
                'target': 'new',
            }
    
    def button_confirm(self):
        for rec in self:
            product_id = self.env['product.product'].search([('is_shipping_product','=',True)],limit=1)
            shipping_cost_line = rec.order_id.order_line.filtered(lambda x: x.product_id == product_id)
            if not shipping_cost_line:
                order_line = [(0,0,{
                    'product_id':product_id.id,
                    'name':product_id.name,
                    'product_uom_qty':1.0,
                    'price_unit':rec.display_price,
                    'unit_discount_price':rec.display_price,
                    'is_shipping_product':True,
                })]
                rec.order_id.write({'order_line':order_line})
            else:
                shipping_cost_line.write({
                    'price_unit':rec.display_price,
                    'unit_discount_price':rec.display_price,
                    'is_shipping_product':True,
                    'fix_discount_price':0,
                    'discount':0,
                    })
            rec.order_id.shipping_id=rec.shipping_id
            rec.order_id._amount_all()