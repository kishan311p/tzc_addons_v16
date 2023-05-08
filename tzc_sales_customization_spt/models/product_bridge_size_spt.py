# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductBridgeSizeSpt(models.Model):
    _name = 'product.bridge.size.spt'
    _description = 'Product Bridge Size' 

    name = fields.Char('Bridge Size', index=True)
    # product_ids = fields.One2many('product.template','bridge_size',string='Products')
    kits_product_ids = fields.One2many('product.product','bridge_size',string='Products')
    bridgesize_id = fields.Many2one('kits.product.color.code', string='Bridge Size')
    products_count = fields.Integer(compute="_compute_bridge_size_spt")

    def _compute_bridge_size_spt(self):
        for record in self:
            products = self.env['product.product'].search([("bridge_size",'=',record.id)])
            record.products_count = len(products)

    def action_open_bridge_size_products_spt(self):
        return {
            "name":_("Bridge Size Products"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "domain":[('bridge_size','=',self.id)],
            "target":"current",
        }
