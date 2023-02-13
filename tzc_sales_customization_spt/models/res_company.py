from odoo import fields, models
import random
import string


class res_company(models.Model):
    _inherit = "res.company"

    account_type = fields.Selection([('sand_box','Sandbox Account'),('production','Production')],default="sand_box")

    sand_box_merchant_id_usd = fields.Char('Sandbox Merchant ID (USD)')
    sand_box_hash_value_usd = fields.Char('Sandbox Hash Value (USD)')
    sand_box_merchant_id_cad = fields.Char('Sandbox Merchant ID (CAD)')
    sand_box_hash_value_cad = fields.Char('Sandbox Hash Value (CAD)')

    production_merchant_id_cad = fields.Char('Production Merchant ID (CAD)')
    production_hash_value_cad = fields.Char('Production Hash Value (CAD)')
    production_merchant_id_usd = fields.Char('Production Merchant ID (USD)')
    production_hash_value_usd = fields.Char('Production Hash Value (USD)')

    kits_quickbooks_backend_id = fields.Many2one("kits.quickbooks.backend", "Quickbook Backend Id")

    excel_token = fields.Char(string="Excel Token")

    bank_details = fields.Html('Bank Details')
    
    def action_token_generator(self,size=32, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
        for record in self:
            self.excel_token = ''.join(random.choice(chars) for _ in range(size))
