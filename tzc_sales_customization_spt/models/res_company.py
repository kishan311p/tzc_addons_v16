import random
import string

from odoo import fields, models


class website(models.Model):
    _inherit = "res.company"

    excel_token = fields.Char(string="Excel Token")

    def action_token_generator(self,size=32, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
        for record in self:
            self.excel_token = ''.join(random.choice(chars) for _ in range(size))
