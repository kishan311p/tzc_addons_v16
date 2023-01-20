from odoo import api, fields, models, _

class kits_multi_website_product_slider_category(models.Model):
    _name = "kits.multi.website.product.slider.category"
    _description = "Kits Multi Website Product Slider Category"
    _order = "sequence"

    name = fields.Char("Name")
    website_id = fields.Many2one("kits.b2c.website","Website")
    limit = fields.Integer("Limit")
    sequence = fields.Integer()

    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_product_slider_category, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res
