# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductBridgeSizeSpt(models.Model):
    _name = 'product.bridge.size.spt'
    _description = 'Product Bridge Size' 

    name = fields.Char('    Bridge Size', index=True)
    # product_ids = fields.One2many('product.template','bridge_size',string='Products')
    kits_product_ids = fields.One2many('product.product','bridge_size',string='Products')
    bridgesize_id = fields.Many2one('kits.product.color.code', string=' Bridge Size')
    products_count = fields.Integer(compute="_compute_bridge_size_spt")
    active = fields.Boolean('Active', default=True)

    def _compute_bridge_size_spt(self):
        for record in self:
            products = self.env['product.product'].search([('is_pending_price','=',False),("bridge_size",'=',record.id)])
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

    def action_active(self):
        for record in self:
            record.active = True

    def action_unactive(self):
        for record in self:
            record.active = False

    def unlink(self):
        if self.env.ref('base.group_system').id  in  self.env.user.groups_id.ids or self.env.ref('tzc_sales_customization_spt.group_marketing_user').id  in  self.env.user.groups_id.ids or self.env.ref('stock.group_stock_manager').id  in  self.env.user.groups_id.ids :
            product_ids = self.env['product.product'].with_context(pending_price=True).sudo().search([('bridge_size','in',self.ids),'|',('active','=',False),('active','=',True)])
            if not product_ids:
                return super(ProductBridgeSizeSpt,self).unlink()
            else:
                raise UserError(_("%s product in this record so you can't delete this record"%(','.join(product_ids.mapped('name')))))
                
        else:
            raise UserError(_("You can't delete this record. Please contact an Administrator."))
