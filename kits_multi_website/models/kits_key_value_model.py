from odoo import fields, models,api

class kits_key_value_model(models.Model):
    _name = 'kits.key.value.model'
    _description = 'Key value model'

    name = fields.Char('Key')
    value = fields.Char('Value')
    website_id = fields.Many2one('kits.b2c.website','Website')
    