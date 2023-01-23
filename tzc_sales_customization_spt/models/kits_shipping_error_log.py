from odoo import _, api, fields, models, tools

class kits_shipping_error_log(models.Model):
    _name = "kits.shipping.error.log"
    _description = "Shipping Error Log"
    _order = 'create_date desc'

    so_date = fields.Datetime('Order Date')
    sale_order = fields.Char('Order#')
    customer_id = fields.Char('Customer Id')
    customer_name = fields.Char('Customer Name')
    email = fields.Char('Email')
    street = fields.Char('Street')
    city = fields.Char('City')
    state_id = fields.Many2one('res.country.state','State')
    postal_code = fields.Char('Zip')
    country_id = fields.Many2one('res.country','Country')
    error = fields.Char('Error')
    shipping_method_id = fields.Many2one('delivery.carrier','Shipping Method')
