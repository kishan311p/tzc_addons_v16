from odoo import api, fields, models, _

class kits_multi_website_shoppage_banner(models.Model):
    _inherit = "kits.multi.website.shoppage.banner"

    website_page_id = fields.Many2one("kits.b2c1.website.page","Website Page")