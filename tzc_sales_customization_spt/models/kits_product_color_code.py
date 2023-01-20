# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class kits_product_color_code(models.Model):
    _name = 'kits.product.color.code'
    _description = 'Product Color Code' 

    name = fields.Char('Color')
    color = fields.Char('HTML Code')