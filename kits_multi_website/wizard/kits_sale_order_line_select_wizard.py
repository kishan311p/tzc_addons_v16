from odoo import fields,models,_
from odoo.exceptions import UserError
class kits_sale_order_line_select_wizard(models.Model):
    _name = 'kits.sale.order.line.select.wizard'
    _description = 'sale order line wizard'
    
    def _get_domain(self):
        if self._context.get('domain'):
            ids= list(set(self.return_request_id.browse(self._context.get('domain')).sale_order_id.sale_order_line_ids.ids)-set(self.return_request_id.browse(self._context.get('domain')).return_request_line_ids.mapped('sale_order_line_id').ids )  )
            return [('id','in',ids)]
    return_line_ids = fields.Many2many('kits.multi.website.sale.order.line','selectsale_order_line_wizard_select_line_wizard','wizard_id','sale_order_line_id', string='Select Product',domain=_get_domain)
    return_request_id = fields.Many2one("kits.multi.website.return.request", "Return Request")

    def action_process(self):
        for record in self:
            if self.return_line_ids:
                self.return_request_id.is_approved = True
                self.return_request_id.is_refunded = True
                product_list = []
                for line in self.return_line_ids:
                    line.state= 'requested'
                    product_list.append((0,0,{
                        'product_id': line.product_id.id,
                        'quantity': line.quantity,
                        'power_type_id': line.power_type_id.id,
                        'glass_type_id': line.glass_type_id.id,
                        'sale_order_line_id': line.id                       
                    }))
                self.return_request_id.return_request_line_ids = product_list
            return{
                'type': 'ir.actions.client',
                'tag': 'reload',
            }
            