from email.policy import default
from odoo import models, fields,_

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