# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductMaterialSpt(models.Model):
    _name = 'product.material.spt'
    _description = 'Product Material' 

    name = fields.Char('Material', index=True)
    # product_ids = fields.One2many('product.template','material',string='Products')

    kits_product_ids = fields.Many2many('product.product','product_with_material_real','material_id','product_id',string='Products')

    products_count = fields.Integer(compute="_compute_material_products")
    # is_published = fields.Boolean('Is Published',default=True)

    eyeglass_avl_material = fields.Boolean(string="Available Eyeglass Material")
    sunglass_avl_material = fields.Boolean(string="Available Sunglass Material")
    new_arrival_avl_material = fields.Boolean(string="Available New Arrival Material")
    sale_avl_material = fields.Boolean(string="Available sale Material")
    active = fields.Boolean('Active')

    def _compute_material_products(self):
        for record in self:
            products = self.env['product.product'].search([('is_pending_price','=',False),("material_id",'in',record.ids)])
            record.products_count = len(products)

    def action_open_material_products_spt(self):
        return {
            "name":_("Material Products"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "domain":[('material_id','in',self.ids)],
            "target":"current",
        }
    
    # def is_publish_material(self):
    #     self.write({'is_published':True})
    
    # def is_unpublish_material(self):
    #     self.write({'is_published':False}) 
           
    # def publish_material_spt(self):
    #     for rec in self:
    #         if not rec.is_published:
    #             rec.is_published = True
                
    # def unpublish_material_spt(self):
    #     for rec in self:
    #         if rec.is_published:
    #             rec.is_published = False

    
    def action_active(self):
        for record in self:
            record.active = True

    def action_unactive(self):
        for record in self:
            record.active = False

    def unlink(self):
        if self.env.ref('base.group_system').id  in  self.env.user.groups_id.ids or self.env.ref('tzc_sales_customization_spt.group_marketing_user').id  in  self.env.user.groups_id.ids or self.env.ref('stock.group_stock_manager').id  in  self.env.user.groups_id.ids :
            product_ids = self.env['product.product'].with_context(pending_price=True).sudo().search([('material_id','in',self.ids),'|',('active','=',False),('active','=',True)])
            if not product_ids:
                return super(ProductMaterialSpt,self).unlink()
            else:
                raise UserError(_("%s product in this record so you can't delete this record"%(','.join(product_ids.mapped('name')))))
                
        else:
            raise UserError(_("You can't delete this record. Please contact an Administrator."))