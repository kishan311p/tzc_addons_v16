# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductSizeSpt(models.Model):
    _name = 'product.size.spt'
    _description = 'Product Size' 

    name = fields.Char('Size', index=True)
    # product_ids = fields.One2many('product.template','size',string='Products')
    kits_product_ids = fields.One2many('product.product','size',string='Products')
    eyesize_id = fields.Many2one('kits.product.color.code', string='Eye Size')
    products_count = fields.Integer("#Products",compute="_compute_size_product_variants")
    active = fields.Boolean('Active')
    
    def _compute_size_product_variants(self):
        for record in self:
            product_ids = self.env['product.product'].search([('is_pending_price','=',False),('size','=',record.id)])
            record.products_count = len(product_ids)

    def action_open_size_products_spt(self):
        return {
            "name":_("Size Products"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "target":"current",
            "domain":[("size",'=',self.id)],
        }

    def action_active(self):
        for record in self:
            record.active = True

    def action_unactive(self):
        for record in self:
            record.active = False
