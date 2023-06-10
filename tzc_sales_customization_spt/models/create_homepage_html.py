from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class create_homepage_html(models.Model):
    _name = 'create.homepage.html'
    _description = 'Create Homepage HTML'
    _rec_name = 'name'

    name = fields.Char('Name',required=True)
    price_inflation = fields.Boolean('Price Inflation')
    inflation = fields.Float('Inflation (%)')
    header_url = fields.Char('Header Image Url')
    header_image = fields.Char('Header Image', related='header_url')
    header_redirect_url = fields.Char('Header Redirect Url')
    banner_ids = fields.One2many('tzc.homepage.banner','home_page_id')
    product_ids = fields.Many2many('product.product',string='Products')
    home_html_code = fields.Char('Html Code')
    body_html = fields.Char('Body')
    view_more_redirect_url = fields.Char('View More Redirect Url')
    unsubscribe_redirect_url = fields.Char('Unsubscribe Redirect Url')
    face_side = fields.Selection([('front_face', 'Front Face'),('side_face', 'Side Face')],default='front_face')

    def generate_html(self):
        self.body_html=''        
        if self.header_url:
            web_url = self.env['kits.b2b.website'].search([],limit=1).url
            header='''
                <!DOCTYPE html>
                <html>

                <head>
                <body class="body" style="padding:0 !important; margin:0 !important; display:block !important; min-width:100% !important; width:100% !important; -webkit-text-size-adjust:none;">
                    <table width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="">
                        <tr>
                            <td align="center" valign="top">
                                <!-- Main -->
                                <table width="450" border="0" cellspacing="0" cellpadding="0" class="mobile-shell">
                                    <tr>
                                        <td class="td" style="width:450px; min-width:450px; font-size:0pt; line-height:0pt; padding:0; margin:0; font-weight:normal;">
                                            <!-- Header -->
                                            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                '''
            header+=f'''
                 <tr>
                    <td class="p30-15-0" style="padding: 0px 45px 0px 45px;">
                        <a href="{self.header_redirect_url}">
                            <img src={self.header_url} border="0" style="border-style:none;box-sizing:border-box;vertical-align:middle;text-decoration:none;border:none;float:none;width:100%;height:auto;display:inline-block" align="middle" width="100%"
                                height="100%">
                        </a>
                    </td>
                </tr>
            '''
        if self.product_ids:
            product_table=''
            row=0
            banner=0
            products_l=self.product_list()
            all_products = self.products_for_banner(products_l)
            for products in all_products:
                if type(products) == dict:
                    if products['banner_id']:
                        product_table=product_table+f'''
                            <layout label='Section B'>
                                <table width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="#ffffff">
                                    <tr>
                                        <td class="p30-15-0" style="padding: 15px 30px 0px 30px;">
                                            <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                <tr>
                                                    <td class="h5-center" style="color:#a1a1a1; font-family:'Raleway', Arial,sans-serif; font-size:16px; line-height:22px; text-align:center;">
                                                        <a href="{products['banner_id'].banner_redirect_url if products['banner_id'].banner_redirect_url else ''}">
                                                            <img src={products['banner_id'].banner_url}  border="0" style="border-style:none;box-sizing:border-box;vertical-align:middle;text-decoration:none;border:none;float:none;width:97%;height:auto;display:inline-block" align="middle"
                                                                width="100%" height="100%">
                                                        </a>
                                                    </td>
                                                </tr>

                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </layout>
                            '''
                else:
                    product_table=product_table+'''<layout label='Section 8'>'''
                    product_table=product_table+'''<table width="100%" border="0" cellspacing="0" cellpadding="0" bgcolor="#ffffff">
                                                    <tr>
                                                        <td style="padding: 0px 30px;" align="center">
                                                            <table class="center" border="0" cellspacing="0" cellpadding="0" style="text-align:center;">
                                                                <tr>'''
                    # product_table=product_table+'''<table style="width:97%;height: auto;background-color: #FDFDFD;"> <tr style="">'''
                    for product in products:
                        style='color:white'
                        product_type=''
                        if product != 'False':
                            pro_price = 0
                            w_price = self.product_ids[product].price_wholesale
                            if self.product_ids[product].sale_type  == 'on_sale':
                                pro_price = self.product_ids[product].on_sale_usd
                            elif self.product_ids[product].sale_type == 'clearance':
                                pro_price = self.product_ids[product].clearance_usd
                            else:
                                pro_price = self.product_ids[product].lst_price

                            if self.price_inflation and self.inflation != 0:
                                pro_price+=pro_price*self.inflation/100
                                w_price+=w_price*self.inflation/100

                            if self.product_ids[product].new_arrivals:
                                product_type = "<img src='https://cdn.teameto.com/data/B2B/email/new-arrivals.png' style='width:50%;'> </img>"
                            else:
                                if self.product_ids[product].sale_type == 'on_sale':
                                    product_type = "<img src='https://cdn.teameto.com/data/B2B/email/on-sale.png' style='width:40%;'> </img>"
                                elif self.product_ids[product].sale_type == 'clearance':
                                    product_type = "<img src='https://cdn.teameto.com/data/B2B/email/clearance.png' style='width:50%;'> </img>"
                                else:
                                    product_type = "<img src='https://cdn.teameto.com/data/B2B/email/clearance.png' style='display:none;width:50%;'> </img>"
                            if self.face_side == 'side_face':
                                img_url = self.product_ids[product].sec_image_url
                            else:
                                img_url = self.product_ids[product].primary_image_url
                            product_table=product_table+f'''
                                <td>
                                    <a href="{self.product_ids[product].product_seo_url if self.product_ids[product].product_seo_url else ''}">
                                        <div style="margin:20px 10px 0px 10px;width: max-content;border: 1px solid rgba(31,123,111,.2);padding: 10px;background-color: var(--white-color);border-radius: 20px;transition: .3s;overflow: hidden;position: relative!important;">
                                            <table>
                                                <tr>
                                                    <td>
                                                        <a href="{self.product_ids[product].product_seo_url if self.product_ids[product].product_seo_url else ''}">
                                                            <div style="text-align: -webkit-left;width:230px;height: 34px;">
                                                                {product_type} 
                                                            </div>
                                                            <img src={img_url} style="border-style:none;box-sizing:border-box;vertical-align:middle;text-decoration:none;border:none;float:none;width:230px;height: auto !important;display:inline-block;" border="0" align="middle" loading=""> 
                                                        </a>
                                                    </td>
                                                </tr>
                                                <tr align="center" style="margin-bottom:10px;margin-top:10px">
                                                    <td>
                                                        <a href="{self.product_ids[product].product_seo_url if self.product_ids[product].product_seo_url else ''}">
                                                            <h6 style="margin: 0 0 16px 0;">
                                                                <a href="{self.product_ids[product].product_seo_url if self.product_ids[product].product_seo_url else ''}">
                                                                    <a style="font-weight:bold;font-size: 13px;margin-bottom: 15px !important;color:#1C7468">{self.product_ids[product].brand_name if self.product_ids[product].brand_name else ''}
                                                                    </a>
                                                                </a>
                                                            </h6>
                                                            <p style="color:#1C7468;font-size: 120%;margin-bottom: 21px !important;font-size:13px ;">{self.product_ids[product].b2b_name if self.product_ids[product].b2b_name else '   '}</p>
                                                            <span class="price mb-0" style="font-weight: 500;color:#1f7b6f;font-size: 13px;justify-content: center;align-items: center;margin-bottom: 10px;">
                                                                <del style="font-weight: 300;color:#ff7373;margin-right: 8px;">
                                                                    <font style="vertical-align: inherit;">
                                                                        <font style="vertical-align: inherit;"><b style="font-weight: bold !important;">${'{:,.2f}'.format(w_price)}</b></font>
                                                                    </font>
                                                                </del>
                                                                <font style="vertical-align: inherit;">
                                                                    <font style="vertical-align: inherit;font-size: 13px;"><b>${'{:,.2f}'.format(pro_price)}</b></font>
                                                                </font>
                                                            </span>
                                                        </a>
                                                    <td>
                                                </tr>
                                            </table>
                                        </div>
                                    </a>
                                </td>
                            '''
                        else:
                            product_table=product_table+f'''
                                <td style="width: 33.3333%;border:none;">
                                    <a href="" style="display: none;">
                                        <div style='margin:20px 15px 20px 15px;display: none;padding: 10px;width: max-content;background-color: var(--white-color);border-radius: 20px;transition: .3s;overflow: hidden;position: relative!important;'>
                                            <div class="">
                                                <div>
                                                <img src="" style="" class="d-none"> </img>
                                                </div>
                                                <a >
                                                    <img src="" style="border-style:none;vertical-align:middle;text-decoration:none;border:none;float:none;width:380px;height: auto !important;display:inline-block;"  border="0" align="middle" class="d-none"> </img>
                                                </a>
                                            </div>
                                            <div align='center' style='margin-bottom:10px;margin-top:10px'>
                                                <h6><a style='font-weight:bold;font-size: 120%;color:#1C7468'></a></h6>
                                                <p style='color:#1C7468;font-size: 120%;'></p>
                                                <span class="price mb-0 ng-star-inserted">
                                                    <del>
                                                        <font style="vertical-align: inherit;">
                                                            <font style="vertical-align: inherit;">$150.00</font>
                                                        </font>
                                                    </del>
                                                    <font style="vertical-align: inherit;">
                                                        <font class="" style="vertical-align: inherit;">$88.80 USD</font>
                                                    </font>
                                                </span>
                                            </div>
                                        </div>
                                    </a>
                                </td>
                            '''
                    product_table=product_table+''' </tr>
                                                    </table>
                                                </td>
                                            </tr>
                                        </table>'''
                    row+=1
        
        button=f'''
           <table width="100%" border="0" cellspacing="0" cellpadding="0">
                <tr>
                    <td class="p10-15-0" bgcolor="#ffffff" style="border-radius: 0px 0px 20px 20px; padding: 0px 30px 0px 30px;">
                        <table width="100%" border="0" cellspacing="0" cellpadding="0">
                            <tr>
                                <td class="m-padder2" align="center" style="">
                                    <table class="center" border="0" cellspacing="0" cellpadding="0" style="text-align:center;">
                                        <div style="padding-bottom:16px;padding-top:48px;" class="row">
                                            <div class="col-12" align="center">
                                                <a href="{self.view_more_redirect_url if self.view_more_redirect_url else 'https://teameto.com'}" target="_blank" style="padding-bottom:10px;background-color: rgb(233,254,250); padding: 12px 20px 12px 20px; text-decoration: none; color: #1C7468; border-radius: 500px; font-size:16px;    border: 1px solid #1C7468;">
                                                View More
                                            </a>
                                            </div>
                                        </div>
                                    </table>
                                </td>
                            </tr>
        '''
        footer=f'''
        <tr>
            <td align="center" class="p10-15" style=" padding: 0px;    border-top: none;">
                <table class="center" border="0" cellspacing="0" cellpadding="0" style="text-align:center;">
                    <div style="border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit;word-break:break-word;padding:0px 10px 28px;font-family:'Cabin',sans-serif"
                        align="left">
                        <table style="border-style:solid none none none;width: 55%;box-sizing:border-box;border-top-color:#1c7468;border-top-width:2px;caption-side:bottom;border-collapse:collapse;table-layout:fixed;border-spacing:0;vertical-align:top;border-top:2px solid #1c7468"
                            width="79%" height="0px" cellspacing="0" cellpadding="0" border="0" align="center">
                            <tbody style="border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit">
                                <tr style="border-style:solid;box-sizing:border-box;border-width:0px;border-color:inherit;vertical-align:top;width:100%">
                                    <td style="    border-top: none;border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit;word-break:break-word;border-collapse:collapse;vertical-align:top;font-size:0px;line-height:0px">
                                        <span> <!--[CDATA[&nbsp;]]--></span>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </table>
            </td>
        </tr>
        <tr>
            <td align="center" class="p10-15" style=" padding: 0px;">
                <div style="border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit;word-break:break-word;padding:25px 10px 10px;font-family:'Cabin',sans-serif"
                    align="left">
                    <table style="box-sizing:border-box;border-collapse:collapse;caption-side:bottom" width="100%" cellspacing="0" cellpadding="0" border="0">
                        <tbody style="border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit">
                            <tr style="border-style:solid;box-sizing:border-box;border-width:0px;border-color:inherit;width:100%">
                                <td style="border-style:solid;box-sizing:border-box;border-left-width:0px;border-bottom-width:0px;border-right-width:0px;border-top-width:0px;border-left-color:inherit;border-bottom-color:inherit;border-right-color:inherit;border-top-color:inherit;padding-right:0px;padding-left:0px"
                                    align="center">
                                    <a href="https://teameto.com" style="text-decoration:none;box-sizing:border-box;color:#35979c" target="_blank">
                                        <img src="https://cdn.teameto.com/data/B2B/logo.png" style="border-style:none;box-sizing:border-box;outline-width:initial;outline-style:none;outline-color:initial;vertical-align:middle;outline:none;text-decoration:none;clear:both;border:none;height:35px;float:none;width:270px;max-width:300px;display:inline-block"
                                            width="270" height="35" border="0" align="middle" class="CToWUd" data-bit="iit" loading="">
                                    </a>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </td>
        </tr>
        <tr>
            <td align="center" class="p10-15" style=" padding: 0px;font-size: 15px;">
                <div style="color:black;" align="center">
                    <p style="margin: 22px;">{self.env.company.street if self.env.company.street else ''}</p>
                    <p style="margin: 22px;">{self.env.company.city if self.env.company.city else ''}
                    ,
                    {self.env.company.state_id.name if self.env.company.state_id.name else ''} 
                    ,
                    {self.env.company.country_id.name if self.env.company.country_id.name else ''}
                    {self.env.company.zip if self.env.company.zip else ''}</p>
                    <p style="margin: 25px;text-decoration: underline;"><a href="{self.env.company.website if self.env.company.website else ''}" style="text-decoration:none ;color: black;">{self.env.company.website if self.env.company.website else ''}</a></p>
                    <p style="margin: 22px;text-decoration: underline;"><a href="tel:{self.env.company.phone if self.env.company.phone else ''}" rel="noopener" style="text-decoration:none;background-color:transparent;color:#000000" target="_blank">
                    {self.env.company.phone if self.env.company.phone else ''}
                    </a>| <a href="mailto:{self.env.company.email if self.env.company.email else ''}" style="text-decoration:none ; color: black;" >{self.env.company.email if self.env.company.email else ''}</a></p>
                </div>
            </td>
        </tr>
        <tr>
            <td>
                <div class="o_layout oe_unremovable oe_unmovable bg-200 o_empty_theme" data-name="Mailing" style="width: 90.5%;margin:auto;">
                    <div class="container o_mail_wrapper o_mail_regular oe_unremovable" style="padding: 0px !important;;max-width: unset !important;">
                        <div class="row">
                            <div class="col o_mail_no_options o_mail_wrapper_td bg-white oe_structure o_editable theme_selection_done">
                                <div class="s_footer_social o_mail_block_footer_social o_mail_footer_social_center o_mail_snippet_general bg-200" data-snippet="s_mail_block_footer_social" data-name="Footer Center">
                                    <div class="container text-center"  style="padding: 18px;">
                                        <div class="row">
                                            <div class="col-lg o_mail_footer_links">
                                                <a role="button" href="{self.unsubscribe_redirect_url if self.unsubscribe_redirect_url else 'https://teameto.com'}" class="btn btn-link o_default_snippet_text" style="padding: 0 0 10px 0;font-size: 15px;text-align: center;">Unsubscribe</a>
                                            </div>
                                        </div>
                                        <div class="row" style="font-size:15px">
                                            <div class="col-lg">
                                                <p class="o_default_snippet_text">
                                                    © 2023 All Rights Reserved
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </td>
        </tr>
        '''
        style_css= '''
        '''
        # give a html code to self.body_html
        self.body_html+=style_css
        if self.header_url:
            self.body_html+=header
        if self.product_ids:
            self.body_html+=product_table
        self.body_html+=button
        self.body_html+=footer 
        self.body_html+='''
                                </td>
                            </tr>
                            </table>
                    </body>

                </html>''' 
            
        # if self.env.user.signature:
        #     self.body_html+=signature

        
    def product_list(self):
        all_products=[]
        products=[]
        for i in range(0,len(self.product_ids)):
            if len(products)!=3:
                products.append(i)
            if len(products)==3:
                all_products.append(products)
                products=[]
        if len(self.product_ids) % 3 != 0:
            if len(products) == 2:
                products.append('False')
            else:
                for i in range(2):
                    products.append('False')
            all_products.append(products)
        
        return all_products
    
    def products_for_banner(self,all_products):
        products_for_banner = []
        for id in self.banner_ids:
            if len(all_products) >= id.row_number:
                all_products.insert(id.row_number-1 ,{'banner_id':id})
            else:
                all_products.append({'banner_id':id})
        return all_products
            # all_products = self.product_list()
            # products_for_banner = []
            # after_no = round(len(all_products)/len(self.banner_ids))
            # products_rows = [x for x in range(0,len(all_products))]
            # no=0
            # for row in products_rows:
            #     if len(products_for_banner)==len(self.banner_ids):
            #         pass
            #     else:
            #         if row==0:
            #             products_for_banner.append(0)
            #         else:
            #             no=no+after_no
            #             if no in products_rows:
            #                 products_for_banner.append(no)
            # return products_for_banner
