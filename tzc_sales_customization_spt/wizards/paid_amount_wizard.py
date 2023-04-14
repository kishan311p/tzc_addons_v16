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
                    # if rec.due_amount < 0.0:
                    #     invoice_id.commission_line_ids.write({'state':'paid'})
                    # elif rec.due_amount > 0.0:
                    #     if self.amount >= rec.due_amount:
                    #         invoice_id.commission_line_ids.write({'state':'paid'})
                    #     elif self.amount < rec.due_amount:
                    #         invoice_id.commission_line_ids.write({'state':'draft'})
                    # elif rec.due_amount == 0.0:
                    #     if rec.amount_paid and rec.amount_paid == rec.picked_qty_order_total:
                    #         invoice_id.commission_line_ids.write({'state':'paid'})
                    #     else:
                    #         if self.amount >= rec.picked_qty_order_total:
                    #             invoice_id.commission_line_ids.write({'state':'paid'})
                    #         elif self.amount < rec.picked_qty_order_total:
                    #             invoice_id.commission_line_ids.write({'state':'draft'})

            rec.mark_as_paid_by_user = self.env.user.id
            rec.paid_amount = self.amount or 0.0
            self.env['order.payment'].create({'order_id':rec.id,'amount':float(self.amount),'state':'approve','is_manual_paid':True,'mode_of_payment':self.payment_method,'payment_description':self.description})
            if rec.payment_link:
                rec.payment_link = False
