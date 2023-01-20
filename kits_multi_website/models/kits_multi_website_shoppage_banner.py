from odoo import api, fields, models

class kits_multi_website_shoppage_banner(models.Model):
    _name = "kits.multi.website.shoppage.banner"
    _description= "Shop page banner"

    image = fields.Char("Desktop Image",compute="_compute_image",store="True")
    image_public_url = fields.Char("Desktop Image Public URL")
    mobile_image = fields.Char("Mobile Image",compute="_compute_mobile_image",store=True)
    mobile_image_public_url = fields.Char("Mobile Image Public URL")
    redirect_url = fields.Char("Redirect URL")
    website_id = fields.Many2one("kits.b2c.website","Website")

    @api.depends('image_public_url')
    def _compute_image(self):
        for record in self:
            record.image = record.image_public_url

    @api.depends('mobile_image_public_url')
    def _compute_mobile_image(self):
        for record in self:
            record.mobile_image = record.mobile_image_public_url
