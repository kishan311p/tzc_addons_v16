# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class geo_restriction_spt(models.Model):
    _name = 'geo.restriction.spt'
    _description = 'Geo Restriction' 

    name = fields.Char('Geo Restriction', index=True)

    products_count = fields.Integer(compute="_compute_geo_restricted_products")

    def _compute_geo_restricted_products(self):
        for record in self:
            products = self.env['product.product'].search([("geo_restriction",'=',record.id)])
            record.products_count = len(products)

    def action_open_get_restricted_products(self):
        return {
            "name":_("Geo Restricted Product"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "domain":[("geo_restriction",'=',self.id)],
            "target":"current",
        }
