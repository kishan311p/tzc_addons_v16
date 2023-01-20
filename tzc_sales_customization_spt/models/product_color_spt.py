from odoo import models, fields, api, _


class ProductColorSpt(models.Model):
    _name = 'product.color.spt'
    _description = 'Product Color' 

    name = fields.Char('Color')
    color = fields.Char('HTML Code')

    primary_color_products = fields.Integer(compute="_compute_color_products_spt")
    secondary_color_products = fields.Integer(compute="_compute_color_products_spt")
    # is_published = fields.Boolean('Is Published',default=True)
    kits_product_ids = fields.One2many('product.product','product_color_name',string="Products")
    kits_product_ids = fields.One2many('product.product','secondary_color_name',string="Products")

    eyeglass_avl_colour = fields.Boolean(string="Available Eyeglass Colour")
    sunglass_avl_colour = fields.Boolean(string="Available Sunglass Colour")
    new_arrival_avl_colour = fields.Boolean(string="Available New Arrival Colour")
    sale_avl_colour = fields.Boolean(string="Available sale Colour")

    def _compute_color_products_spt(self):
        for record in self:
            primanry_products = self.env['product.product'].search([('product_color_name','=',record.id)])
            secondary_products = self.env['product.product'].search([('secondary_color_name','=',record.id)])
            record.primary_color_products = len(primanry_products)
            record.secondary_color_products = len(secondary_products)

    def action_open_primary_color_products_spt(self):
        return {
            "name":_("Color Products"),
            "type":"ir.actions.act_window",
            "res_model": "product.product",
            "view_mode":"tree,form",
            "domain":[('product_color_name','=',self.id)]
        }
    def action_open_secondarycolor_products_spt(self):
        return {
            "name":_("Color Products"),
            "type":"ir.actions.act_window",
            "res_model": "product.product",
            "view_mode":"tree,form",
            "domain":[('secondary_color_name','=',self.id)]
        }
    # def is_publish_color(self):
    #     self.write({'is_published':True})
    
    # def is_unpublish_color(self):
    #     self.write({'is_published':False})

    # def publish_colors_spt(self):
    #     for rec in self:
    #         if not rec.is_published:
    #             rec.is_published = True
    # def unpublish_colors_spt(self):
    #     for rec in self:
    #         if rec.is_published:
    #             rec.is_published = False
