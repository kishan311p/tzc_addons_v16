# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class product_temple_size_spt(models.Model):
    _name = 'product.temple.size.spt'
    _description = 'Product Temple Size' 

    name = fields.Char('Temple Size')
    # product_ids = fields.One2many('product.template','temple_size',string='Products')
    kits_product_ids = fields.One2many('product.product','temple_size',string='Products')

    products_count = fields.Integer(compute="_compute_temple_size_products")

    def _compute_temple_size_products(self):
        for record in self:
            products = self.env['product.product'].search([("temple_size",'=',record.id)])
            record.products_count = len(products)

    def action_open_temple_size_products_spt(self):
        return {
            "name":_("Temple Size Products"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "domain":[("temple_size",'=',self.id)],
            "target":"current",
        }
