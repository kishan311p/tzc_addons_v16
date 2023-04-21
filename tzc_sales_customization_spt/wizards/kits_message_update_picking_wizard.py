from odoo import _, api, fields, models, tools

class kits_message_update_picking_wizard(models.TransientModel):
    _name = 'kits.message.update.picking.wizard'
    _description = "Kits Message Update Picking Wizard"

    product_ids = fields.Many2many('product.product','kits_message_update_picking_wizard_product_rel','wizard_id','product_id','Products')
    message = fields.Text('Message')
    sale_order_ids = fields.Many2many('sale.order','message_update_picking_wizard_sale_order_rel','wizard_id','sale_id','Sale Order')
    picking_id = fields.Many2one('stock.picking','Delivery')

    def action_merge_with_order(self):
        for rec in self.sale_order_ids:
            for line in rec.order_line:
                if line.product_id in self.picking_id.sale_id.order_line.product_id:
                    product_ids = self.picking_id.sale_id.order_line.filtered(lambda x: x.product_id == line.product_id)
                    qty = sum(product_ids.mapped('product_uom_qty')) + line.product_uom_qty
                    product_ids.write({'product_uom_qty':qty,'sale_type':line.product_id.sale_type})
                    product_ids.product_id_change()
                else:
                    order_lines_vals = {
                            'product_id' : line.product_id.id,
                            'product_uom_qty' : line.product_uom_qty,
                            'unit_discount_price' : line.unit_discount_price,
                            'sale_type':line.product_id.sale_type,
                            'order_id':self.picking_id.sale_id.id,
                        }
                    line_id = self.env['sale.order.line'].create(order_lines_vals)
                    line_id.product_id_change()
            rec.state = 'merged'
        self.picking_id.sale_id._amount_all()