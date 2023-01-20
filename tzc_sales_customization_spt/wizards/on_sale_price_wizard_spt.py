# -*- coding: utf-8 -*-
# Part of SnepTech See LICENSE file for full copyright and licensing details.##
##############################################################################
from odoo import models, fields, api, _


class on_sale_price_wizard_spt(models.TransientModel):
    _name = 'on.sale.price.wizard.spt'
    _description = 'On Sale Price'

    on_sale_usd_in_percentage = fields.Float('Price In Percentage')
    on_sale_usd = fields.Float('USD Price')    
    product_ids = fields.Many2many('product.product','on_sale_price_wizard_product_product_rel','wizard_id','product_id',string='Products')
    price_type = fields.Selection([('fix','Fix'),('percentage','Percentage')],default='fix',string='Price On')
    sale_type = fields.Selection([('clearance','Clearance'),('on_sale','On Sale')],'Sale Type')
    
    def action_process(self):
        # catalog_obj = self.env['sale.catalog']
        # catalog_obj.connect_server()
        # method = catalog_obj.get_method('action_process_on_sale_price_wizard_model')
        # if method['method']:
        #     localdict = {'self': self,}
        #     exec(method['method'], localdict)
        
        for product in self.product_ids:
            if self.sale_type == 'on_sale':
                product.sale_type = 'on_sale'
                if self.price_type == 'percentage':
                    product.on_sale_usd_in_percentage = self.on_sale_usd_in_percentage
                    product.on_sale_usd = False

                else:
                    product.on_sale_usd = self.on_sale_usd
                product.calculate_onsale_price_for_product_import()
            if self.sale_type == 'clearance':
                product.sale_type = 'clearance'
                if self.price_type == 'percentage':
                    product.clearance_usd_in_percentage = self.on_sale_usd_in_percentage
                    product.clearance_usd = False
                else:
                    product.clearance_usd = self.on_sale_usd
                product.calculate_clearance_price_for_product_import() 
