# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProductBrandSpt(models.Model):
    _name = 'product.brand.spt'
    # _inherit = ['website.published.multi.mixin']
    _description = 'Product Brand' 
    _order = "name asc"

    active = fields.Boolean('Active', default=True)
    name = fields.Char('Brand',index=True)
    kits_product_ids = fields.One2many('product.product','brand',string="Brand ")
    description = fields.Text('   Description', translate=True)
    # website_id = fields.Many2one("website", string="Website")
    brand_link = fields.Char('Image URL')
    logo = fields.Char('Image',related='brand_link')
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
    # case_type = fields.Selection([('original', 'Original'),('generic', 'Generic')],"Case Type",default='generic')
    model_ids = fields.One2many('product.model.spt', 'brand_id', string='Model')
    case_product_ids = fields.One2many('product.product', 'brand_id', string='Case Products')
    geo_restriction = fields.Many2many('res.country','brand_with_country_real','brand_id','country_id','Geo Restriction', index=True)
    sort_name = fields.Char('Sort Name')
    
    def action_open_brand_products_spt(self):
        return {
            "name":_("Brand Products"),
            "type":"ir.actions.act_window",
            "res_model":"product.product",
            "view_mode":"tree,form",
            "domain":[('is_pending_price','=',False),('brand','=',self.id)],
            "target":"current",
        }

    @api.onchange('brand_link')
    def _onchange_brand_link(self):
        for record in self:
            record.logo = record.brand_link

    def _get_brand_data_spt(self):
        for record in self:
            product_ids = self.env['product.product'].search([('is_pending_price','=',False),('brand', '=', record.id)]).ids
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

    def action_active(self):
        for record in self:
            record.active = True

    def action_unactive(self):
        for record in self:
            record.active = False

    def unlink(self):
        if self.env.ref('base.group_system').id  in  self.env.user.groups_id.ids or self.env.ref('tzc_sales_customization_spt.group_marketing_user').id  in  self.env.user.groups_id.ids or self.env.ref('stock.group_stock_manager').id  in  self.env.user.groups_id.ids :
            product_ids = self.env['product.product'].with_context(pending_price=True).sudo().search([('brand','in',self.ids),'|',('active','=',False),('active','=',True)])
            if not product_ids:
                return super(ProductBrandSpt,self).unlink()
            else:
                raise UserError(_("%s product in this record so you can't delete this record"%(','.join(product_ids.mapped('name')))))
                
        else:
            raise UserError(_("You can't delete this record. Please contact an Administrator."))
