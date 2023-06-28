from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductColorSpt(models.Model):
    _name = 'product.color.spt'
    _description = 'Product Color' 

    name = fields.Char('Color',index=True)
    color = fields.Char('HTML Code')

    primary_color_products = fields.Integer(compute="_compute_color_products_spt")
    secondary_color_products = fields.Integer(compute="_compute_color_products_spt")
    lense_color_products = fields.Integer(compute="_compute_color_products_spt")
    # is_published = fields.Boolean('Is Published',default=True)
    kits_product_ids = fields.One2many('product.product','product_color_name',string="Products")
    kits_product_ids = fields.One2many('product.product','secondary_color_name',string="Products")
    active = fields.Boolean('Active')

    def _compute_color_products_spt(self):
        for record in self:
            primanry_products = self.env['product.product'].search([('is_pending_price','=',False),('product_color_name','=',record.id)])
            secondary_products = self.env['product.product'].search([('is_pending_price','=',False),('secondary_color_name','=',record.id)])
            lense_color_name = self.env['product.product'].search([('is_pending_price','=',False),('lense_color_name','=',record.id)])
            record.primary_color_products = len(primanry_products)
            record.secondary_color_products = len(secondary_products)
            record.lense_color_products = len(lense_color_name)

    def action_open_primary_color_products_spt(self):
        return {
            "name":_("Color Products"),
            "type":"ir.actions.act_window",
            "res_model": "product.product",
            "view_mode":"tree,form",
            "domain":[('product_color_name','=',self.id)]
        }
    def action_open_lense_color_name_products_spt(self):
        return {
            "name":_("Color Products"),
            "type":"ir.actions.act_window",
            "res_model": "product.product",
            "view_mode":"tree,form",
            "domain":[('lense_color_name','=',self.id)]
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

    def action_active(self):
        for record in self:
            record.active = True

    def action_unactive(self):
        for record in self:
            record.active = False

    def unlink(self):
        if self.env.ref('base.group_system').id  in  self.env.user.groups_id.ids or self.env.ref('tzc_sales_customization_spt.group_marketing_user').id  in  self.env.user.groups_id.ids or self.env.ref('stock.group_stock_manager').id  in  self.env.user.groups_id.ids :
            product_ids = self.env['product.product'].with_context(pending_price=True).sudo().search([('product_color_name','in',self.ids),'|',('secondary_color_name','in',self.ids),'|',('lense_color_name','in',self.ids),'|',('active','=',False),('active','=',True)])
            if not product_ids:
                return super(ProductColorSpt,self).unlink()
            else:
                raise UserError(_("%s product in this record so you can't delete this record"%(','.join(product_ids.mapped('name')))))
                
        else:
            raise UserError(_("You can't delete this record. Please contact an Administrator."))