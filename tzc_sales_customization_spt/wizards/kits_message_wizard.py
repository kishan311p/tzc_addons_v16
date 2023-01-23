from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class kits_message_wizard(models.TransientModel):
    _name = "kits.message.wizard"
    _description = "Kits Message Wizard"
    _rec_name = "order_id"

    kits_message = fields.Char('Message')
    order_id = fields.Many2one('sale.order',"order")

    def action_confirm(self):
        for rec in self:
            link = self.env['sale.order'].generate_link(rec.order_id)
            if link:
                rec.order_id.payment_link = link
                return{
                    'name':_('Generate a Payment Link'),
                    'type':'ir.actions.act_window',
                    'res_model':'kits.generate.payment.link.wizard',
                    'view_mode':'form',
                    'context':{'default_kits_payment_link':link,'default_sale_order_id':rec.order_id.id},
                    'target':'new',
                }
            else:
                raise UserError('Something went wrong.. Payment link can\'t generate.\n\n- Please check bambora account details.')
