from odoo import fields, models, api, _


class product_product(models.Model):
    _inherit = 'product.product'

    def kits_product_price_compute(self):
        return

    b2b_product_size_value = fields.Char(
        'B2B Product Size Value',
        compute="compute_b2b_values",
        compute_sudo=True,
        store=True
    )
    b2b_name = fields.Char(
        'B2B Name',
        compute='compute_b2b_values',
        compute_sudo=True,
        store=True
    )
    brand_name = fields.Char(
        'Brand Name',
        compute="_compute_brand_name",
        store=True,
        compute_sudo=True
    )

    @api.depends('brand', 'brand.name')
    def _compute_brand_name(self):
        for product in self:
            product.brand_name = product.brand.name

    @api.depends('eye_size_compute', 'bridge_size_compute', 'temple_size_compute', 'eye_size', 'bridge_size', 'temple_size',
                 'model', 'model.name', 'manufacture_color_code', 'categ_id', 'categ_id.name'
                 )
    def compute_b2b_values(self):
        for product in self:
            product.b2b_product_size_value = '{} {} {}'.format(
                product.eye_size_compute or '00', product.bridge_size_compute or '00', product.temple_size_compute or '00')
            product.b2b_name = '{} {} {} {} {} ({})'.format(
                product.model.name or '00',
                product.manufacture_color_code or '00',
                product.eye_size_compute or '00',
                product.bridge_size_compute or '00',
                product.temple_size_compute or '00',
                product.categ_id.name,
            )
