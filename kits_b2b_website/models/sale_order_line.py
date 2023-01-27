from odoo import _, api, fields, models

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    b2b_currency_rate = fields.Float('Currency Rate ')