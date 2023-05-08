from odoo import _, api, fields, models, tools

class product_pricelist(models.Model):
    _inherit = 'product.pricelist'

    is_pricelist_excluded = fields.Boolean("Bypass Inflation and special discount")