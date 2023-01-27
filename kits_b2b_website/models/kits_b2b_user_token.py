from odoo import _, api, fields, models

class kits_b2b_user_token(models.Model):
    _name = 'kits.b2b.user.token'
    _description = 'User Token'
    _rec = 'user_id'

    user_id = fields.Many2one('res.users', string='User')
    login_token = fields.Char('Login Token')
    address_token = fields.Char('Address Token')
    order_token = fields.Char('Order Token')
    payment_token = fields.Char('Payment Token')
    resert_password_up_token = fields.Char('Reset Password Token')

    expiry_date = fields.Datetime('Expiry Date')
    token_expired = fields.Boolean(compute='_compute_token_expired', string='Token Expired')

    def _compute_token_expired(self):
        for record in self:
            token_expired =False
            if record.expiry_date < fields.Datetime.now():
                token_expired = True
            record.token_expired = token_expired