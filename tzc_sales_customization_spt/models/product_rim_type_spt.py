# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class product_rim_type_spt(models.Model):
    _name = 'product.rim.type.spt'
    _description = 'Product Rim Type' 

    name = fields.Char('Rim Type', index=True)
    # product_ids = fields.One2many('product.template','rim_type',string='Products')
    kits_product_ids = fields.One2many('product.product','rim_type',string='Products')
    products_count = fields.Integer(compute="_compute_rim_type_products")
    # is_published = fields.Boolean('Is Published',default=True)
    
    image_url = fields.Char('Image Url')
    image = fields.Char('Image',related='image_url')
    active = fields.Boolean('Active')

    def _compute_rim_type_products(self):
        for record in self:
            products = self.env['product.product'].search([('is_pending_price','=',False),("rim_type",'=',record.id)])
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
    def action_active(self):
        for record in self:
            record.active = True

    def action_unactive(self):
        for record in self:
            record.active = False

    def unlink(self):
        if self.env.ref('base.group_system').id  in  self.env.user.groups_id.ids or self.env.ref('tzc_sales_customization_spt.group_marketing_user').id  in  self.env.user.groups_id.ids or self.env.ref('stock.group_stock_manager').id  in  self.env.user.groups_id.ids :
            product_ids = self.env['product.product'].with_context(pending_price=True).sudo().search([('rim_type','in',self.ids),'|',('active','=',False),('active','=',True)])
            if not product_ids:
                return super(product_rim_type_spt,self).unlink()
            else:
                raise UserError(_("%s product in this record so you can't delete this record"%(','.join(product_ids.mapped('name')))))
                
        else:
            raise UserError(_("You can't delete this record. Please contact an Administrator."))