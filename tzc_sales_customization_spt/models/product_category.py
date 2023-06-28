from email.policy import default
from odoo import models, fields,_
from odoo.exceptions import UserError

class ProductCategory(models.Model):
    _inherit = 'product.category'

    active = fields.Boolean('Active',default=True)

    
    def action_open_category_products_spt(self):
        return {
            "name":_("Category Size Products"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "domain":[('categ_id','=',self.id)],
            "target":"current",
        }

    def _compute_product_count(self):
        for record in self:
            categ_ids = self.env['product.product'].search([('is_pending_price','=',False),('categ_id','=',record.id)])
            record.product_count = len(categ_ids)

    def action_active(self):
        for record in self:
            record.active = True

    def action_unactive(self):
        for record in self:
            record.active = False

    def unlink(self):
        if self.env.ref('base.group_system').id  in  self.env.user.groups_id.ids or self.env.ref('tzc_sales_customization_spt.group_marketing_user').id  in  self.env.user.groups_id.ids or self.env.ref('stock.group_stock_manager').id  in  self.env.user.groups_id.ids :
            product_ids = self.env['product.product'].with_context(pending_price=True).sudo().search([('categ_id','in',self.ids),'|',('active','=',False),('active','=',True)])
            if not product_ids:
                return super(ProductCategory,self).unlink()
            else:
                raise UserError(_("%s product in this record so you can't delete this record"%(','.join(product_ids.mapped('name')))))
                
        else:
            raise UserError(_("You can't delete this record. Please contact an Administrator."))
