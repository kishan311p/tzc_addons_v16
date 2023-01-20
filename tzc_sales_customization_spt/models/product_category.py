from email.policy import default
from odoo import models, fields

class ProductCategory(models.Model):
    _inherit = 'product.category'

    active = fields.Boolean('Active',default=True)