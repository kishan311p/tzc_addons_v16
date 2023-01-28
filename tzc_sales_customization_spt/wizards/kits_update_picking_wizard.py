from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class kits_update_picking_wizard(models.TransientModel):
    _name = "kits.update.picking.wizard"
    _description = 'Kits Update Picking Wizard'

    partner_id = fields.Many2one('res.partner','Customer')
    picking_id = fields.Many2one('stock.picking','Picking Order')
    sale_order_ids = fields.Many2many('sale.order','sale_order_sale_order_wizard_rel','sale_order_id','wizard_id','Quotations')

    def action_update(self):
        if self.sale_order_ids:
            diff_price = self.check_product_price()
            if not diff_price:
                for rec in self.sale_order_ids:
                    picking_old_state = self.picking_id.state
                    sale_old_state = self.picking_id.sale_id.state
                    for line in rec.order_line:
                        self.picking_id.with_context(mail_notrack=True).write({'state':'draft'})
                        self.picking_id.sale_id.with_context(mail_notrack=True).write({'state':'sale'})
                        if line.product_id in self.picking_id.sale_id.order_line.product_id:
                            product_ids = self.picking_id.sale_id.order_line.filtered(lambda x: x.product_id == line.product_id)
                            qty = sum(product_ids.mapped('product_uom_qty')) + line.product_uom_qty
                            product_ids.write({'product_uom_qty':qty})
                        else:
                            order_lines_vals = [(0,0,{
                                'product_id' : line.product_id.id,
                                'product_uom_qty' : line.product_uom_qty,
                                'unit_discount_price' : line.unit_discount_price
                            })]
                            self.picking_id.sale_id.write({'order_line':order_lines_vals})
                    rec.state = 'merged'
                    self.picking_id.with_context(mail_notrack=True).state = picking_old_state
                    self.picking_id.sale_id.with_context(mail_notrack=True).state = sale_old_state
                    self.picking_id.sale_id.merge_reference = [(4,rec.id)]
            else:
                product_ids = self.env['product.product'].browse(diff_price)
                message = 'Below products having different price.'
                return {
                    'name':_('Message'),
                    'type':'ir.actions.act_window',
                    'res_model':'kits.message.update.picking.wizard',
                    'view_mode':'form',
                    'context':{'default_product_ids':diff_price,'default_message':message,'default_sale_order_ids':self.sale_order_ids.ids,'default_picking_id':self.picking_id.id},
                    'target':'new',
                }
        else:
            raise UserError('Please Select Order.')

    def check_product_price(self):
        product_list = []
        for rec in self.sale_order_ids:
            for line in rec.order_line:
                line_id = self.picking_id.sale_id.order_line.filtered(lambda x:x.product_id == line.product_id)
                if line_id and line.unit_discount_price != line_id.unit_discount_price:
                    if line.product_id not in product_list:
                        product_list.append(line.product_id.id)
        
        return product_list
