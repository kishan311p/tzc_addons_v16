from odoo import _, api, fields, models, tools

class product_pricelist_item(models.Model):
    _inherit = 'product.pricelist.item'

    def write(self, vals):
        if vals.get('fixed_price'):
            print('Hey')
        res = super(product_pricelist_item,self).write(vals)
        return res