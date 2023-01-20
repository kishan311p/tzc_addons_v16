from odoo import api, fields, models, _

class kits_multi_website_customer_token_line(models.Model):
    _name = "kits.multi.website.customer.token.line"

    customer_id = fields.Many2one('kits.multi.website.customer','Customer')
    token = fields.Char("Login Token")
    token_validity = fields.Datetime("Token Validity")
    