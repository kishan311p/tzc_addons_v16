from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class paid_amount_wizard(models.TransientModel):
    _name = 'paid.amount.wizard'
    _description = "Paid Amount Wizard"

    amount = fields.Float('Amount')
    date = fields.Datetime('Date')
    order_id = fields.Many2one('sale.order','Order')
    payment_method = fields.Selection([('cash','Cash'),('cheque','Cheque'),('bank','Bank Transfer'),('wire','Wire Transfer'),('bambora','Bambora Payment')],'Payment Method')
    description = fields.Text('Description')

    def action_pay(self):
        for rec in self.order_id:
            cancel_order_ids = rec.filtered(lambda x:x.state == 'cancel')
            invoice_id = rec.invoice_ids.filtered(lambda invoice:invoice.state not in ('cancel','draft'))
            if cancel_order_ids:
                raise UserError('You can\'t pay canceled orders.')
            else:
                rec.is_paid = True
                if invoice_id and invoice_id.commission_line_ids:
                    if self.order_id.payment_status:
                        invoice_id.commission_line_ids.write({'state':self.order_id.payment_status})
                    else:
                        invoice_id.commission_line_ids.write({'state':'draft'})
                 
            rec.mark_as_paid_by_user = self.env.user.id
            rec.paid_amount = self.amount or 0.0
      
            payment_obj = self.env['account.payment'].sudo()
            vals = {
                'name' : self.order_id.name,
                'partner_id' : self.order_id.partner_id.id,
                'sale_id' : self.order_id.id,
                'partner_type' : 'customer',
                'payment_type' : 'inbound',
                'journal_id' : self.env.company.journal_id.id,
                'currency_id' : self.order_id.currency_id.id,
                'date' : self.date,
                'amount' : self.amount
                }
            payment = payment_obj.create(vals)
            payment.action_post()
            invoice_id = self.order_id.invoice_ids.filtered(lambda x:x.state == 'posted')
            receive = payment.line_ids.filtered('credit')
            if invoice_id:
                invoice_id.js_assign_outstanding_line(receive.id)

            if rec.payment_link:
                rec.payment_link = False
