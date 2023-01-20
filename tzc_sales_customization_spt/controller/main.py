from odoo.http import request
from odoo import http,_
from werkzeug.exceptions import NotFound
import logging
import werkzeug
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db, Home
from odoo.addons.base_setup.controllers.main import BaseSetup
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


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
