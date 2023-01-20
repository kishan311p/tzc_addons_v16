from odoo import fields, models, api, _
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Border, Font, Side, Alignment, Protection
import base64
from io import BytesIO
import os
import shutil
import openpyxl
from odoo.exceptions import UserError
import pandas as pd
from datetime import datetime


class product_info_wizard_spt(models.TransientModel):
    _name = 'product.info.wizard.spt'
    _description = 'Product Excel Report Export'

    brand_ids = fields.Many2many('product.brand.spt', 'product_info_wizar_product_brand_spt_rel',
                                 'print_wizard_sale_order_excel_id', 'product_brand_id', 'Brand')
    category_ids = fields.Many2many('product.category', 'product_info_wizar_product_category_rel',
                                    'product_info_wizar_id', 'product_category_id', 'Category')
    model_ids = fields.Many2many('product.model.spt', 'product_info_wizar_product_model_rel',
                                 'product_info_wizar_id', 'product_model_id', 'Model')
    start_quantity = fields.Integer("From",default=-20000000)
    end_quantity = fields.Integer("To",default=20000000)
    not_set_image = fields.Boolean('Products Without Image',help="If selected, Report will have products with images not set.")
    consignment_products = fields.Boolean("Consignment Below Minimum Level")
    file = fields.Binary('File')
    temporary_out_of_stock = fields.Selection([('all','All'),('in_stock', 'In Stock'),('out_of_stock', 'Temporary Out Of Stock'),],default='all', string='Temporary Out Of Stock')
    is_published = fields.Boolean('Published')
    sku = fields.Text('SKU')
    # added
    barcode = fields.Char("Barcode")
    color_code = fields.Char("Color Code")
    color_ids = fields.Many2many("product.color.spt",'search_product_info_wizard_spt_product_color_spt_rel','search_product_info_wizard_id','product_color_spt_id','Color')
    material_ids = fields.Many2many("product.material.spt",'search_product_info_wizard_spt_product_material_spt_rel','search_product_info_wizard_id','product_material_id','Material')
    rim_type_ids = fields.Many2many("product.rim.type.spt",'search_product_info_wizard_spt_product_rim_type_spt_rel','search_product_info_wizadrd_id','product_rim_type_spt_id','Rim Type')
    shape_ids = fields.Many2many("product.shape.spt",'search_product_info_wizard_spt_product_shape_spt_rel','search_product_info_wizard_id','product_shape_spt_id','Shape')
    start_price = fields.Integer(default=-5000000)
    end_price = fields.Integer(default=5000000)
    eye_size_start = fields.Integer(default=-1000000)
    eye_size_end = fields.Integer(default=1000000)
    bridge_size_start = fields.Integer(default=-1000000)
    bridge_size_end = fields.Integer(default=1000000)
    temple_size_start = fields.Integer(default=-1000000)
    temple_size_end = fields.Integer(default=1000000)

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')

    in_future_archive = fields.Boolean('Future Archive')

    product_flex_hinges = fields.Selection([('yes','Yes'),('no','No'),('all','All'),],default='all',string=' Flex Hinges')

    def action_sale_print_filtered_report(self):
        self.check_range_values()

        params=["where pp.active = 'True' "]
        if self.not_set_image:
            q_image = """pp.is_image_missing"""
            params.append(f" and {q_image}")
        if self.category_ids:
            q_categ = f"pp.categ_id in ({str(','.join(self.category_ids.mapped(lambda x : str(x.id))))})"
            params.append(f" and {str(q_categ)}")
        if self.brand_ids:
            q_brand = f"pp.brand in ({str(','.join(self.brand_ids.mapped(lambda x: str(x.id))))})"
            params.append(f" and {str(q_brand)}")
        if self.model_ids:
            q_model = f"pp.model in ({str(','.join(self.model_ids.mapped(lambda x: str(x.id))))})"
            params.append(f" and {str(q_model)}")
        
        if self.temporary_out_of_stock == 'out_of_stock':
            params.append(f"and pp.temporary_out_of_stock = 'True'")
        elif self.temporary_out_of_stock == 'in_stock':
            params.append(f"and pp.temporary_out_of_stock  is Not TRUE")

        if self.is_published:
            params.append('and pp.is_published_spt = true')
        
        if self.sku:
            sku_s = [each.strip() for each in self.sku.split(',') if each.strip()]
            if len(sku_s):
                params.append(' and pp.default_code in %s'%(str(sku_s).replace('[','(').replace(']',')')))
        
        if self.barcode:
            barcodes = [barcode.strip() for barcode in self.barcode.split(',') if barcode.strip()]
            if len(barcodes):
                params.append(' and pp.barcode in %s'%(str(barcodes).replace('[','(').replace(']',')')))
        
        if self.color_code:
            color_codes = [color_code.strip() for color_code in self.color_code.split(',') if color_code.strip()]
            if len(color_codes):
                params.append(' and pp.manufacture_color_code in %s'%(str(color_codes).replace('[','(').replace(']',')')))
        
        if self.color_ids:
            params.append(' and pp.product_color_name in %s'%(str(self.color_ids.ids).replace('[','(').replace(']',')')))
        
        if self.material_ids:
            params.append(' and material_real.material_id in %s'%(str(self.material_ids.ids).replace('[','(').replace(']',')')))
        
        if self.rim_type_ids:
            params.append(' and pp.rim_type in %s'%(str(self.rim_type_ids.ids).replace('[','(').replace(']',')')))
        
        if self.shape_ids:
            params.append(' and shape_real.shape_id in %s'%(str(self.shape_ids.ids).replace('[','(').replace(']',')')))
        
        if self.in_future_archive:
            params.append(' and pp.in_future_archive = true')
        
        date_domain = []
        if self.start_date:
            start_date = datetime.combine(self.start_date, datetime.min.time())
            products = self.env['sale.order'].search([('date_order','>=',start_date)]).mapped('order_line').mapped('product_id')
            date_domain.extend(products.ids)
        
        if self.end_date:
            end_date = datetime.combine(self.end_date, datetime.min.time())
            products = self.env['sale.order'].search([('date_order','<=',start_date)]).mapped('order_line').mapped('product_id')
            date_domain.extend(products.ids)
        if (self.start_date or self.end_date) and not date_domain:
            params.append(' and pp.id is NULL')
        if date_domain:
            params.append(' and pp.id in %s'%(str(date_domain).replace('[','(').replace(']',')')))

        eye_filtere_list=[]
        check_eye_null = 'pp.eye_size_compute is NULL'
        if self.eye_size_start:
            eye_filtere_list.insert(0,'pp.eye_size_compute >= %s'%(self.eye_size_start))
        if self.eye_size_end:
            eye_filtere_list.insert(1 if len(eye_filtere_list) else 0,'pp.eye_size_compute <= %s'%(self.eye_size_end))
        if 0 in range(self.eye_size_start,self.eye_size_end+1):
            eye_filtere_list.append(check_eye_null)
        if len(eye_filtere_list):
            null_line = eye_filtere_list.pop(-1) if check_eye_null in eye_filtere_list else False
            range_filter = '(%s)'%(' and '.join(eye_filtere_list))
            null_filter = '%s'%(' or {}'.format(null_line) if null_line and eye_filtere_list else '')
            params.append(' and (%s)'%('%s%s'%(range_filter if eye_filtere_list else '',null_filter))) if eye_filtere_list or null_filter else None
        
        bridge_filtere_list=[]
        check_bridge_null = 'pp.bridge_size_compute is NULL'
        if self.bridge_size_start:
            bridge_filtere_list.insert(0,'pp.bridge_size_compute >= %s'%(self.bridge_size_start))
        if self.bridge_size_end:
            bridge_filtere_list.insert(1 if len(bridge_filtere_list) else 0,'pp.bridge_size_compute <= %s'%(self.bridge_size_end))
        if 0 in range(self.bridge_size_start,self.bridge_size_end+1):
            bridge_filtere_list.append(check_bridge_null)
        if len(bridge_filtere_list):
            null_line = bridge_filtere_list.pop(-1) if check_bridge_null in bridge_filtere_list else False
            range_filter = '(%s)'%(' and '.join(bridge_filtere_list))
            null_filter = '%s'%(' or {}'.format(null_line) if null_line and bridge_filtere_list else '')
            params.append(' and (%s)'%('%s%s'%(range_filter if bridge_filtere_list else '',null_filter))) if bridge_filtere_list or null_filter else None

        temple_filtere_list=[]
        check_temple_null = 'pp.temple_size_compute is NULL'
        if self.temple_size_start:
            temple_filtere_list.insert(0,'pp.temple_size_compute >= %s'%(self.temple_size_start))
        if self.temple_size_end:
            temple_filtere_list.insert(1 if len(temple_filtere_list) else 0,'pp.temple_size_compute <= %s'%(self.temple_size_end))
        if 0 in range(self.temple_size_start,self.temple_size_end+1):
            temple_filtere_list.append(check_temple_null)
        if len(temple_filtere_list):
            null_line = temple_filtere_list.pop(-1) if check_temple_null in temple_filtere_list else False
            range_filter = '(%s)'%(' and '.join(temple_filtere_list))
            null_filter = '%s'%(' or {}'.format(null_line) if null_line and temple_filtere_list else '')
            params.append(' and (%s)'%('%s%s'%(range_filter if temple_filtere_list else '',null_filter))) if temple_filtere_list or null_filter else None
            
        if self.temporary_out_of_stock == 'in_stock':
            params.append(' and pp.temporary_out_of_stock = true')
        if self.temporary_out_of_stock == 'out_of_stock':
            params.append(' and pp.temporary_out_of_stock = false')

        if self.product_flex_hinges == 'yes':
            params.append(f" and pp.flex_hinges = 'yes'")
        elif self.product_flex_hinges == 'no':
            params.append(f" and pp.flex_hinges = 'no'")

        available_qty_spt_filtere_list=[]
        check_available_qty_spt_null = 'pp.available_qty_spt is NULL'
        if self.start_quantity:
            available_qty_spt_filtere_list.insert(0,'pp.available_qty_spt >= %s'%(self.start_quantity))
        if self.end_quantity:
            available_qty_spt_filtere_list.insert(1 if len(available_qty_spt_filtere_list) else 0,'pp.available_qty_spt <= %s'%(self.end_quantity))
        if 0 in range(self.start_quantity,self.end_quantity+1):
            available_qty_spt_filtere_list.append(check_available_qty_spt_null)
        if len(available_qty_spt_filtere_list):
            null_line = available_qty_spt_filtere_list.pop(-1) if check_available_qty_spt_null in available_qty_spt_filtere_list else False
            range_filter = '(%s)'%(' and '.join(available_qty_spt_filtere_list))
            null_filter = '%s'%(' or {}'.format(null_line) if null_line and available_qty_spt_filtere_list else '')
            params.append(' and (%s)'%('%s%s'%(range_filter if available_qty_spt_filtere_list else '',null_filter))) if available_qty_spt_filtere_list or null_filter else None


        lst_price_usd_filtere_list=[]
        check_lst_price_usd_null = 'pp.lst_price_usd is NULL'
        if self.start_price:
            lst_price_usd_filtere_list.insert(0,'pp.lst_price_usd >= %s'%(self.start_price))
        if self.end_price:
            lst_price_usd_filtere_list.insert(1 if len(lst_price_usd_filtere_list) else 0,'pp.lst_price_usd <= %s'%(self.end_price))
        if 0 in range(self.start_price,self.end_price+1):
            lst_price_usd_filtere_list.append(check_lst_price_usd_null)
        if len(lst_price_usd_filtere_list):
            null_line = lst_price_usd_filtere_list.pop(-1) if check_lst_price_usd_null in lst_price_usd_filtere_list else False
            range_filter = '(%s)'%(' and '.join(lst_price_usd_filtere_list))
            null_filter = '%s'%(' or {}'.format(null_line) if null_line and lst_price_usd_filtere_list else '')
            params.append(' and (%s)'%('%s%s'%(range_filter if lst_price_usd_filtere_list else '',null_filter))) if lst_price_usd_filtere_list or null_filter else None
        
        if self.consignment_products:
            params.append(' and (pp.available_qty_spt < pp.minimum_qty)')

        query = f"""select
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
            COALESCE ((select sum(sml.qty_done) from stock_move_line sml
            left join stock_move sm on sml.move_id=sm.id
            left join sale_order_line sol on sm.sale_line_id=sol.id
            left join sale_order so on sol.order_id=so.id
            where sol.product_id = pp.id and so.state not in ('draft','sent','cancel')),0) as "Total Order Qty",
            COALESCE ((select sum(aml.quantity) from account_move_line aml left join account_move am on aml.move_id=am.id where aml.product_id = pp.id and am.state='posted'),0) as "Total Invoice Qty",
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
			(select count(inv.id) from account_move_line aml
			left join account_move inv on aml.move_id = inv.id
			where aml.product_id = pp.id and inv.state not in ('cancel')) as "#Invoice",
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
            {''.join(params)} order by pp.default_code;"""
        print('\n')
        print(query)
        print('\n')
        self.env.cr.execute(query)
        product_ids = self._cr.fetchall()
        columns = [desc[0] for desc in self.env.cr.description]
        df = pd.DataFrame(product_ids,columns=columns)
        writer = pd.ExcelWriter('/tmp/Prodcts_Export.xlsx')
        df.to_excel(writer,index=False,sheet_name="Products")
        writer.save()
        message=  f"From {self.env['product.product'].search_count([('active','=',True)])} products {product_ids.__len__()} products are exported."
        context = {"default_message":message}
        if self._context.get('image_report'):
            context.update({'image':True,'data':product_ids})
        return {
            "name": _("Exported Products"),
            "type":"ir.actions.act_window",
            "res_model":"warning.spt.wizard",
            "view_mode":"form",
            "view_id":self.env.ref('tzc_sales_customization_spt.warning_wizard_spt_form_view').id,
            "context":context,
            'target':"new",
        }

    def product_export_report_with_image(self):
        if self._context.get('with_image'):
            return self.with_context(image_report=True).action_sale_print_filtered_report()

    def check_range_values(self):
        self.ensure_one()
        messages=[]
        if self.start_date and self.end_date and self.end_date < self.start_date:
            messages.append('Given date range is invalid!\nPlease check the date range.')
        if self.start_price and self.end_price and self.end_price < self.start_price:
            messages.append("'To' Price must be greater than 'From' Price")
        if self.bridge_size_start and self.bridge_size_end and self.bridge_size_start > self.bridge_size_end:
            messages.append("'To' Bridge Size must be greater than  'From' Bridge Size.")
        if self.eye_size_start and self.eye_size_end and self.eye_size_start > self.eye_size_end:
            messages.append("'To' Eye Size must be greater than 'From' Eye Size.")
        if self.temple_size_start and self.temple_size_end and self.temple_size_start > self.temple_size_end:
            messages.append("'To' Temple Size must be greater than 'From' Temple Size.")
        if self.start_quantity and self.end_quantity and self.start_quantity > self.end_quantity:
            messages.append("'From' Quantity can not be higher than 'To' Quantity.")

        if len(messages) >= 1:
            raise UserError('\n'.join(messages))

    def action_process(self):
        domain=[]
        self.check_range_values()
        if self.category_ids:
            domain.append(('categ_id','in',self.category_ids.ids))
        if self.brand_ids:
            domain.append(("brand",'in',self.brand_ids.ids))
        if self.model_ids:
            domain.append(("model",'in',self.model_ids.ids))
        if self.color_code:
            domain.append(("color.color",'=',self.color_code))
        if self.color_ids:
            domain.append(("color",'in',self.color_ids.ids))
        if self.material_ids:
            domain.append(("material",'in',self.material_ids.ids))
        if self.rim_type_ids:
            domain.append(("rim_type","in",self.rim_type_ids.ids))
        if self.shape_ids:
            domain.append(("shape","in",self.shape_ids.ids))
        
        # price filter
        price_filter_list = []
        null_price = ('lst_price_usd','in',(False,0))
        if self.start_price:
            price_filter_list.append(("lst_price_usd",">=",self.start_price))
        if self.end_price:
            price_filter_list.append(("lst_price_usd",'<=',self.end_price))
        if 0 in range(self.start_price,self.end_price):
            price_filter_list.append(null_price)
        if len(price_filter_list):
            if null_price in price_filter_list:
                price_filter_list.remove(null_price)
                if len(price_filter_list):
                    domain.append('|')
                domain.append(null_price)
                if len(price_filter_list):
                    if len(price_filter_list) == 2:
                        domain.append('&')
                        domain.append(price_filter_list[0])
                        domain.append(price_filter_list[1])
                    else:
                        domain.append(price_filter_list[0])
            else:
                [domain.append(d) for d in price_filter_list if d not in domain]
        
        # eye size filter
        eye_size_filter = []
        null_eye_size = ("eye_size_compute",'in',(False,0))
        if self.eye_size_start:
            eye_size_filter.append(("eye_size_compute",">=",self.eye_size_start))
        if self.eye_size_end:
            eye_size_filter.append(("eye_size_compute","<=",self.eye_size_end))
        if 0 in range(self.temple_size_start,self.temple_size_end+1):
            eye_size_filter.append(null_eye_size)
        if eye_size_filter:
            # add in domain
            if null_eye_size in eye_size_filter:
                eye_size_filter.remove(null_eye_size)
                domain.append('|')
                domain.append(null_eye_size)
                if len(eye_size_filter):
                    domain.append('&')
                    domain.append(eye_size_filter[0])
                    domain.append(eye_size_filter[1])
                else:
                    domain.append(eye_size_filter[0])
            else:
                [domain.append(d) for d in eye_size_filter if d not in domain]
        
        # bridge size filter
        bridge_filter_list = []
        null_bridge_size_start = ("bridge_size_compute",'in',(False,0))
        if self.bridge_size_start:
            bridge_filter_list.append(("bridge_size_compute",">=",self.bridge_size_start))
        if self.bridge_size_end:
            bridge_filter_list.append(("bridge_size_compute","<=",self.bridge_size_end))
        if 0 in range(self.temple_size_start,self.temple_size_end+1):
            bridge_filter_list.append(null_bridge_size_start)
        if bridge_filter_list:
            # add in domain
            if null_bridge_size_start in  bridge_filter_list:
                bridge_filter_list.remove(null_bridge_size_start)
                domain.append('|')
                domain.append(null_bridge_size_start)
                if len(bridge_filter_list):
                    if len(bridge_filter_list) == 2:
                        domain.append('&')
                        domain.append(bridge_filter_list[0])
                        domain.append(bridge_filter_list[1])
                    else:
                        domain.append(bridge_filter_list[0])
            else:
                [domain.append(d) for d in bridge_filter_list if d not in domain]
        
        # temple size filter
        temple_size_list = []
        null_Temple = ("temple_size_compute",'in',(False,0))
        if self.temple_size_start:
            temple_size_list.append(("temple_size_compute",'>=',self.temple_size_start))
        if self.temple_size_end:
            temple_size_list.append(("temple_size_compute",'<=',self.temple_size_end))
        if 0 in range(self.temple_size_start,self.temple_size_end+1):
            temple_size_list.append(null_Temple)
        if temple_size_list:
            # add in domain
            if null_Temple in  temple_size_list:
                temple_size_list.remove(null_Temple)
                domain.append('|')
                domain.append(null_Temple)
                if len(temple_size_list):
                    if len(temple_size_list) == 2:
                        domain.append('&')
                        domain.append(temple_size_list[0])
                        domain.append(temple_size_list[1])
                    else:
                        domain.append(temple_size_list[0])
            else:
                [domain.append(d) for d in temple_size_list if d not in domain]
        
        # temporary out of stock
        if self.temporary_out_of_stock == 'in_stock':
                domain.append(("temporary_out_of_stock",'=',False))        
        if self.temporary_out_of_stock == 'out_of_stock':
                domain.append(("temporary_out_of_stock",'=',True))
        if self.is_published:
            domain.append(('is_published_spt','=',True))
        
        # Qty filter
        quantity_filtere_list = []
        null_Temple = ("available_qty_spt",'in',(False,0))
        if self.start_quantity:
            quantity_filtere_list.append(("available_qty_spt",'>=',self.start_quantity))
        if self.end_quantity:
            quantity_filtere_list.append(("available_qty_spt",'<=',self.end_quantity))
        if 0 in range(self.start_quantity,self.end_quantity+1):
            quantity_filtere_list.append(null_Temple)
        if quantity_filtere_list:
            # add in domain
            if null_Temple in quantity_filtere_list:
                quantity_filtere_list.remove(null_Temple)
                domain.append('|')
                domain.append(null_Temple)
                if len(quantity_filtere_list):
                    if len(quantity_filtere_list) == 2:
                        domain.append('&')
                        domain.append(quantity_filtere_list[0])
                        domain.append(quantity_filtere_list[1])
                    else:
                        domain.append(quantity_filtere_list[0])
            else:
                [domain.append(d) for d in quantity_filtere_list if d not in domain]
        
        if self.sku:
            split_ = [each.strip() for each in self.sku.split(',') if each.strip()]
            if len(split_):
                domain.append(('default_code','in',split_))
        
        # date range products of orders
        date_domain = []
        if self.start_date:
            date_domain.append(('date_order','>=',self.start_date))
        if self.end_date:
            date_domain.append(('date_order','<=',self.end_date))
        if date_domain:
            date_domain.append(('state','not in',('draft','recieved','cancel')))
            order_lines = self.env['sale.order'].search(date_domain)
            domain.append('|')
            domain.append(('id','in',order_lines.mapped('order_line').mapped('product_id').ids)) if order_lines else None
        
        if self.not_set_image:
            domain.extend([('is_image_missing','=',True)])
            # domain.extend(['|',('image_variant_1920','=',False),('image_secondary','=',False)])
        if self.in_future_archive:
            domain.append(('in_future_archive','=',True))

        product_ids = self.env['product.product'].search(domain)
        if product_ids:
            return {
                "name":_("Product Variants"),
                "type":"ir.actions.act_window",
                "res_model":"product.product",
                "view_mode":"tree,form,activity",
                "domain":[("id","in",product_ids.ids)],
                "target":"current"
            }
        else:
            raise UserError(_('product not found.'))
