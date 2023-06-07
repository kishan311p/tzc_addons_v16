from odoo.http import request
from odoo import http,_
from werkzeug.exceptions import NotFound
import logging
import werkzeug
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.addons.base_setup.controllers.main import BaseSetup
from odoo.exceptions import UserError
from odoo.addons.web.controllers.main import ReportController
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.addons.account.controllers.portal import PortalAccount
from odoo.addons.website_sale_digital.controllers.main import WebsiteSaleDigital
from odoo.addons.sale.controllers.portal import CustomerPortal as SaleCustomerPortal
import datetime
import json

_logger = logging.getLogger(__name__)

class kitsCustomerPortal(http.Controller):
    @http.route(['/my/home'], type='http', auth="user", website=True)
    def home(self, **kw):
        # values = self._prepare_portal_layout_values()
        return request.render("http_routing.404")
    
    @http.route(['/my/account'], type='http', auth='user', website=True)
    def account(self, redirect=None, **post):
        return request.render("http_routing.404")

    @http.route('/my/security', type='http', auth='user', website=True, methods=['GET', 'POST'])
    def security(self, **post):
        return request.render("http_routing.404")
    
CustomerPortal.home = kitsCustomerPortal.home
CustomerPortal.account = kitsCustomerPortal.account
CustomerPortal.security = kitsCustomerPortal.security
CustomerPortal.home = kitsCustomerPortal.home

class kitsSaleCustomerPortal(CustomerPortal):
    
    @http.route(['/my/quotes/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_quotes(self, **kwargs):
        return request.render("http_routing.404")
    
    @http.route(['/my/orders/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_orders(self, **kwargs):
        return request.render("http_routing.404")

    @http.route(['/my/orders/<int:order_id>'], type='http', auth="public", website=True)
    def portal_order_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
        return request.render("http_routing.404")

    @http.route(['/my/orders/<int:order_id>/accept'], type='json', auth="public", website=True)
    def portal_quote_accept(self, order_id, access_token=None, name=None, signature=None):
        return request.render("http_routing.404")

    @http.route(['/my/orders/<int:order_id>/decline'], type='http', auth="public", methods=['POST'], website=True)
    def portal_quote_decline(self, order_id, access_token=None, decline_message=None, **kwargs):
        return request.render("http_routing.404")
    
SaleCustomerPortal.portal_my_quotes = kitsSaleCustomerPortal.portal_my_quotes
SaleCustomerPortal.portal_my_orders = kitsSaleCustomerPortal.portal_my_orders
SaleCustomerPortal.portal_order_page = kitsSaleCustomerPortal.portal_order_page
SaleCustomerPortal.portal_quote_accept = kitsSaleCustomerPortal.portal_quote_accept
SaleCustomerPortal.portal_quote_decline = kitsSaleCustomerPortal.portal_quote_decline

class kitsPortalAccount(CustomerPortal):

    @http.route(['/my/invoices', '/my/invoices/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_invoices(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None, **kw):
       return request.render("http_routing.404")
    
    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
       return request.render("http_routing.404")
    
PortalAccount.portal_my_invoices = kitsPortalAccount.portal_my_invoices
PortalAccount.portal_my_invoice_detail = kitsPortalAccount.portal_my_invoice_detail

class kits_ReportController(http.Controller):
    @http.route(['/bambora/approved','/bambora/declined'], type='http', auth='public', website=True, methods=['GET', 'POST'], csrf=False)
    def get_payment_status(self,**kw):
        payment_status = False
        order_number = False
        paid_amount = 0.0 
        amount = 0.0
        transaction_id = False

        for split_url in request.httprequest.url.split('&'):
            if split_url.split('=')[0] == 'trnOrderNumber':
                order_number = split_url.split('=')[1]
            elif split_url.split('=')[0] == 'trnAmount':
                paid_amount = split_url.split('=')[1]
                amount = split_url.split('=')[1] # for email template
            # elif split_url.split('=')[0] == 'trnDate':
            #     str_trn_date = split_url.split('=')[1]
            #     transaction_date = str_trn_date.replace("%2F",'/').replace("%3A",':').replace("+",' ')
            elif split_url.split('=')[0] == 'trnId':
                transaction_id = split_url.split('=')[1]
            elif '?' in split_url and 'trnApproved' in split_url.split('?')[1]:
                if split_url.split('?')[1].split('=')[1] == '1':
                    payment_status = 'approved'
                else:
                    payment_status = 'declined'

        order_id = request.env['sale.order'].sudo().search([('name','like',order_number)])
        # payment_obj = request.env['order.payment'].sudo()
        payment_obj = request.env['account.payment']
        # same_transaction_line_id = request.env['order.payment'].sudo().search([('transaction_id','=',transaction_id)])
        if order_number and payment_status:
            # status = 'approve' if payment_status == 'approved' else 'decliend'
            # if transaction_id and not same_transaction_line_id:
            # payment_obj.create({'order_id':order_id.id,'amount':float(paid_amount),'state':status,'mode_of_payment':'bambora','is_manual_paid':False,'transaction_id':transaction_id})
            pay_id = payment_obj.create({'name':order_id.name,
                                'partner_id':order_id.partner_id.id,
                                'sale_id':order_id.id,
                                'partner_type':'customer',
                                'payment_type':'inbound',
                                'journal_id':request.env.company.journal_id.id,
                                'currency_id':order_id.currency_id.id,
                                'amount':float(paid_amount),
                                'transaction_id':transaction_id,
                                'date':datetime.datetime.now().date()})
            pay_id.action_post()
            receive = pay_id.line_ids.filtered('credit')
            invoice_id = order_id.invoice_ids.filtered(lambda x:x.state == 'posted')
            if invoice_id:
                invoice_id.js_assign_outstanding_line(receive.id)
        if order_number and payment_status == 'approved':
            # if not same_transaction_line_id:
                if order_id and order_id.state not in ['draft','sent','recived']:
                    total_paid_amount = sum(payment_obj.sudo().search([('sale_id','=',order_id.id),('state','=','posted')]).mapped('amount'))
                    # total_paid_amount = sum(payment_obj.search([('order_id','=',order_id.id),('state','=','approve')]).mapped('amount'))
                    # paid_amount = paid_amount if not total_paid_amount else total_paid_amount
                    order_id.amount_paid = total_paid_amount
                    if order_id.picked_qty_order_total == float(paid_amount):
                        order_id.is_paid = True

                    order_id.payment_link = False

                    if total_paid_amount < order_id.picked_qty_order_total:
                        order_id.payment_status = 'partial'
                    elif total_paid_amount == order_id.picked_qty_order_total:
                        order_id.payment_status = 'full'
                    elif total_paid_amount > order_id.picked_qty_order_total:
                        order_id.payment_status = 'over'

                    template_id = request.env.ref('tzc_sales_customization_spt.mail_template_for_approve_payment')
                    template_id = template_id.with_context(signature = order_id.user_id.signature,order = order_id.name,date=datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),amount = order_id.currency_id.name + ' ' + order_id.currency_id.symbol + str(amount))
                    template_id.sudo().send_mail(order_id.id,force_send=True,email_layout_xmlid="mail.mail_notification_light")
                    # email_layout_xmlid

                if order_id and invoice_id and invoice_id.commission_line_ids:
                    if order_id.payment_status in ['full','over']:
                        invoice_id.commission_line_ids.write({'state':'paid'})
                    else:
                        invoice_id.commission_line_ids.write({'state':'draft'})
        else:
            template_id = request.env.ref('tzc_sales_customization_spt.mail_template_for_decline_payment')
            template_id = template_id.with_context(signature = order_id.user_id.signature,order = order_id.name,date=datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),amount = order_id.currency_id.name + ' ' + order_id.currency_id.symbol + str(amount))
            template_id.sudo().send_mail(order_id.id,force_send=True,email_layout_xmlid="mail.mail_notification_light")

        # transaction_date = datetime.datetime.now().strftime("%m/%d/%y %H:%M:%S %2p") + ' (UTC)'
        # values = {
        #     'order': order_id if order_id else False,
        #     'order_number':order_number if order_number else False,
        #     'paid_amount':round(float(paid_amount),2) if paid_amount else False,
        #     'transaction_date':transaction_date if transaction_date else False,
        #     'payment_status':payment_status if payment_status else False,
        #     'transaction_id':transaction_id if transaction_id else False,
        #     'trnurl':request.httprequest.url,
        # }
        # return request.render("tzc_website.thankyou_page",values)

class Website_brands(http.Controller):
    @http.route(['/product-export'], type="http", auth="public", website=True, sitemap=False)
    def export_products(self):
        excel_token = request.env.company.excel_token
        token = request.httprequest.args.get('token')
        if excel_token != token:
            raise NotFound()

        query = '''select
            pp.default_code as "SKU",
            pp.variant_name as "Name",
            pbs.name as "Brand",
            pms.name as "Model",
            pcc.name as "Manufacturing Color Code",
            pp.eye_size_compute as "Eye Size",
            pc.name as "Category",
            (pp.available_qty_spt+pp.reversed_qty_spt) as "Total Qty",
            pp.available_qty_spt as "Available Qty",
            pp.reversed_qty_spt as "Reserved Qty",
            pp.lst_price_usd as "Price",
            pp.barcode as "Barcode",
            pp.image_url as "Image",
            pp.image_secondary_url as "Image 2",
            (select case when pp.is_published_spt = True then 'Yes' else 'No' end) as "Is Published",
            (SELECT CASE WHEN pp.is_image_missing = True then 'false' else 'true' end) as "Image Set",
            pcs.name as "Color Name",
            (select name from product_color_spt where id = pp.secondary_color_name) as "Secondary Color Name",
            COALESCE (pp.temporary_out_of_stock,false)::varchar as "Temporary Out Of Stock",
            pp.manufacture_color_code as "Manufacturer Color Code",
            pbss.name as "Bridge Size",
            COALESCE (ptss.name,'')::varchar as "Temple Size",
            (select name from product_color_spt where id = pp.lense_color_name) as "Lence Color Name",
            prts.name as "Rim Type",
            shape.name as "Shape",
            material.name as "Material",
            pp.flex_hinges as "Flex Hinges",
            COALESCE (pp.weight,0.0)::float as "Weight",
            (select case when pp.gender = 'male' then 'M' when pp.gender = 'female' then 'F' when pp.gender = 'm/f' then 'M/F' else '' end ) as "Gender",
            pp.create_date::Date as "Create Date",
            pp.write_Date::Date as "Modify Date",
            case when country.name is NULL then 'N/A' else country.name->>'en_US' end as "Country of Origin",
            pp.order_not_invoice as "#Open Orders",
            (select count(oder.id) from sale_order_line sol 
                        left join sale_order oder on sol.order_id = oder.id
                        where sol.product_id = pp.id and oder.state not in ('cancel','merged')) as "#Order",
            (SELECT CASE WHEN pp.is_forcefully_unpublished = True then 'Yes' else 'No' end) as "Is Forcefully Unpublished"
        from product_product pp
            left join product_template pt on pp.product_tmpl_id = pt.id
            left join product_brand_spt pbs on pp.brand=pbs.id
            left join product_model_spt pms on pp.model=pms.id
            left join product_category pc on pp.categ_id=pc.id
            left join product_color_spt pcs on pp.product_color_name=pcs.id
            left join product_size_spt pss on pp.size=pss.id 
            left join product_bridge_size_spt pbss on pp.bridge_size = pbss.id
            left join product_temple_size_spt ptss on pp.temple_size = ptss.id
            left join product_rim_type_spt prts on pp.rim_type = prts.id
            FULL OUTER join product_with_material_real material_real on pp.id = material_real.product_id
            left join product_material_spt material on material_real.material_id = material.id
            FULL OUTER join product_with_shape_real shape_real on pp.id = shape_real.product_id
            left join product_shape_spt shape on shape_real.shape_id = shape.id 
            left join res_country country on pp.country_of_origin = country.id
            left join kits_product_color_code pcc on pp.color_code = pcc.id
            where pp.active = 'True' and (pt.is_shipping_product is not true and pt.is_admin is not true and pt.is_global_discount is not true) order by pp.default_code;'''
        request.env.cr.execute(query)
        data = {
            "list_of_files": request._cr.fetchall(),
        }
        return request.render("tzc_sales_customization_spt.template_export_product", data)

# class AuthSignupHome(Home):
#     def do_signup(self, qcontext):
#         res = super(AuthSignupHome,self).do_signup(qcontext)
#         if qcontext and 'login' in qcontext.keys():
#             user_id = request.env['res.users'].sudo().search([('login','=',qcontext['login'])],limit=1)
#             ip_address = request.httprequest.environ['REMOTE_ADDR']
#             if user_id:
#                 user_id.sudo().write({
#                    'signup_user_ip': str(ip_address),
#                 })
#         return res
