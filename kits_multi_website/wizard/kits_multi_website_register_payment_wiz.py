from odoo import api, fields, models, _
from odoo.exceptions import UserError

class kits_multi_website_register_payment_wiz(models.TransientModel):
    _name = "kits.multi.website.register.payment.wiz"
    _description = "Kits Multi Website Register Payment Wiz"

    amount = fields.Float("Amount   ")
    journal_id = fields.Many2one("account.journal",domain=[('type','in',['bank', 'cash'])])
    invoice_id = fields.Many2one("kits.multi.website.invoice", "Invoice")
    payment_option = fields.Selection([('wallet','Wallet'),('bank','Bank Account')])


    def action_confirm_payment(self):
        for record in self:
            record.invoice_id.sale_order_id.invoice_state = 'paid'
            if record.payment_option == "wallet":
                if record.amount > record.invoice_id.customer_id.wallet_amount:
                    raise UserError("Not enough money in wallet!")
                record.invoice_id.customer_id.wallet_amount -= record.amount
                wallet_transaction_vals = {
                    'invoice_id' : record.invoice_id.id, 
                    'sale_order_id' : record.invoice_id.sale_order_id.id, 
                    'amount': -abs(record.amount),
                    'customer_id': record.invoice_id.customer_id.id,
                    'refund_date': fields.datetime.now(),
                }
                self.env['kits.multi.website.wallet.transaction'].create(wallet_transaction_vals) 
            record.invoice_id.write({
                'state': 'paid',
                'amount_paid': record.amount,
                'journal_id': record.journal_id.id,
                'payment_date': fields.date.today(),
            }) 
  
