from odoo import _, api, fields, models, tools
from openpyxl import Workbook
from openpyxl.styles import Border, Side, Alignment, Font
import base64
from io import BytesIO

class reserved_product_report(models.TransientModel):
    _name = "reserved.product.report"
    _description = "Reserved Product Report"

    product_sku = fields.Char('Products SKU\'s')
    report_file = fields.Binary()

    def action_export(self):
        active_id = self.id
        f_name = 'Reserved Product Report'
        workbook = Workbook()
        bd = Side(style='thin', color="000000")
        top_bottom_border = Border(top=bd, bottom=bd)
        heading_font = Font(name="Garamond", size="10", bold=True)
        table_font = Font(name="Garamond", size="10", bold=False)
        align_left = Alignment(
            vertical="center", horizontal='left', text_rotation=0, wrap_text=True)
        align_right = Alignment(
            vertical="center", horizontal='right', text_rotation=0, wrap_text=True)
        align_center = Alignment(
            vertical="center", horizontal='center', text_rotation=0, wrap_text=True)

        product_internal_ref = self.product_sku.split(',') if self.product_sku else ''
        for sku in list(dict.fromkeys(product_internal_ref)):
            sheet = workbook.create_sheet(title=sku, index=0)
            
            table_header_row = 1
            sheet.row_dimensions[table_header_row].height = 30
            sheet.cell(row=table_header_row, column=1).value = 'Order Reference'
            sheet.cell(row=table_header_row, column=2).value = "Customer"
            sheet.cell(row=table_header_row, column=3).value = "Creation Date"
            sheet.cell(row=table_header_row, column=4).value = "Updated On"
            sheet.cell(row=table_header_row, column=5).value = "Created by"
            sheet.cell(row=table_header_row, column=6).value = "Updated By"
            sheet.cell(row=table_header_row, column=7).value = 'Shipped Date'
            sheet.cell(row=table_header_row, column=7).value = "Salesperson"
            sheet.cell(row=table_header_row, column=8).value = "Order Source"
            sheet.cell(row=table_header_row, column=9).value = "Reserved Qty"
            sheet.cell(row=table_header_row, column=10).value = "Status"
            sheet.cell(row=table_header_row, column=11).value = "Payment Status"
            sheet.cell(row=table_header_row, column=12).value = "Has Payment Link"

            sheet.cell(row=table_header_row, column=1).alignment = align_center
            sheet.cell(row=table_header_row, column=2).alignment = align_center
            sheet.cell(row=table_header_row, column=3).alignment = align_center
            sheet.cell(row=table_header_row, column=4).alignment = align_center
            sheet.cell(row=table_header_row, column=5).alignment = align_center
            sheet.cell(row=table_header_row, column=6).alignment = align_center
            sheet.cell(row=table_header_row, column=7).alignment = align_center
            sheet.cell(row=table_header_row, column=8).alignment = align_center
            sheet.cell(row=table_header_row, column=9).alignment = align_center
            sheet.cell(row=table_header_row, column=10).alignment = align_center
            sheet.cell(row=table_header_row, column=11).alignment = align_center
            sheet.cell(row=table_header_row, column=12).alignment = align_center

            for col in range(1, 13):
                sheet.cell(row=table_header_row,
                        column=col).border = top_bottom_border
                sheet.cell(row=table_header_row, column=col).font = heading_font
            
            row_index = table_header_row+1

            order_ids = self.env['sale.order.line'].search([('product_id.default_code','=',sku.strip()),('state','in',('in_scanning','scanned','scan'))]).mapped('order_id')
            for order in order_ids:
                sheet.row_dimensions[row_index].height = 22
                sheet.cell(row=row_index, column=1).value = order.name or ''
                sheet.cell(row=row_index, column=2).value = order.partner_id.display_name or ''
                sheet.cell(row=row_index, column=3).value = order.create_date or ''
                sheet.cell(row=row_index, column=4).value = order.updated_on or ''
                sheet.cell(row=row_index, column=5).value = order.create_uid.name or ''
                sheet.cell(row=row_index, column=6).value = order.updated_by.name or ''
                sheet.cell(row=row_index, column=7).value = order.user_id.name or ''
                sheet.cell(row=row_index, column=8).value = order.source_spt or ''
                sheet.cell(row=row_index, column=9).value = order.order_line.filtered(lambda x:x.product_id.default_code == sku).picked_qty or 0
                sheet.cell(row=row_index, column=10).value = dict(order._fields['state'].selection).get(order.state) or ''
                sheet.cell(row=row_index, column=11).value = dict(order._fields['payment_status'].selection).get(order.payment_status) or ''
                sheet.cell(row=row_index, column=12).value = 1 if order.is_payment_link else 0

                sheet.cell(row=row_index, column=1).font = table_font
                sheet.cell(row=row_index, column=2).font = table_font
                sheet.cell(row=row_index, column=3).font = table_font
                sheet.cell(row=row_index, column=4).font = table_font
                sheet.cell(row=row_index, column=5).font = table_font
                sheet.cell(row=row_index, column=6).font = table_font
                sheet.cell(row=row_index, column=7).font = table_font
                sheet.cell(row=row_index, column=8).font = table_font
                sheet.cell(row=row_index, column=9).font = table_font
                sheet.cell(row=row_index, column=10).font = table_font
                sheet.cell(row=row_index, column=11).font = table_font
                sheet.cell(row=row_index, column=12).font = table_font

                sheet.cell(row=row_index, column=1).alignment = align_left
                sheet.cell(row=row_index, column=2).alignment = align_left
                sheet.cell(row=row_index, column=3).alignment = align_right
                sheet.cell(row=row_index, column=4).alignment = align_right
                sheet.cell(row=row_index, column=5).alignment = align_left
                sheet.cell(row=row_index, column=6).alignment = align_left
                sheet.cell(row=row_index, column=7).alignment = align_left
                sheet.cell(row=row_index, column=8).alignment = align_left
                sheet.cell(row=row_index, column=9).alignment = align_left
                sheet.cell(row=row_index, column=10).alignment = align_right
                sheet.cell(row=row_index, column=11).alignment = align_left
                sheet.cell(row=row_index, column=12).alignment = align_left

                row_index += 1
            
            sheet.column_dimensions['A'].width = 17
            sheet.column_dimensions['B'].width = 40
            sheet.column_dimensions['C'].width = 25
            sheet.column_dimensions['D'].width = 25
            sheet.column_dimensions['E'].width = 25
            sheet.column_dimensions['F'].width = 25
            sheet.column_dimensions['G'].width = 25
            sheet.column_dimensions['H'].width = 25
            sheet.column_dimensions['I'].width = 15
            sheet.column_dimensions['J'].width = 20
            sheet.column_dimensions['K'].width = 15
            sheet.column_dimensions['L'].width = 15

        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        self.report_file = base64.b64encode(data)
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=reserved.product.report&download=true&field=report_file&id=%s&filename=%s.xlsx' % (active_id, f_name),
            'target': 'self',
        }
