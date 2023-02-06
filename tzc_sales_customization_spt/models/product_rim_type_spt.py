# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class product_rim_type_spt(models.Model):
    _name = 'product.rim.type.spt'
    _description = 'Product Rim Type' 

    name = fields.Char('Rim Type')
    # product_ids = fields.One2many('product.template','rim_type',string='Products')
    kits_product_ids = fields.One2many('product.product','rim_type',string='Products')
    products_count = fields.Integer(compute="_compute_rim_type_products")
    # is_published = fields.Boolean('Is Published',default=True)
    
    eyeglass_avl_rim_type = fields.Boolean(string="Available Eyeglass Rim Type")
    sunglass_avl_rim_type = fields.Boolean(string="Available Sunglass Rim Type")
    new_arrival_avl_rim_type = fields.Boolean(string="Available New Arrival Rim Type")
    sale_avl_rim_type = fields.Boolean(string="Available sale Rim Type")
    image_url = fields.Char('Image Url')
    image = fields.Char('Image',related='image_url')

    def _compute_rim_type_products(self):
        for record in self:
            products = self.env['product.product'].search([("rim_type",'=',record.id)])
            record.products_count = len(products)
    
    def action_open_rim_type_product_spt(self):
        return {
            "name":_("Products"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "domain":[("rim_type",'=',self.id)],
            "target":"current",
        }
    # def is_publish_rim_type(self):
    #     self.write({'is_published':True})
    
    # def is_unpublish_rim_type(self):
    #     self.write({'is_published':False})

    # def publish_rim_type_spt(self):
    #     for rec in self:
    #         if not rec.is_published:
    #             rec.is_published = True
                
    # def unpublish_rim_type_spt(self):
    #     for rec in self:
    #         if rec.is_published:
    #             rec.is_published = False
