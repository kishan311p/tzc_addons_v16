# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


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

    def unlink(self):
        if self.env.ref('base.group_system').id  in  self.env.user.groups_id.ids or self.env.ref('tzc_sales_customization_spt.group_marketing_user').id  in  self.env.user.groups_id.ids or self.env.ref('stock.group_stock_manager').id  in  self.env.user.groups_id.ids :
            product_ids = self.env['product.product'].with_context(pending_price=True).sudo().search([('size','in',self.ids),'|',('active','=',False),('active','=',True)])
            if not product_ids:
                return super(ProductSizeSpt,self).unlink()
            else:
                raise UserError(_("%s product in this record so you can't delete this record"%(','.join(product_ids.mapped('name')))))
                
        else:
            raise UserError(_("You can't delete this record. Please contact an Administrator."))