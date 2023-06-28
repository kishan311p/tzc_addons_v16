# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class kits_product_color_code(models.Model):
    _name = 'kits.product.color.code'
    _description = 'Product Color Code' 

    name = fields.Char('Color')
    color = fields.Char('HTML Code')
    model_id = fields.Many2one('product.model.spt', string='model')
    temple_size_ids = fields.One2many('product.temple.size.spt', 'templesize_id', string='Temple Size ')
    bridge_size_ids = fields.One2many('product.bridge.size.spt', 'bridgesize_id', string='Bridge Size  ')
    eye_size_ids = fields.One2many('product.size.spt', 'eyesize_id', string='Eye Size')
    active = fields.Boolean('Active')
    products_count = fields.Integer(
        string='Number of products',
        compute='_get_color_code_data_spt',
        help='It shows the number of product counts',
    )

    def _get_color_code_data_spt(self):
        for record in self:
            product_ids = self.env['product.product'].search([('is_pending_price','=',False),('color_code', '=', record.id)]).ids
            record.products_count = len(product_ids)

    def action_open_color_code_products_spt(self):
        return {
            "name":_("Color Code Products"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "domain":[('color_code','=',self.id)],
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
            product_ids = self.env['product.product'].with_context(pending_price=True).sudo().search([('color_code','in',self.ids),'|',('active','=',False),('active','=',True)])
            if not product_ids:
                return super(kits_product_color_code,self).unlink()
            else:
                raise UserError(_("%s product in this record so you can't delete this record"%(','.join(product_ids.mapped('name')))))
                
        else:
            raise UserError(_("You can't delete this record. Please contact an Administrator."))