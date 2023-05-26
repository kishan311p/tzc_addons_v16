from odoo import models,fields,api,_
from odoo.exceptions import UserError

class account_payment(models.Model):
    _inherit = 'account.payment'

    is_return_credit = fields.Boolean('Return Credit Payment ?')
    sale_id = fields.Many2one('sale.order','Order')
    transaction_id = fields.Char('Transaction')

    def kits_create_credit_payment(self,partner,order,amount):
        payment_obj = self.env['account.payment'].sudo()
        total_credit_payment = sum(order.kits_credit_payment_ids.mapped('amount'))
        order_currency = order.currency_id
        if not partner.id:
            raise UserError(_("Partner is required to create credit note."))
        if not order.id:
            raise UserError(_("Order is required to create credit note."))
        if not amount or amount < 0:
            raise UserError(_("Amount is required to create credit note."))
        vals = {
            'name':order.name,
            'partner_id':partner.id,
            'sale_id':order.id,
            'is_return_credit':True,
            'partner_type':'vendor' if partner.is_vendor else 'customer',
            'payment_type':'outbound',
            'journal_id':self.env['account.journal'].search([('type','=','cash')],limit=1).id,
            'currency_id':order_currency.id,
            'date':fields.Date.today(),
            'amount':amount,
            'payment_method_id':1,
        }
        if total_credit_payment + amount > order.amount_total:
            raise UserError(_("You can not create credit notes totaling amount more than order's total amount.\nYou are entering %s %s more."%(order_currency._convert(abs(order.amount_total-(total_credit_payment+amount)),order_currency,self.env.companies[0],fields.Date().today()),order_currency.symbol)))
        else:
            payment = payment_obj.create(vals)
            payment.action_post()
        return payment
