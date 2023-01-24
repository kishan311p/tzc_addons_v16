from odoo import fields, models

class product_packaging(models.Model):
    _inherit = "product.packaging"
    
    package_carrier_type = fields.Selection([('none', 'No carrier integration')], string='Carrier', default='none')