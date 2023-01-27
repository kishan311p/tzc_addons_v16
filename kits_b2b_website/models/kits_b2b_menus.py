from odoo import fields, models, api, _

class kits_b2b_menus(models.Model):
    _name = 'kits.b2b.menus'
    _description = "B2B Menus"
    
    name = fields.Char('Name')
    website_id = fields.Many2one('kits.b2b.website','Website')
    page_id = fields.Many2one('kits.b2b.pages','Page')
    is_published = fields.Boolean('Is Published')
    sequence = fields.Integer(index=True,)
    my_dashboard_model_id = fields.Many2one('kits.b2b.website','My Dashboard')
    redirect_url = fields.Char('Redirect URL')
    query_params = fields.Char('Query Params')
    fileter_params = fields.Char('Fileter Params')
