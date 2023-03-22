from odoo import api, fields, models, _
import os
from odoo.exceptions import UserError
import base64

class kits_b2c_website(models.Model):
    _name = "kits.b2c.website"
    _description = "Kits B2C Website"

    def _get_domain(self):
        return [('id','in',self.env.ref('base.group_user').users.ids)]

    name = fields.Char("Name")
    url = fields.Char("URL")
    domain = fields.Char("domain",compute="_compute_logo",store=True)
    logo = fields.Char("Logo",compute="_compute_logo",store=True)
    website_name = fields.Selection([], string="Website Name")
    logo_public_url = fields.Char("Image Public Url")
    favicon = fields.Char("Favicon",compute="_compute_favicon",store=True)
    favicon_public_url = fields.Char("Favicon Public URL")
    shoppage_banner_ids = fields.One2many('kits.multi.website.shoppage.banner','website_id','Shoppage Banner Lines')
    sale_pricelist_id = fields.Many2one("product.pricelist","Sale Pricelist")
    msrp_pricelist_id = fields.Many2one("product.pricelist","MSRP Pricelist")
    is_allow_for_geo_restriction = fields.Boolean('Apply Geo Restriction') 
    sale_order_sequence_id = fields.Many2one('ir.sequence', string='Sale Order Sequence')
    invoice_sequence_id = fields.Many2one('ir.sequence', string='Invoice Sequence')
    return_request_sequence_id = fields.Many2one('ir.sequence', string='Return Request Sequence')
    text_file_path = fields.Char('Robots File Path')
    text_data = fields.Text('Robots File Content')
    sitemap_file_path = fields.Char('Sitemap File Path')
    sitemap_file = fields.Binary('Sitemap File')
    sitemap_name = fields.Char('Sitemap File Name')
    return_product_days = fields.Float('Return Product Days')
    text_file_url = fields.Char('Robots File Url',compute="file_url")
    sitemap_url = fields.Char('Sitemap Url',compute="file_url")
    shipping_text = fields.Html('Shipping')
    privacy_policy_text = fields.Html('Privacy Policy')
    terms_and_condition_text = fields.Html('Terms and Condition')
    faqs_ids = fields.One2many('kits.key.value.model','website_id',"Faq's")
    user_id = fields.Many2one('res.users', string='Default Salesperson',domain=_get_domain)


    @api.depends()
    def file_url(self):
        for record in self:
            record.text_file_url = ''
            record.sitemap_url = ''
            if record.url:
                record.text_file_url = record.url+'/robots.txt'
                record.sitemap_url = record.url+'/sitemap.xml'

    def action_daily_cron(self):
        self= self.search([])
        self.action_update_text_file()
        self.action_update_sitemap_file()

    @api.depends('logo_public_url')
    def _compute_logo(self):
        for record in self:
            record.logo = record.logo_public_url
            

    @api.depends('favicon_public_url')
    def _compute_favicon(self):
        for record in self:
            record.favicon = record.favicon_public_url


    @api.depends('url')
    def _compute_url(self):
        for record in self:
            record.domain = record.url

   
    def action_update_text_file(self):
        for record in self:
            if os.path.isdir(record.text_file_path.strip()):
                file_name = record.text_file_path.strip()+'/robots.txt'
                f = open(file_name,'a')
                f.truncate(0)
                f.write(str(record.text_data))
                f.close()


    def action_update_sitemap_file(self):
        for record in self:
            if os.path.isdir(record.sitemap_file_path.strip()):
                file_name = record.sitemap_file_path.strip()+'/sitemap.xml'
                website_id =  self.env['kits.b2c.website'].search([('website_name','=','b2c1')])
                page_id = self.env['kits.b2c1.website.page'].search([('website_id','=',website_id.id)])
                attribute_filter_id = self.env['kits.multi.website.attribute.filter'].search([('website_id','=',website_id.id)])
                url_list = [website_id.url,'%s/shop '%(website_id.url),'%s/contact-us'%(website_id.url),'%s/our-story'%(website_id.url)]
                url_list = list(set(url_list))
                text = """<urlset>"""
                for lst in url_list:
                    if lst :
                        text += " <url><loc>%s</loc></url>"%(lst.strip())

                proudct_ids = self.env['product.product'].search([('application_type','in',('1','2'))])
                for pid in proudct_ids:
                    text += '<url><loc>%s/product-details?productid=%s</loc></url>'%(website_id.url,pid.id)
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
