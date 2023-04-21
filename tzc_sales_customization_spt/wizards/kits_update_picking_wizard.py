from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class kits_update_picking_wizard(models.TransientModel):
    _name = "kits.update.picking.wizard"
    _description = 'Kits Update Picking Wizard'

    partner_id = fields.Many2one('res.partner','Customer')
    picking_id = fields.Many2one('stock.picking','Picking Order')
    sale_order_ids = fields.Many2many('sale.order','sale_order_sale_order_wizard_rel','sale_order_id','wizard_id','Quotations')

    def action_update(self):
        order_line_list = []
        if self.sale_order_ids:
            diff_price = self.check_product_price()
            if not diff_price:
                for rec in self.sale_order_ids:
                    product_list =self.picking_id.sale_id.order_line.mapped('product_id.id')
                    picking_old_state = self.picking_id.state
                    sale_old_state = self.picking_id.sale_id.state
                    for line in rec.order_line:
                        self.picking_id.with_context(mail_notrack=True).write({'state':'draft'})
                        self.picking_id.sale_id.with_context(mail_notrack=True).write({'state':'sale'})
                        if line.product_id.id in product_list:
                            product_ids = self.picking_id.sale_id.order_line.filtered(lambda x: x.product_id == line.product_id)
                            qty = sum(product_ids.mapped('product_uom_qty')) + line.product_uom_qty
                            product_ids.write({'product_uom_qty':qty})
                            order_line_list.extend(product_ids.ids)
                        else:
                            order_lines_vals = [(0,0,{
                                'product_id' : line.product_id.id,
                                'sale_type' : line.sale_type,
                                'product_uom_qty' : line.product_uom_qty,
                                'unit_discount_price' : line.unit_discount_price
                            })]
                            self.picking_id.sale_id.write({'order_line':order_lines_vals})
                    rec.state = 'merged'
                    self.picking_id.with_context(mail_notrack=True).state = picking_old_state
                    self.picking_id.sale_id.with_context(mail_notrack=True).state = sale_old_state
                    self.picking_id.sale_id.merge_reference = [(4,rec.id)]
                    self.picking_id.sale_id.order_line.filtered(lambda line: line.id not in order_line_list).product_id_change()
                    self.picking_id.sale_id._amount_all()
            else:
                product_ids = self.env['product.product'].browse(diff_price)
                message = 'Below products having different price.'
                pid_list = [(4,pid) for pid in diff_price]
                wizard_id = self.env['kits.message.update.picking.wizard'].create({'product_ids':pid_list,'message':message,'sale_order_ids':self.sale_order_ids.ids,'picking_id':self.picking_id.id})
                return {
                    'name':_('Message'),
                    'type':'ir.actions.act_window',
                    'res_model':'kits.message.update.picking.wizard',
                    'view_mode':'form',
                    'res_id':wizard_id.id,
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
