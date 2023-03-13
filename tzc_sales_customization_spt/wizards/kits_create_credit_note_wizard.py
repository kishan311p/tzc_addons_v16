from odoo import models,fields,api,_
from odoo.exceptions import UserError

class kits_create_credit_note_wizard(models.TransientModel):
    _name = "kits.create.credit.note.wizard"
    _description = "Create Credit Note Wizard"
    
    def set_order_amount(self):
        order_amount = self.env['sale.order'].browse(self._context.get('default_sale_id')).amount_total
        return order_amount
    
    def set_paid_amount(self):
        amount = sum(self.env['sale.order'].browse(self._context.get('default_sale_id')).kits_credit_payment_ids.mapped('amount'))
        return amount

    sale_id = fields.Many2one('sale.order','Sale')
    picking_id = fields.Many2one('stock.picking','Picking')
    order_amount = fields.Float('Order Amount',default=set_order_amount,store=True,readonly=True)
    paid_amount = fields.Float('Total Credits',default=set_paid_amount,store=True,readonly=True)
    credit_amount = fields.Float('Credit Amount',required=True)
    refund_date = fields.Date('Refund Date',default=fields.Date.today(),required=True)


    def action_create_credit_note(self):
        if not self.credit_amount:
            raise UserError(_('Please provide credit amount.'))
        # if self.picking_id:
        #     self.picking_id.credit_note_created = True
        credit_note = self.env['account.payment'].sudo().kits_create_credit_payment(self.sale_id.partner_id,self.sale_id,self.credit_amount)
        self.sale_id.kits_credit_payment_ids = [(6,0,self.sale_id.kits_credit_payment_ids.ids+credit_note.ids)]
