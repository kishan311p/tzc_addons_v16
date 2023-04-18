from odoo import _, api, fields, models, tools

class on_consignment_product_message_wizard(models.TransientModel):
    _name = 'on.consignment.product.message.wizard'
    _description = "On Consignment Product Message Wizard"

    order_id = fields.Many2one('sale.order',"order")
    line_ids = fields.One2many('on.consignment.product.message.wizard.line', 'on_consignment_id', string='line')

    def action_process_product(self):
        for line in self.line_ids:
            line.sol_id.write({'product_uom_qty':line.assign_qty})
                
        self.order_id.with_context(on_consign_wizard=True).action_confirm()

class on_consignment_product_message_wizard_line(models.TransientModel):
    _name = 'on.consignment.product.message.wizard.line'
    _description = 'on.consignment.product.message.wizard.line'
    
    
    product_id = fields.Many2one('product.product', string='Product')
    minimum_qty = fields.Integer('Minimum Qty',related='product_id.minimum_qty')
    available_qty_spt = fields.Integer('Available Qty',related='product_id.available_qty_spt',store=True)
    assign_qty = fields.Integer('Assign Qty')
    on_consignment_id = fields.Many2one('on.consignment.product.message.wizard','On Consignment')
    sol_id = fields.Many2one('sale.order.line')
    ordered_qty = fields.Float('Ordered Qty',related='sol_id.product_uom_qty')
    
