from odoo import api, fields, models

class ProductBrandSliderImageSpt(models.Model):
    _name='product.brand.slider.image.spt'
    _description = 'Product brand slider image'

    name = fields.Char("Name")
    image_1920 = fields.Binary('Image')
    brand = fields.Many2one('product.brand.spt','Brand')