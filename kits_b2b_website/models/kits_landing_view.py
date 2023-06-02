from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class kits_landing_view(models.Model):
    _name = 'kits.landing.view'

    name = fields.Char('Name')
    on_link = fields.Char('Redirect URL')
    mobile_banner = fields.Char('Mobile Banner',related='mobile_banner_url')
    dekstop_banner = fields.Char('Dekstop Banner',related='dekstop_banner_url')
    website_id = fields.Many2one('kits.b2b.website','Website')
    mobile_banner_url = fields.Char('Mobile Banner')
    dekstop_banner_url = fields.Char('Dekstop Banner')
    video_url_ids = fields.One2many('kits.landing.url', 'landing_view_id', string='Video URL')
    seo_keyword = fields.Char('URL Keyword')

class kits_landing_url(models.Model):
    _name = 'kits.landing.url'
    
    url = fields.Char('URL')
    landing_view_id = fields.Many2one('kits.landing.view', string='Landing View')