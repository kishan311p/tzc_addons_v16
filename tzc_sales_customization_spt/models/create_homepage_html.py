from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class create_homepage_html(models.Model):
    _name = 'create.homepage.html'
    _rec_name = 'name'

    name = fields.Char('Name',required=True)
    header_url = fields.Char('Header Url')
    header_redirect_url = fields.Char('Header Redirect Url')
    banner_ids = fields.One2many('tzc.homepage.banner','home_page_id')
    product_ids = fields.Many2many('product.product',string='Products')
    home_html_code = fields.Char('Html Code')
    body_html = fields.Char('Body')
    view_more_redirect_url = fields.Char('View More Redirect Url')
    unsubscribe_redirect_url = fields.Char('Unsubscribe Redirect Url')

    def generate_html(self):
        self.body_html=''        
        if self.header_url:
            web_url = self.env['kits.b2b.website'].search([],limit=1).url
            header=f'''
                <a href="{web_url}" tyle="text-decoration:none;background-color:transparent;color:rgb(0,135,132)" target="_blank">
                    <img src={self.header_url} class="header-img" border="0" align="middle" loading="" style="box-sizing:border-box;vertical-align:middle;width: 80%;height: auto;">
                </a>
            '''
        if self.product_ids:
            product_table=''
            product_table+='''<div>'''
            row=0
            banner=0
            all_products=self.product_list()
            banner_sequence = self.products_for_banner()
            for products in all_products:
                if self.banner_ids:
                    if row in banner_sequence :
                        product_table=product_table+f'''
                        <div style="">
                            <a href="{self.banner_ids[banner].banner_redirect_url if self.banner_ids[banner].banner_redirect_url else ''}" style="text-decoration:none;background-color:transparent;color:rgb(0,135,132)" target="_blank">
                                <img src={self.banner_ids[banner].banner_url} border="0" style="border-style:none;box-sizing:border-box;vertical-align:middle;text-decoration:none;border:none;float:none;width: 80%;height: auto;display:inline-block" align="middle" loading=""> 
                            </a>
                        </div>
                        '''
                        banner+=1
                # product_table=product_table+'''<table class="" style='width:100%;display:flex'>'''
                product_table=product_table+'''<table> <tr style="background-color: #FDFDFD;">'''
                for product in products:
                    style='color:white'
                    product_type=''
                    if self.product_ids[product].new_arrivals:
                        # product_type = 'New Arrivals'
                        product_type = 'https://cdn.teameto.com/data/B2B/email/new-arrivals.png'
                        style='width:50%;'
                    else:
                        if self.product_ids[product].sale_type == 'on_sale':
                            # product_type = 'On Sale'
                            product_type = 'https://cdn.teameto.com/data/B2B/email/on-sale.png'
                            style='width:40%;'
                        elif self.product_ids[product].sale_type == 'clearance':
                            # product_type = 'Clearance'
                            product_type = 'https://cdn.teameto.com/data/B2B/email/clearance.png'
                            style='width:50%;'
                        
                    product_table=product_table+f'''
                        <td style="width: 33.3333%;">
                            <a href="{self.product_ids[product].product_seo_url if self.product_ids[product].product_seo_url else ''}">
                                <div style='margin:20px 15px 20px 15px;border: 1px solid rgba(31,123,111,.2);padding: 10px;background-color: var(--white-color);border-radius: 20px;transition: .3s;overflow: hidden;position: relative!important;'>
                                        <div class="">
                                            <div>
                                            <img src={product_type} style="{style}"> </img>
                                            </div>
                                            <a >
                                                <img src={self.product_ids[product].primary_image_url} style="border-style:none;box-sizing:border-box;vertical-align:middle;text-decoration:none;border:none;float:none;width:380px;height: auto !important;display:inline-block;"  border="0" align="middle"> </img>
                                            </a>
                                        </div>
                                        <div align='center' style='margin-bottom:10px;margin-top:10px'>
                                            <h6><a style='font-weight:bold;font-size: 120%;color:#1C7468'>{self.product_ids[product].brand_name if self.product_ids[product].brand_name else ''}</a></h6>
                                            <p style='color:#1C7468;font-size: 120%;'>{self.product_ids[product].b2b_name if self.product_ids[product].b2b_name else '   '}</p>
                                        </div>
                                </div>
                            </a>
                        </td>
                    '''
                product_table=product_table+'''</tr></table>'''
                row+=1
            product_table+='''</div>'''
            
       
        button=f'''
            <div style="padding-bottom:40px;padding-top:30px;width: 90%;height: auto;" class="row">
                <div class="col-12" align="center">
                    <a href="{self.view_more_redirect_url if self.view_more_redirect_url else 'https://teameto.com'}" target="_blank" style="padding-bottom:10px;background-color: rgb(233,254,250); padding: 12px 20px 12px 20px; text-decoration: none; color: #1C7468; border-radius: 500px; font-size:16px;    border: 1px solid #1C7468;" >
                        View More
                    </a>
                </div>
            </div>
        '''

        footer=f'''
        <div style="width: 90%;height: auto;border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit;word-break:break-word;padding:0px 10px 28px;font-family:'Cabin',sans-serif" align="left">
            <table style="border-style:solid none none none;width: 55%;box-sizing:border-box;border-top-color:#1c7468;border-top-width:2px;caption-side:bottom;border-collapse:collapse;table-layout:fixed;border-spacing:0;vertical-align:top;border-top:2px solid #1c7468" width="79%" height="0px" cellspacing="0" cellpadding="0" border="0" align="center">
                <tbody style="border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit">
                    <tr style="border-style:solid;box-sizing:border-box;border-width:0px;border-color:inherit;vertical-align:top;width:100%">
                        <td style="border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit;word-break:break-word;border-collapse:collapse;vertical-align:top;font-size:0px;line-height:0px">
                            <span> <![CDATA[&nbsp;]]></span>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>

        <div style="width: 90%;height: auto;border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit;word-break:break-word;padding:25px 10px 10px;font-family:'Cabin',sans-serif" align="left">
            <table style="box-sizing:border-box;border-collapse:collapse;caption-side:bottom" width="100%" cellspacing="0" cellpadding="0" border="0">
                <tbody style="border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit">
                    <tr style="border-style:solid;box-sizing:border-box;border-width:0px;border-color:inherit;width:100%">
                        <td style="border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit;padding-right:0px;padding-left:0px" align="center"> 
                            <a href="https://teameto.com" style="text-decoration:none;box-sizing:border-box;color:#35979c" target="_blank"> 
                                <img src="https://cdn.teameto.com/data/B2B/logo.png" alt="" title="" style="border-style:none;box-sizing:border-box;outline-width:initial;outline-style:none;outline-color:initial;vertical-align:middle;outline:none;text-decoration:none;clear:both;border:none;height:35px;float:none;width:270px;max-width:300px;display:inline-block" width="270" height="35" border="0" align="middle" class="CToWUd" data-bit="iit"/>
                            </a>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        <br/>
        <div style="color:black;width: 90%;height: auto;" align="center">
            {self.env.company.street if self.env.company.street else ''}
            <br/>
            <br/>
            {self.env.company.city if self.env.company.city else ''}
            ,
            {self.env.company.state_id.name if self.env.company.state_id.name else ''}
            ,
            {self.env.company.country_id.name if self.env.company.country_id.name else ''}
            {self.env.company.zip if self.env.company.zip else ''}
            <br/>
            <br/>
            <a href="{self.env.company.website if self.env.company.website else ''}" style="text-decoration:none ;color: black;">{self.env.company.website if self.env.company.website else ''}</a>
            <br/>
            <br/>
            <a href="tel:+1%20905%20944%209786" rel="noopener" style="text-decoration:none;background-color:transparent;color:#000000" target="_blank">
            {self.env.company.phone if self.env.company.phone else ''}
            </a>
            |
            <a href="{self.env.company.email if self.env.company.email else ''}" style="text-decoration:none ; color: black;" >{self.env.company.email if self.env.company.email else ''}</a>
        </div>
        <div style="width: 90%;height: auto;background-color:#E9ECEF;padding: 30px 0px 20px 140px;">
            <a href="{self.unsubscribe_redirect_url if self.unsubscribe_redirect_url else 'https://teameto.com'}">
                Unsubscribe
            </a>
            <br/>
            <br/>
            <p style='color:#1C7468'>
            © 2023 All Rights Reserved
            </p>
        </div>
        '''

        if self.env.user.signature:
            signature = f''' 
            <p style="width: 80%;height: auto;;padding-top:30px">
                {self.env.user.signature}
            </p>
            '''
        style_css= '''
        <style>
            @media (max-width: 575.98px) {
                .name-font{
                    font-size: 150%;
                }
            }
            @media (max-width: 767.98px) {
                .name-font{
                    font-size: 200%;
                }
            }
        </style>
        '''
        # give a html code to self.body_html
        self.body_html+=style_css
        if self.header_url:
            self.body_html+=header
        if self.product_ids:
            self.body_html+=product_table
        self.body_html+=button
        self.body_html+=footer
            
        if self.env.user.signature:
            self.body_html+=signature

        
    def product_list(self):
        all_products=[]
        products=[]
        for i in range(0,len(self.product_ids)):
            if len(products)!=3:
                products.append(i)
            if len(products)==3:
                all_products.append(products)
                products=[]
        if len(self.product_ids) %3 != 0:
            all_products.append(products)
        
        return all_products
    
    def products_for_banner(self):
        if self.banner_ids:
            all_products = self.product_list()
            products_for_banner = []
            after_no = round(len(all_products)/len(self.banner_ids))
            products_rows = [x for x in range(0,len(all_products))]
            no=0
            for row in products_rows:
                if len(products_for_banner)==len(self.banner_ids):
                    pass
                else:
                    if row==0:
                        products_for_banner.append(0)
                    else:
                        no=no+after_no
                        if no in products_rows:
                            products_for_banner.append(no)
            return products_for_banner
