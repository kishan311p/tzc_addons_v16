# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class kits_product_color_code(models.Model):
    _name = 'kits.product.color.code'
    _description = 'Product Color Code' 

    name = fields.Char('Color')
    color = fields.Char('HTML Code')
    model_id = fields.Many2one('product.model.spt', string='model')
    temple_size_ids = fields.One2many('product.temple.size.spt', 'templesize_id', string='Temple Size')
    bridge_size_ids = fields.One2many('product.bridge.size.spt', 'bridgesize_id', string='Bridge Size')
    eye_size_ids = fields.One2many('product.size.spt', 'eyesize_id', string='Eye Size')
    