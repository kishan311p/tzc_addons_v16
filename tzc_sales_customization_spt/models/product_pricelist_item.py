from odoo import _, api, fields, models, tools

class product_pricelist_item(models.Model):
    _inherit = 'product.pricelist.item'

    def write(self, vals):
        if vals.get('fixed_price'):
            if self.fixed_price > vals.get('fixed_price'):
                self.product_id.is_new_price = True
        res = super(product_pricelist_item,self).write(vals)
        return res
