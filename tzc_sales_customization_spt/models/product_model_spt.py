# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class ProductModelSpt(models.Model):
    _name = 'product.model.spt'
    _description = 'Product Model' 

    name = fields.Char('Model')
    # product_ids = fields.One2many('product.template','model',string='Products ')
    kits_product_ids = fields.One2many('product.product','model',string='Products ')
    
    product_count = fields.Integer("Products",compute="_compute_product_count")
    def _compute_product_count(self):
        for record in self:
            product_ids = self.env['product.product'].search([('model','=',record.id)])
            record.product_count = len(product_ids)

    def open_model_product_variants(self):
        return {
            "name":_("Model Products"),
            "res_model":"product.product",
            "view_mode":"tree,form",
            "domain":[('model','=',self.id)],
            "type":'ir.actions.act_window',
            "target":"current",
        }
