from odoo import _, api, fields, models
from datetime import datetime

class sale_catalog(models.Model):
    _inherit = 'sale.catalog'
    
    def catalog_reject_mail(self,partner_id,message) :
        self.ensure_one()
        self.env.ref('tzc_sales_customization_spt.kits_mail_reject_catalog_to_sales_person').with_context(message=message,customer=partner_id,signature=self.user_id.signature).send_mail(self.id, force_send=True,email_layout_xmlid="mail.mail_notification_light")
        return {}

    def catalog_email(self,partner_id):
        for record in self:
            so_id  = self.env['sale.order'].search([('partner_id','=',partner_id),('catalog_id','=',record.id)])
            verified = so_id.partner_verification()
            quotation_template_id = self.env.ref('tzc_sales_customization_spt.tzc_email_template_catalog_quotation_spt') if verified else None
            url = ''
            pdf_links = self.env['ir.model'].sudo().generate_report_access_link(
                'sale.catalog',
                record.id,
                'sale.action_report_saleorder',
                partner_id,
                'pdf'
            )
            if pdf_links.get('success') and pdf_links.get('url'):
                url = pdf_links.get('url')  
            quotation_template_id.with_context(pdf_url=url,signature=self.user_id.signature).send_mail(so_id.id,force_send=True) if verified else None
            confirmation_template_id = self.env.ref('tzc_sales_customization_spt.tzc_email_template_saleperson_quotation_spt')
            confirmation_template_id.with_context(pdf_url=url,signature=self.user_id.signature).send_mail(so_id.id,email_values={'email_to': so_id.user_id.partner_id.email},force_send=True)
        return {}

    def line_ordering_by_product(self):
        is_geo_restriction = self.env['kits.b2b.website'].search([('website_name','=','b2b1')],limit = 1).is_allow_for_geo_restriction
        product_list = []
        for line in self.line_ids:
            if is_geo_restriction :
                if line.catalog_id.customer_id.country_id.id not in line.product_pro_id.geo_restriction.ids:
                    product_name = line.product_pro_id.name_get()[0][1].strip()
                    product_list.append(product_name)
            else :
                product_name = line.product_pro_id.name_get()[0][1].strip()
                product_list.append(product_name)
        product_list = list(filter(None, product_list))
        product_list = list(set(product_list))
        product_list.sort()
        return product_list

    def line_product_dict(self,product_name):
        is_geo_restriction = self.env['kits.b2b.website'].search([('website_name','=','b2b1')],limit = 1).is_allow_for_geo_restriction
        product_dict = {}
        if self.accept_decline_flag:
            self.accept_decline_flag = False
            self.line_ids = self.line_ids.filtered(lambda x:x.product_qty != 0)
            
        for line in self.line_ids:
            line_dict = {} 
            product_name = line.product_pro_id.name_get()[0][1].strip()
            if is_geo_restriction : 
                if line.catalog_id.customer_id.country_id.id not in line.product_pro_id.geo_restriction.ids:
                    if line.catalog_id.customer_id.country_id.id not in line.product_pro_id.geo_restriction.ids:
                        if line.product_pro_id.name in product_dict.keys():
                            product_dict[product_name]['line_ids'].append(line) 
                        else:
                            line_dict['line_ids'] = [line]
                            product_dict[product_name] = line_dict
            else:
                if line.product_pro_id.name in product_dict.keys():
                            product_dict[product_name]['line_ids'].append(line) 
                else:
                    line_dict['line_ids'] = [line]
                    product_dict[product_name] = line_dict
        return product_dict

    def get_catalog_line(self):
        product_obj = self.env['product.product']
        order_line_obj = self.env['sale.order.line']
        catalog_line_obj = self.env['sale.catalog.line']
        is_geo_restriction = self.env['kits.b2b.website'].search([('website_name','=','b2b1')],limit = 1).is_allow_for_geo_restriction
        order_id = self.env['sale.order'].search([('catalog_id','=',self.id),('partner_id','=',self.customer_id.id)],order = 'id desc',limit = 1)
        if order_id:
            b2b_currency_id = self.env['kits.b2b.multi.currency.mapping'].search([('currency_id','=',order_id.b2b_currency_id.id)])
            if b2b_currency_id.currency_id.id != self.customer_id.preferred_currency.id:
                b2b_currency_id = self.env['kits.b2b.multi.currency.mapping'].search([('currency_id','=',self.customer_id.preferred_currency.id)])
            rate = b2b_currency_id.currency_rate or 1.0
            line_ids = order_line_obj.search([('order_id','=',order_id.id)])
            product_list = set(line_ids.mapped('product_id.variant_name'))
        else:
            self._onchange_pricelist_id()
            rate = self.env['kits.b2b.multi.currency.mapping'].search([('currency_id','=',self.customer_id.preferred_currency.id)]).currency_rate or 1.0
            line_ids = self.line_ids
            product_list = set(line_ids.mapped('product_pro_id.variant_name'))
            
        product_list = list(product_list)
        product_list.sort()
        product_dict = {}
        for product_name in product_list:
            product_id = product_obj.search([('active','=',True),('variant_name','=',product_name)],order = 'id desc',limit=1)
            if is_geo_restriction and self.customer_id.country_id.id in product_id.geo_restriction.ids:
                continue
            line_dict = {'product_id' : product_id,'qty': 0}
            if order_id:
                line_ids = order_line_obj.search([('order_id','=',order_id.id),('product_id','=',product_id.id)])
                for line in line_ids:
                    if line_dict.get('price_unit',False):
                        line_dict['price_unit'] = (line_dict.get('price_unit',0) + line.price_unit)/2
                        line_dict['our_price'] =( line_dict.get('our_price',0) + line.unit_discount_price)/2
                        line_dict['qty'] = int(line_dict.get('qty',0) + line.product_qty)
                    else:    
                        line_dict['price_unit'] = line.price_unit
                        line_dict['our_price'] = line.unit_discount_price
                        line_dict['qty'] = int(line.product_qty)
                    if line.is_special_discount:
                        line_dict['is_special_discount'] = True
            else: 
                line_ids = catalog_line_obj.search([('catalog_id','=',self.id),('product_pro_id','=',product_id.id)])
                for line in line_ids:
                    if line_dict.get('price_unit',False):
                        line_dict['price_unit'] = (line_dict.get('price_unit',0) + line.price_unit)/2
                        line_dict['our_price'] =( line_dict.get('our_price',0) + line.unit_discount_price)/2
                        line_dict['qty'] = int(line_dict.get('qty',0) + line.product_qty)
                    else:    
                        line_dict['price_unit'] = line.product_price
                        line_dict['our_price'] = line.unit_discount_price
                        line_dict['qty'] = line.product_qty 
                    if line.is_special_discount:
                        line_dict['is_special_discount'] = True   
            line_dict['price_unit'] = round(line_dict.get('price_unit',0)* rate,2)
            line_dict['our_price'] = round(line_dict.get('our_price',0),2)    
            line_dict['sub_total'] = round(line_dict.get('our_price',0) * line_dict.get('qty',0),2)        
            product_dict [product_name] = line_dict
        return product_dict

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id(self):
        pricelist_obj = self.env['product.pricelist.item']
        for record in self:
           for line in record.line_ids:
                product_price  =  pricelist_obj.search([('pricelist_id','=',self.env['kits.b2b.website'].search([('website_name','=','b2b1')],limit = 1).pricelist_id.id),('product_id','=',line.product_pro_id.id)],limit=1).fixed_price
                pricelist_item_id = pricelist_obj.search([('product_id','=',line.product_pro_id.id),('pricelist_id','=',record.pricelist_id.id)],limit=1)
                line.product_price = product_price
                line.product_price_msrp = line.product_pro_id.price_msrp
                line.product_price_wholesale = line.product_pro_id.price_wholesale
                line.unit_discount_price = pricelist_item_id.fixed_price
                if line.sale_type:
                    if line.sale_type == 'on_sale':
                        line.unit_discount_price = line.product_pro_id.on_sale_usd
                    else:
                        line.unit_discount_price = line.product_pro_id.clearance_usd

                if line.discount:
                    line.unit_discount_price = line.product_price - (line.product_price * line.discount) * 0.01
                
                if not record.pricelist_id.is_pricelist_excluded:
                    active_inflation = self.env['kits.inflation'].search([('is_active','=',True)])
                    inflation_rule_ids = self.env['kits.inflation.rule'].search([('country_id','in',self.env.user.country_id.ids),('brand_ids','in',line.product_pro_id.brand.ids),('inflation_id','=',active_inflation.id)])
                    inflation_rule = inflation_rule_ids[-1] if inflation_rule_ids else False
                    if inflation_rule:
                        is_inflation = False
                        if active_inflation.from_date and active_inflation.to_date :
                            if active_inflation.from_date <= datetime.now().date() and active_inflation.to_date >= datetime.now().date():
                                is_inflation = True
                        elif active_inflation.from_date:
                            if active_inflation.from_date <= datetime.now().date():
                                is_inflation = True
                        elif active_inflation.to_date:
                            if active_inflation.to_date >= datetime.now().date():
                                is_inflation = True
                        else:
                            if not active_inflation.from_date:
                                is_inflation = True
                            if not active_inflation.to_date:
                                is_inflation = True
                            
                        if is_inflation:
                            line.product_price = round(product_price+(product_price*inflation_rule.inflation_rate /100),2)
                            line.unit_discount_price = round(line.unit_discount_price+(line.unit_discount_price*inflation_rule.inflation_rate /100),2)
                            line.product_price_msrp = round(line.product_price_msrp+(line.product_price_msrp*inflation_rule.inflation_rate /100),2)
                            line.product_price_wholesale = round(line.product_price_wholesale+(line.product_price_wholesale*inflation_rule.inflation_rate /100),2)

                    active_fest_id = self.env['tzc.fest.discount'].search([('is_active','=',True)])
                    special_disocunt_id = self.env['kits.special.discount'].search([('country_id','in',self.env.user.partner_id.country_id.ids),('brand_ids','in',line.product_pro_id.brand.ids),('tzc_fest_id','=',active_fest_id.id)])
                    price_rule_id = special_disocunt_id[-1] if special_disocunt_id else False
                    if price_rule_id:
                        applicable = False
                        if active_fest_id.from_date and active_fest_id.to_date :
                            if active_fest_id.from_date <= datetime.now().date() and active_fest_id.to_date >= datetime.now().date():
                                applicable = True
                        elif active_fest_id.from_date:
                            if active_fest_id.from_date <= datetime.now().date():
                                applicable = True
                        elif active_fest_id.to_date:
                            if active_fest_id.to_date >= datetime.now().date():
                                applicable = True
                        else:
                            if not active_fest_id.from_date:
                                applicable = True
                            if not active_fest_id.to_date:
                                applicable = True
                            
                        if applicable:
                            line.unit_discount_price = round((line.unit_discount_price - line.unit_discount_price * price_rule_id.discount / 100),2)
                            line.is_special_discount = True
                            line.product_price_msrp = round(line.product_price_msrp-(line.product_price_msrp*price_rule_id.discount /100),2)
                            line.product_price_wholesale = round(line.product_price_wholesale-(line.product_price_wholesale*price_rule_id.discount /100),2)

                line._compute_amount()
