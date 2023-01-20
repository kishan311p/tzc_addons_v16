# -*- coding: utf-8 -*-
# Part of SnepTech. See LICENSE file for full copyright and licensing details.##
###############################################################################

from odoo import api, fields, models, _

class product_import_line_spt(models.Model):
    _name = 'product.import.line.spt'
    _description = 'Import Product Line'
    
    name = fields.Char('Name')
    variant_name = fields.Char('Variant Name')
    default_code = fields.Char('Internal Reference')
    active = fields.Boolean('Active')
    list_price = fields.Float('List Price')
    price_msrp = fields.Float('MSRP')
    standard_price = fields.Float('Standard Price')
    detailed_type = fields.Char('Type')
    barcode = fields.Char('Barcode')
    price_wholesale = fields.Float('Wholesale Price')
    brand = fields.Many2one('product.brand.spt','Brand')
    model = fields.Many2one('product.model.spt','Model')
    # size = fields.Many2one('product.size.spt','Size')
    color = fields.Many2one('kits.product.color.code','Manufacturing Color Code')    
    categ_id = fields.Many2one('product.category','Categ')

    image_url = fields.Char('Image1 URL')
    image_secondary_url = fields.Char('Image2 URL')
    import_id = fields.Many2one('product.import.spt', 'Product Import')
    taxes_id = fields.Many2many('account.tax','import_line_tax_spt_real','import_line_id','tax_id','Customer Taxes')
    
    qty = fields.Float('qty')
    hs_code = fields.Char('Hs Code')
    weight = fields.Float('Weight')
    volume = fields.Float('Volume')
    note = fields.Text(string='Notes')
    
    website_description = fields.Html('Category Description', sanitize_attributes=False)
    website_published = fields.Boolean('Website Published')
    is_published_spt = fields.Boolean('Is Published (Flag)')
    website_meta_description = fields.Text("Website meta description")
    website_meta_title = fields.Char("Website meta title")
    website_meta_keywords = fields.Char("Website meta keywords")
    # kits_ecom_categ_id = fields.Many2one('product.public.category','Website Product Category')
    is_select_for_lenses = fields.Boolean('Is Allow For Add Lenses')

    replenishable = fields.Boolean('Replenishable?')
    
    # public_categ_ids = fields.Many2many(
    #     'product.public.category', relation='product_public_category_product_import_line_spt_rel',
    #     string='Website Product Category',
    #     help="The product will be available in each mentioned eCommerce category. Go to Shop > "
            #  "Customize and enable 'eCommerce categories' to view all eCommerce categories.")
             
    country_of_origin = fields.Many2one('res.country','Country Of Origin')
    material = fields.Many2one('product.material.spt','Material')
    flex_hinges = fields.Selection([('yes','Yes'),('no','No')],'Flex Hinges')
  
    #attribute
    html_color = fields.Char('Html Color')
    color_name = fields.Char('Color Name')
    eye_size = fields.Many2one('product.size.spt','Eye Size')
    # color = fields.Char('Color')
    secondary_html_color = fields.Char('Secondary Html Color Code')

    product_color_name =  fields.Many2one('product.color.spt','Product Color Name')
    secondary_color_name =  fields.Many2one('product.color.spt','Secondary Color Name')
    
    product_seo_keyword = fields.Char('Product SEO Keyword')
    gender = fields.Selection([('male','Male'),('female','Female'),('m/f','M/F')], string='Gender')
    bridge_size = fields.Many2one('product.bridge.size.spt','Bridge Size')
    temple_size = fields.Many2one('product.temple.size.spt','Temple Size')
    shape = fields.Many2one('product.shape.spt','Shape')
    lense_color_name =  fields.Many2one('product.color.spt','Lense Color Name')
    aging = fields.Many2one('product.aging.spt','Aging')
    geo_restriction = fields.Many2many('res.country','import_line_with_country_real','import_line_id','country_id','Geo Restriction')
    rim_type = fields.Many2one('product.rim.type.spt','Rim Type')
    custom_message = fields.Text(string='Custom Message', default='', translate=True)
    # eto_sale_method = fields.Selection([('regular','Regular'),('fs','FS')],default='regular',string='ETO Sale Method')
    # website_url = fields.Char('Website URL', help='The full URL to access the document through the website.', readonly= False)
   
    price_wholesale_usd = fields.Float('Wholesale Price USD',digits='Product Price',help="Wholesale Price")
    price_msrp_usd = fields.Float('MSRP USD',digits='Product Price',help="MSRP Price")
    lst_price_usd = fields.Float('Public Price USD',digits='Product Price',help="Public Price In USD")
    sale_type = fields.Selection([('clearance','Clearance'),('on_sale','On Sale')],'Sale Type')
    on_sale_usd_in_percentage = fields.Float('Sale USD Percentage')
    on_sale_usd = fields.Float('Sale USD')
    temporary_out_of_stock = fields.Boolean('Temporary Out Of Stock')
    new_arrivals = fields.Boolean('New Arrivals')
    length = fields.Float('Length')
    width = fields.Float('Width')
    height = fields.Float('Height')
    old_id = fields.Char('Old Id')

    shape_id = fields.Many2one('product.shape.spt','Shape ')
    material_id = fields.Many2one('product.material.spt','Material ')
#     material_ids = fields.Many2many('product.material.spt','product_import_line_with_material_real','product_import_line_id','material_id','Materials')
#     shape_ids = fields.Many2many('product.shape.spt','product_import_line_with_shape_real','product_import_line_id','shape_id','Shapes')
    product_brand_commission = fields.Float('Product Brand Commission')
    case_type = fields.Selection([('original', 'Original'),('generic', 'Generic')],"Case Type")
    case_image_url = fields.Char('Case Image Url')

    on_consignment = fields.Boolean('On Consignment')
    minimum_qty = fields.Integer('Minimum Qty')
    is_new_price = fields.Boolean('New Price')
    is_forcefully_unpublished = fields.Boolean('Forcefully Unpublished')
    is_b2c_published = fields.Boolean('B2C1 Published')
    is_3d_model = fields.Boolean('Is 3D Model')
    application_type = fields.Selection([('0','B2B'),('1','Both'),('2','Only B2C')],'Application Type')
    b2c_keyword = fields.Char('B2C Keyword')
    b2c_title = fields.Char('B2C Title')
    b2c_description = fields.Text('B2C Description')
