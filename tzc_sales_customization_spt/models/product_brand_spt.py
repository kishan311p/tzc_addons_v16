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
    logo = fields.Char('Image')
    brand_link = fields.Char('Image URL')
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
    
    eyeglass_avl_brand = fields.Boolean(string='Available Eyeglass Brand')
    sunglass_avl_brand = fields.Boolean(string='Available Sunglass Brand')
    new_arrival_avl_brand = fields.Boolean(string='Available New Arrival Brand')
    sale_avl_brand = fields.Boolean(string='Available Sale Brand')
    # website_published = fields.Boolean(string='Website Publish',default=True)
    # slider_image_ids = fields.One2many('product.brand.slider.image.spt', 'brand',string='Slider Images')

    @api.onchange('brand_link')
    def _onchange_brand_link(self):
        for record in self:
            record.logo = record.brand_link

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
