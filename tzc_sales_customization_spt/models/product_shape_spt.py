# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class product_shape_spt(models.Model):
    _name = 'product.shape.spt'
    _description = 'Product shape' 

    name = fields.Char('Shape', index=True)
    # product_ids = fields.One2many('product.template','shape',string='Products')
    kits_product_ids = fields.Many2many('product.product','product_with_shape_real','shape_id','product_id','Products')

    products_count = fields.Integer(compute="_compute_shape_products")
    # is_published = fields.Boolean('Is Published',default=True)

    eyeglass_avl_shape = fields.Boolean(string="Available Eyeglass Shape")
    sunglass_avl_shape = fields.Boolean(string="Available Sunglass Shape")
    new_arrival_avl_shape = fields.Boolean(string="Available New Arrival Shape")
    sale_avl_shape = fields.Boolean(string="Available sale Shape")
    image_url = fields.Char('Image Url')
    image = fields.Char('Image',related='image_url')
        
    def _compute_shape_products(self):
        for record in self:
            products = self.env['product.product'].search([("shape_id",'in',record.ids)])
            record.products_count = len(products)
        
    def action_open_shape_products_spt(self):
        return {
            "name":_("Shape Products"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "target":"current",
            "domain":[("shape_id",'in',self.ids)],
        }
    # def is_publish_shape(self):
    #     self.write({'is_published':True})
    
    # def is_unpublish_shape(self):
    #     self.write({'is_published':False})

    # def publish_shape_spt(self):
    #     for rec in self:
    #         if not rec.is_published:
    #             rec.is_published = True
                
    # def unpublish_shape_spt(self):
    #     for rec in self:
    #         if rec.is_published:
    #             rec.is_published = False
