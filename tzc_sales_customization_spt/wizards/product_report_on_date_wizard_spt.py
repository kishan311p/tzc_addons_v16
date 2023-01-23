# -*- coding: utf-8 -*-
# Part of SnepTech See LICENSE file for full copyright and licensing details.##
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
import base64
from io import BytesIO
from odoo.tools import float_compare
from datetime import timedelta,datetime
from dateutil import tz
class product_report_on_date_wizard_spt(models.TransientModel):
    _name = 'product.report.on.date.wizard.spt'
    _description = 'Set QTY Available'
    
    start_date = fields.Date('Date')
    file = fields.Binary('File')
    exclude_zero_qty = fields.Boolean('Exclude Zero Qty')


    def action_print_report_file(self):
        move_line_obj = self.env['stock.move.line']
        self.ensure_one()
        # tz_from = current system timezone,
        # tz_to = User Setting's timezone
        tz_from, tz_to = tz.gettz(datetime.now().tzinfo), (tz.gettz(self.env.user.tz) or self.env.context.get('tz'))
        if self.start_date:
            start_date = datetime.combine(self.start_date, datetime.min.time()) +timedelta(seconds=-1,days=+1)
            start_date = start_date.replace(tzinfo=tz_from).astimezone(tz=tz_to)

        product_ids = self.env['product.product'].search([])
        active_id = self.id
        f_name = 'Product_on_hand'  # FileName
        workbook = Workbook()
        sheet = workbook.create_sheet(
            title="Product Update History", index=0)  # sheet name

        # sheet
        bd = Side(style='thin', color="000000")
        top_bottom_border = Border(top=bd, bottom=bd)
        bottom_border = Border(bottom=bd)
        table_header_font = Font(size=10, bold=True, name="Garamond")
        table_font = Font(size=10, bold=False, name="Garamond")
        alignment = Alignment(
            vertical='center', horizontal='center', text_rotation=0, wrap_text=True)
        left_alignment = Alignment(
            vertical='center', horizontal='left', text_rotation=0, wrap_text=True)
     

        # -------------------------------- Header --------------------------------
        sheet.merge_cells('A1:H3')
        sheet.cell(row=1,column=1).value = str('Inventory At '+str(self.start_date))
        sheet.cell(row=1,column=1).font = Font(size=14,bold=True,name="Garamond")
        sheet.cell(row=1,column=1).alignment = left_alignment
        
        # -------------------------------- Table  --------------------------------
        table_header_row = 5
        sheet.cell(row=table_header_row, column=1).value = 'NAME'
        sheet.cell(row=table_header_row, column=2).value = 'SKU'
        sheet.cell(row=table_header_row, column=3).value = 'Brand'
        sheet.cell(row=table_header_row, column=5).value = 'CATEGORY'
        sheet.cell(row=table_header_row, column=6).value = 'ON HAND QTY'
        sheet.cell(row=table_header_row, column=7).value = 'Price CAD'
        sheet.cell(row=table_header_row, column=8).value = 'Price USD'
        sheet.cell(row=table_header_row, column=4).value = 'Model'
        sheet.cell(row=table_header_row, column=1).font = table_header_font
        sheet.cell(row=table_header_row, column=2).font = table_header_font
        sheet.cell(row=table_header_row, column=3).font = table_header_font
        sheet.cell(row=table_header_row, column=4).font = table_header_font
        sheet.cell(row=table_header_row, column=5).font = table_header_font
        sheet.cell(row=table_header_row, column=6).font = table_header_font
        sheet.cell(row=table_header_row, column=7).font = table_header_font
        sheet.cell(row=table_header_row, column=8).font = table_header_font
        sheet.cell(row=table_header_row, column=1).alignment = left_alignment
        sheet.cell(row=table_header_row, column=2).alignment = left_alignment
        sheet.cell(row=table_header_row, column=3).alignment = left_alignment
        sheet.cell(row=table_header_row, column=4).alignment = left_alignment
        sheet.cell(row=table_header_row, column=5).alignment = alignment
        sheet.cell(row=table_header_row, column=6).alignment = alignment
        sheet.cell(row=table_header_row, column=7).alignment = alignment
        sheet.cell(row=table_header_row, column=8).alignment = alignment
        sheet.cell(row=table_header_row, column=1).border = top_bottom_border
        sheet.cell(row=table_header_row, column=2).border = top_bottom_border
        sheet.cell(row=table_header_row, column=3).border = top_bottom_border
        sheet.cell(row=table_header_row, column=4).border = top_bottom_border
        sheet.cell(row=table_header_row, column=5).border = top_bottom_border
        sheet.cell(row=table_header_row, column=6).border = top_bottom_border
        sheet.cell(row=table_header_row, column=7).border = top_bottom_border
        sheet.cell(row=table_header_row, column=8).border = top_bottom_border

        product_dict = {}
        for product_id in product_ids:
            qty = []
            line_ids  = move_line_obj.search([('product_id','=',product_id.id),('state','=','done'),('date','<=',start_date)])
            for line in line_ids:
                stock_operation = False
                if line.location_id.usage == 'inventory' and line.location_dest_id.usage == 'internal':
                    stock_operation = line.qty_done
                elif line.location_id.usage == 'internal' and line.location_dest_id.usage == 'inventory':
                    stock_operation = -line.qty_done
                elif line.location_id.usage == 'internal' and line.location_dest_id.usage == 'customer':
                    stock_operation = -line.qty_done
                elif line.location_id.usage == 'internal' and line.location_dest_id.usage == 'supplier':
                    stock_operation = line.qty_done
                
                elif line.location_id.usage == 'customer' and line.location_dest_id.usage == 'internal':
                    stock_operation = line.qty_done
                
                elif line.location_id.usage == 'customer' and line.location_dest_id.usage == 'inventory':
                    stock_operation = -line.qty_done

                else:
                    self

                if stock_operation:
                    qty.append(stock_operation)
            exclude_zero_qty = True
            if self.exclude_zero_qty and sum(qty) < 1:
                exclude_zero_qty = False
            if exclude_zero_qty:
                product_dict[product_id.name+str(product_id.id)] = {
                    'name': product_id.name_get()[0][1],
                    'categ': product_id.categ_id.name,
                    'qty': sum(qty) ,
                    'sku': product_id.default_code,
                    'brand': product_id.brand.name,
                    'model': product_id.model.name,
                    'lst_price': product_id.lst_price,
                    'lst_price_usd': product_id.lst_price_usd,
                    }

        row_index = table_header_row+1
        for record in sorted(product_dict):
            sheet.cell(row=row_index,
                       column=1).value = product_dict[record].get('name')
            sheet.cell(row=row_index, column=1).font = table_font
            sheet.cell(row=row_index, column=1).alignment = left_alignment
            sheet.cell(row=row_index,
                       column=2).value = product_dict[record].get('sku')
            sheet.cell(row=row_index, column=2).font = table_font
            sheet.cell(row=row_index, column=2).alignment = left_alignment
            sheet.cell(row=row_index,
                       column=3).value = product_dict[record].get('brand')
            sheet.cell(row=row_index, column=3).font = table_font
            sheet.cell(row=row_index,
                       column=5).value = product_dict[record].get('categ')
            sheet.cell(row=row_index, column=5).font = table_font
            sheet.cell(row=row_index,
                       column=6).value = product_dict[record].get('qty')
            sheet.cell(row=row_index, column=6).font = table_font

            sheet.cell(row=row_index,
                       column=7).value = product_dict[record].get('lst_price')
            sheet.cell(row=row_index, column=7).font = table_font

            sheet.cell(row=row_index,
                       column=8).value = product_dict[record].get('lst_price_usd')
            sheet.cell(row=row_index, column=8).font = table_font

            sheet.cell(row=row_index,
                       column=4).value = product_dict[record].get('model')
            sheet.cell(row=row_index, column=4).font = table_font

           
            sheet.cell(row=row_index, column=1).border = bottom_border
            sheet.cell(row=row_index, column=2).border = bottom_border
            sheet.cell(row=row_index, column=3).border = bottom_border
            sheet.cell(row=row_index, column=4).border = bottom_border
            sheet.cell(row=row_index, column=5).border = bottom_border
            sheet.cell(row=row_index, column=6).border = bottom_border
            sheet.cell(row=row_index, column=7).border = bottom_border
            sheet.cell(row=row_index, column=8).border = bottom_border
            row_index += 1
        # -------------------------------- table end --------------------------------

        sheet.column_dimensions['A'].width = 30  
        sheet.column_dimensions['B'].width = 18 
        sheet.column_dimensions['C'].width = 15 
        sheet.column_dimensions['D'].width = 15 
        sheet.column_dimensions['E'].width = 15 
        sheet.column_dimensions['F'].width = 15 
        sheet.column_dimensions['G'].width = 15 
        sheet.column_dimensions['H'].width = 15 

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        self.file = base64.b64encode(data)
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=product.report.on.date.wizard.spt&download=true&field=file&id=%s&filename=%s.xlsx' % (active_id, f_name),
            'target': 'self',
        }
