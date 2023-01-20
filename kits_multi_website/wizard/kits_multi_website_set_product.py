from odoo import api, fields, models, _
import xlrd
import base64
from odoo.exceptions import UserError
class kits_multi_website_set_product(models.TransientModel):
    _name = "kits.multi.website.set.product"
    _description = "Kits Multi Website Set Product"

    website_ids = fields.Many2many("kits.b2c.website","set_product_b2c_website_rel","set_product_id","website_id","Websites")
    product_ids = fields.Many2many("product.product", "set_product_product_product_rel","set_product_id","product_product_id","Products")

    def action_set_product(self):                
        if self.website_ids:
            for website in self.website_ids:
                self.product_ids.write({
                    'website_ids': [(4, website.id)] 
                    })  
        else:
            self.product_ids.write({
                'website_ids': False,
            }) 
        return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                        'title': 'Process is completed.',
                        'message': 'Please reload your screen.',
                        'sticky': True,
                    }
                }
