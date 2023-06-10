from odoo import fields, models, api, _
import os
import base64
from odoo.exceptions import UserError

class kits_b2b_website(models.Model):
    _name = 'kits.b2b.website'
    _description = "B2B Website"

    name = fields.Char('Name')
    website_name = fields.Selection([('b2b1', 'B2B1')], string='Type')
    url = fields.Char('Website URL')
    is_allow_for_geo_restriction = fields.Boolean('Apply Geo Restriction')
    company_id = fields.Many2one('res.company', string='Company')
    login_validity_in_days = fields.Integer('Login Validity In Days')
    reset_password_validity_in_hours = fields.Integer(
        'Reset Password Validity In Hours'
    )
    pricelist_id = fields.Many2one(
        'product.pricelist',
        string='Default Pricelist'
    )
    portal_user_id = fields.Many2one('res.groups', string='Default Portal User')
    my_dashboard_ids = fields.One2many(
        'kits.b2b.menus',
        'my_dashboard_model_id',
        'My Dashboard'
    )
    logo = fields.Char('Logo', related="image_logo")
    image_logo = fields.Char('Logo')
    stock_location_id = fields.Many2one(
        'stock.location',
        string='Stock Location'
    )
    virtual_location_id = fields.Many2one(
        'stock.location',
        string='Virtual Location'
    )
    recommended_products_ids = fields.Many2many(
        'product.product',
        string='Recommended Products'
    )
    shipping = fields.Html('Terms & Conditions')
    privacy_policy = fields.Html('Privacy Policy')
    terms_and_conditions = fields.Html('Terms and Conditions')
    show_product_image = fields.Selection([
        ('front_face', 'Front Face'),
        ('side_face', 'Side Face')],
        string="Shop Product Image Face",
        default='front_face'
    )
    home_ad_ids = fields.One2many(
        'kits.b2b.home.advertisement',
        'website_id',
        string='Header Ads'
    )
    location_text = fields.Text('Location')
    location_icon_url = fields.Char('Location Icon URL')
    location_icon = fields.Char(
        'Location Icon',
        related='location_icon_url',
        store=True
    )

    shipping_text = fields.Text('Shipping Cart')
    shipping_icon_url = fields.Char('Shipping Icon URL')
    shipping_icon = fields.Char(
        'Shipping Icon',
        related='shipping_icon_url',
        store=True
    )

    login_slider_ids = fields.One2many(
        'kits.b2b.image.model',
        'login_id',
        string="Login Slider"
    )
    homepage_meta_keyword = fields.Char('Meta Keyword    ')
    homepage_meta_title = fields.Char('Meta Title    ')
    homepage_meta_description = fields.Text('Meta Description    ')
    
    shop_meta_keyword = fields.Char('Meta Keyword')
    shop_meta_title = fields.Char('Meta Title')
    shop_meta_description = fields.Text('Meta Description')

    shipping_meta_keyword = fields.Char('Meta Keyword ')
    shipping_meta_title = fields.Char('Meta Title ')
    shipping_meta_description = fields.Text('Meta Description ')

    pp_meta_keyword = fields.Char('Meta Keyword  ')
    pp_meta_title = fields.Char('Meta Title  ')
    pp_meta_description = fields.Text('Meta Description  ')

    tc_meta_keyword = fields.Char('Meta Keyword   ')
    tc_meta_title = fields.Char('Meta Title   ')
    tc_meta_description = fields.Text('Meta Description   ')
    
    text_file_url = fields.Char('Robots File Url',compute="file_url_b_2_b")
    sitemap_url = fields.Char('Sitemap Url',compute="file_url_b_2_b")
    text_file_path = fields.Char('Robots File Path')
    text_data = fields.Text('Robots File Content')
    text_file = fields.Binary('Robots File')
    text_file_name = fields.Char('Robots File Name')

    sitemap_file_path = fields.Char('Sitemap File Path')
    sitemap_file = fields.Binary('Sitemap File')
    sitemap_name = fields.Char('Sitemap File Name')


    def file_url_b_2_b(self):
        for record in self:
            record.text_file_url = ''
            record.sitemap_url = ''
            if record.url:
                record.text_file_url = record.url+'/robots.txt'
                record.sitemap_url = record.url+'/sitemap.xml'

    def action_update_text_file(self):
        for record in self:
            file_name = '/tmp/robots.txt'
            f = open(file_name,'a')
            f.truncate(0)
            f.write(str(record.text_data))
            f.close()
            f = open(file_name,'rb')
            data = f.read()
            f.close()
            record.text_file_name = file_name.split('/')[-1]
            record.text_file = base64.b64encode(data)


    def action_update_sitemap_file(self):
        for record in self:
            file_name = '/tmp/sitemap.xml'
            if not os.path.isfile(file_name):
                f = open(file_name,'a')
                f.close()
            website_id =  self.env['kits.b2b.website'].search([('website_name','=','b2b1')])
            url_list = [website_id.url,'%s/shop '%(website_id.url),'%s/eyeglass?category=7'%(website_id.url),'%s/sunglass?category=6'%(website_id.url),'%s/sale?product group=on_sale,clearance'%(website_id.url),'%s/new-arrivals?new_arrivals=True'%(website_id.url),'%s/contact-us'%(website_id.url),'%s/aboutus'%(website_id.url),'%s/brands'%(website_id.url),'%s/faqs'%(website_id.url),'%s/login'%(website_id.url),'%s/privacy-policy'%(website_id.url),'%s/shipping'%(website_id.url),'%s/terms-conditions'%(website_id.url)]
            url_list = list(set(url_list))
            text = """<urlset>"""
            for lst in url_list:
                if lst :
                    text += " <url><loc>%s</loc></url>"%(lst.strip())

            proudct_ids = self.env['product.product'].search([('is_published_spt','=',True)])
            for pid in proudct_ids:
                text += '<url><loc>%s/product/%s</loc></url>'%(website_id.url,pid.product_seo_keyword)
            text+="</urlset>"
            text = text.replace("&","&amp;")
            f = open(file_name,'a')
            f.truncate(0)
            f.write(str(text))
            f.close()
            f = open(file_name,'rb')
            data = f.read()
            f.close()
            record.sitemap_name = file_name.split('/')[-1]
            record.sitemap_file = base64.b64encode(data)

    # def write(self, vals):
    #     res = super(kits_b2b_website,self).write(vals)
    #     for record in self:
    #         if record.is_allow_for_geo_restriction :
    #             remove_order_line_obj = self.env['sale.order.line']
    #             order_ids = self.env['sale.order'].search([('state','=','draft')])
    #             for order_id in order_ids:
    #                 for line in order_id.order_line:
    #                     if order_id.country_id.id in line.product_id.geo_restriction.ids:
    #                         remove_order_line_obj |= line
    #             if remove_order_line_obj:
    #                 remove_order_line_obj.unlink()
    #             remove_wishlist = self.env['kits.b2b.product.wishlist']
    #             wishlist_ids = remove_wishlist.search([])
    #             for index in range(0,len(wishlist_ids.ids)):
    #                 wishlist_id = wishlist_ids[index]
    #                 if wishlist_id.partner_id.country_id.id in wishlist_id.product_id.geo_restriction.ids:
    #                     remove_wishlist |= wishlist_id
    #             if remove_wishlist:
    #                 remove_wishlist.unlink()
    #     return res
