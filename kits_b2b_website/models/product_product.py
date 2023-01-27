from odoo import fields, models, api, _

class product_product(models.Model):
    _inherit = 'product.product'

    def kits_product_price_compute(self):
        return