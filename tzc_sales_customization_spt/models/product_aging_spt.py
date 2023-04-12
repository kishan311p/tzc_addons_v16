# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductAgingSpt(models.Model):
    _name = 'product.aging.spt'
    _description = 'Product Aging' 

    name = fields.Char('Aging', index=True)
    products_count = fields.Integer(compute="_compute_aging_products_count")
    kits_product_ids = fields.One2many('product.product','aging',string="Products")

    def _compute_aging_products_count(self):
        for record in self:
            products =  self.env['product.product'].search([("aging",'=',record.id)])
            record.products_count = len(products)

    def action_open_aging_spt(self):
        return {
            "name":_("Aging Products"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "domain":[('aging','=',self.id)],
            "target":"current",
        }
