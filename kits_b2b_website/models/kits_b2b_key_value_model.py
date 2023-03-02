from odoo import fields, models, api, _

class kits_b2b_key_value_model(models.Model):
    _name = 'kits.b2b.key.value.model'
    _description="B2B Key Value Model"

    name = fields.Text('Key')
    value = fields.Text('Value')
    website_id = fields.Many2one('kits.b2b.website','Website')
    page_id = fields.Many2one('kits.b2b.pages','page')
    head_office = fields.Boolean('Header Office?',default=False)

    contact_us_page_id = fields.Many2one('kits.b2b.pages','Contact Us Page')
