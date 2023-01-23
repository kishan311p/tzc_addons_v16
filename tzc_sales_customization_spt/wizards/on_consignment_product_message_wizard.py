from odoo import _, api, fields, models, tools

class on_consignment_product_message_wizard(models.TransientModel):
    _name = 'on.consignment.product.message.wizard'
    _description = "On Consignment Product Message Wizard"

    product_ids = fields.Many2many('product.product','on_consignment_product_with_product_product_real','wizard_id','product_id','Products')
    order_id = fields.Many2one('sale.order',"order")

    def action_process_product(self):
        for product in self.product_ids:
            product_id = self.env['product.product'].search([('id','=',product.id)])
            if product_id:
                ordre_line_id = self.order_id.order_line.filtered(lambda x:x.product_id.id == product_id.id)
                if ordre_line_id:
                    ordre_line_id.write({'product_uom_qty':product.assign_qty})
                
        self.order_id.with_context(on_consign_wizard=True).action_confirm()
