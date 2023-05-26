from odoo import _, api, fields, models, tools

class tzc_homepage_banner(models.Model):
    _name = 'tzc.homepage.banner'

    sequence = fields.Integer('Sequence')
    banner_url = fields.Char('Banner Url')
    banner_redirect_url = fields.Char('Banner Redirect Url')
    home_page_id = fields.Many2one('create.homepage.html','Home Page')
    banner_image = fields.Char('Banner Image', related='banner_url')
    row_number = fields.Integer('Row Number')
