from odoo import _,api,fields,models

class AccountJournal(models.Model):
    _inherit = 'account.journal'

    post_at = fields.Selection([('pay_val', 'Payment Validation'), ('bank_rec', 'Bank Reconciliation')], string="Post At", default='pay_val')
