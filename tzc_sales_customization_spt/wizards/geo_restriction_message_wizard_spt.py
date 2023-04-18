from odoo import models, fields, api, _


class geo_restriction_message_wizard_spt(models.TransientModel):
    _name = 'geo.restriction.message.wizard.spt'
    _description = 'Geo Restriction Message'


    order_line_ids = fields.Many2many('sale.order.line','gre_restriction_with_sale_order_line_real','wizard_id','order_line_id','order line')
    

    def action_process(self):
        order_id = self.order_line_ids.mapped('order_id')[0]
        for line in self.order_line_ids:
            line.unlink()
        line_ids = order_id.order_line.filtered(lambda x:x.product_id.on_consignment and x.product_uom_qty > x.product_id.actual_stock)
        if line_ids:
            line_ids -= self.order_line_ids
            wizard_id = self.env['on.consignment.product.message.wizard'].create({
                    'order_id' : order_id.id
                })
            wizard_lines_list = []
            for line in line_ids:
                wizard_lines_list.append((0,0,{
                    'product_id' : line.product_id.id,
                    'sol_id' : line.id,
                    'assign_qty' : line.product_id.minimum_qty,
                }))
            wizard_id.line_ids = wizard_lines_list

            return {
                'name': _('Product Minimum Stock Alert.'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'on.consignment.product.message.wizard',
                'target': 'new',
                'res_id' : wizard_id.id
            }
        else:
            order_id.with_context(allow_restricted=True).action_confirm()
    
    def action_process_with_products(self):
        order_id = self.order_line_ids.mapped('order_id')[0]
        line_ids = order_id.order_line.filtered(lambda x:x.product_id.on_consignment and x.product_uom_qty > x.product_id.actual_stock)
        if line_ids:
            wizard_id = self.env['on.consignment.product.message.wizard'].create({
                    'order_id' : order_id.id
                })
            wizard_lines_list = []
            for line in line_ids:
                wizard_lines_list.append((0,0,{
                    'product_id' : line.product_id.id,
                    'sol_id' : line.id,
                    'assign_qty' : line.product_id.minimum_qty,
                }))
            wizard_id.line_ids = wizard_lines_list
                    
            # line_ids.mapped('product_id').write({'assign_qty':0.0})
            return {
                'name': _('Product Minimum Stock Alert.'),
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'on.consignment.product.message.wizard',
                'target': 'new',
                'res_id' : wizard_id.id
            }
        order_id.with_context(allow_restricted=True).action_confirm()
