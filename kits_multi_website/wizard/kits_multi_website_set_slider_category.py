from odoo import api, fields, models, _

class kits_multi_website_set_slider_category(models.TransientModel): 
    _name = "kits.multi.website.set.slider.category"
    _description = "Kits Multi Website Set Slider Category"

    product_ids = fields.Many2many("product.product","slider_category_product_product_rel","slider_category_id","product_id","Products")
    slider_category_ids = fields.Many2many("kits.multi.website.product.slider.category","set_slider_category_product_slider_category_rel","set_slider_category_id","product_slider_category_id","Product Slider Categories")

    def action_set_slider_categpries_to_products(self):
        if self.slider_category_ids:
            for category in self.slider_category_ids: 
                self.product_ids.write({
                    'slider_category_ids': [(4, category.id)] 
                    })  
        else:
            self.product_ids.write({'slider_category_ids':False})
