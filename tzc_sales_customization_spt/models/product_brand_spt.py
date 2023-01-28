# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductBrandSpt(models.Model):
    _name = 'product.brand.spt'
    # _inherit = ['website.published.multi.mixin']
    _description = 'Product Brand' 

    name = fields.Char('Brand')
    kits_product_ids = fields.One2many('product.product','brand',string="Brand ")
    description = fields.Text('   Description', translate=True)
    # website_id = fields.Many2one("website", string="Website")
    logo = fields.Char('Logo File')
    sequence = fields.Integer('Sequence', default=1, help="Gives the sequence order when displaying.")
    brand_link = fields.Char('Brand website link')
    collection_button_name = fields.Char('Collection Button Name')
    # slider_image_ids = fields.One2many('product.brand.slider.image.spt', 'brand',string='Slider Images')
    product_ids = fields.Many2many(
        'product.product',
        string='Brand Products',
        help="Add products for this brand",compute='_get_brand_data_spt',readonly=False
    )
    
    products_count = fields.Integer(
        string='Number of products',
        compute='_get_brand_data_spt',
        help='It shows the number of product counts',
    )
    
    # is_brand_page = fields.Boolean(string='Is Brand Page',help="It will set the separate landing page for this brand")
    # brand_page = fields.Many2one("website.page", string="Brand Page",help="Select the brand page which you want to set for this brand.")
    brand_image = fields.Char('Brand Image')
    brand_image = fields.Binary('Brand Image')
    desc_heading = fields.Char('Description Heading')
    brand_seo_keyword = fields.Char('Brand SEO Keyword',copy=False,help="Make sure that seo Keyword doesn't containt whitespace,slash(\,/).")
    is_logo_published = fields.Boolean('Publish logo',help='Publish logo after set logo image to show in brands slider.')
    
    eyeglass_avl_brand = fields.Boolean(string='Available Eyeglass Brand')
    sunglass_avl_brand = fields.Boolean(string='Available Sunglass Brand')
    new_arrival_avl_brand = fields.Boolean(string='Available New Arrival Brand')
    sale_avl_brand = fields.Boolean(string='Available Sale Brand')
    # website_published = fields.Boolean(string='Website Publish',default=True)
    # slider_image_ids = fields.One2many('product.brand.slider.image.spt', 'brand',string='Slider Images')

    def _get_brand_data_spt(self):
        for record in self:
            product_ids = self.env['product.product'].search([('brand', '=', record.id)]).ids
            record.product_ids = product_ids
            for brand in record:
                brand.products_count = len(product_ids)

    # def publish_brands_spt(self):
    #     for rec in self:
    #         if not rec.website_published:
    #             rec.website_published = True
    # def unpublish_brands_spt(self):
    #     for rec in self:
    #         if rec.website_published:
    #             rec.website_published = False

    # def website_publish_button(self):
    #     """
    #     Set slider filter published and unpublished on website
    #     :return:
    #     """
    #     if self.website_published:
    #         self.write({'website_published': False})
    #     else:
    #         self.write({'website_published': True})
