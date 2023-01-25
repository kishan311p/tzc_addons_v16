from odoo import _, api, fields, models, tools

class update_qty_log(models.Model):
    _name = 'update.qty.log'
    _rec_name = "product_default_code"
    _description = 'Update Qty Log'

    product_default_code = fields.Char('SKU')
    created_date = fields.Datetime('Date')
    user_id = fields.Many2one('res.users','User Name')
    before_qty_on_hand = fields.Float('On Hand Quantity')
    before_available_qty = fields.Float('Available Quantity')
    before_reserved_qty = fields.Float('Reserved Quantity')
    after_qty_on_hand = fields.Float('On Hand Quantity ')
    after_available_qty = fields.Float('Available Quantity ')
    after_reserved_qty = fields.Float('Reserved Quantity ')
    origin_order_id = fields.Many2one('sale.order','Reference Order')
