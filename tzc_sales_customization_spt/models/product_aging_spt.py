# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProductAgingSpt(models.Model):
    _name = 'product.aging.spt'
    _description = 'Product Aging' 

    name = fields.Char('Aging', index=True)
    products_count = fields.Integer(compute="_compute_aging_products_count")
    kits_product_ids = fields.One2many('product.product','aging',string="Products")

    def _compute_aging_products_count(self):
        for record in self:
            products =  self.env['product.product'].search([('is_pending_price','=',False),("aging",'=',record.id)])
            record.products_count = len(products)

    def action_open_aging_spt(self):
        return {
            "name":_("Aging Products"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "domain":[('aging','=',self.id)],
            "target":"current",
        }
        
    def unlink(self):
        if self.env.ref('base.group_system').id  in  self.env.user.groups_id.ids or self.env.ref('tzc_sales_customization_spt.group_marketing_user').id  in  self.env.user.groups_id.ids or self.env.ref('stock.group_stock_manager').id  in  self.env.user.groups_id.ids :
            product_ids = self.env['product.product'].with_context(pending_price=True).sudo().search([('aging','in',self.ids),'|',('active','=',False),('active','=',True)])
            if not product_ids:
                return super(ProductAgingSpt,self).unlink()
            else:
                raise UserError(_("%s product in this record so you can't delete this record"%(','.join(product_ids.mapped('name')))))
                
        else:
            raise UserError(_("You can't delete this record. Please contact an Administrator."))