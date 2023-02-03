from odoo import api,models,fields,_

class order_payment(models.Model):
    _name = 'order.payment'
    _rec_name = 'order_id'
    
    order_id = fields.Many2one('sale.order','Order')
    amount = fields.Float('Amount')
    state = fields.Selection([('draft','Draft'),('approve','Approved'),('decliend','Declined')],'Status')
    create_date = fields.Datetime('Date')
    is_manual_paid = fields.Boolean('Manually Paid')
    mode_of_payment = fields.Selection([('cash','Cash'),('cheque','Cheque'),('bank','Bank Transfer'),('wire','Wire Transfer'),('bambora','Bambora Payment')],'Payment Method')
    payment_description = fields.Text('Description')
    transaction_id = fields.Char('Transaction ID')
