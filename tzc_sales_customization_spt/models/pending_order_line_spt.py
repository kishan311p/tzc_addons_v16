# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class pending_order_line_spt(models.Model):
    _name = 'pending.order.line.spt'
    _rec_name = 'product_id'
    _description = "Pending Catalog Line"

    product_id = fields.Many2one('product.product','Product')
    qty = fields.Float('Qty')
    pending_order_id = fields.Many2one('pending.order.spt', 'pending Order')
    cataog_line_id = fields.Many2one('sale.catalog.line', 'Catalog Line')
