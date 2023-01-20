from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from openpyxl.workbook.workbook import Workbook
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
import base64
from io import BytesIO
import pandas as pd
import xlsxwriter
from lxml import etree

class sales_commission_report_wizard(models.TransientModel):
    _name = 'sales.commission.report.wizard'
    _description = 'Sales Commission Report'

    def _get_salesmanagers(self):
        if self.env.user.has_group('base.group_system'):
            managers = self.env.ref('tzc_sales_customization_spt.group_sales_manager_spt').users
            return [('is_sales_manager','=',True),('id','in',managers.ids),'|',('active','=',True),('active','=',False)]
        else:
            return [('is_sales_manager','=',True)]
    
    # def _get_sales_person(self):
    #     return [('id','=',self.env.user.id),('is_salesperson','=',True),'|',('active','=',True),('active','=',False)]

    def _get_sales_person(self):
        user_id = self.env.user
        if not user_id.has_group('base.group_system'):
            return [('is_salesperson','=',True),('id','in',user_id.allow_user_ids.ids + user_id.ids),'|',('active','=',True),('active','=',False)]
        else:
            return [('is_salesperson','=',True)]

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    sales_person_ids = fields.Many2many('res.users', 'sales_commission_wizard_res_users_rel', 'wizard_id', 'user_id', string="Sales Persons",default=lambda self:self.env.user,domain=_get_sales_person)
    sales_manager_ids = fields.Many2many('res.users', 'sales_manager_commission_wizard_res_users_rel', 'wizard_id', 'user_id', string="Sales Manager",default=lambda self:self.env.user,domain=_get_salesmanagers)
    file = fields.Binary()
    commission_for = fields.Selection([('sales_person', 'Salesperson'),('sales_manager', 'Sales Manager')],default="sales_person")
    commission_is = fields.Selection([('all','All'),('is_paid','Paid'),('is_unpaid','Unpaid')],default='all',string="Commission Type")
    apply_groups = fields.Selection([('admin','Administrator'),('sales_person','Salesperson'),('sales_manager','Sales Manager')],string="Apply Groups")


    @api.model
    def default_get(self, default_fields):
        res= super(sales_commission_report_wizard, self).default_get(default_fields)
        apply_groups =''
        if self.env.user.has_group('tzc_sales_customization_spt.group_sales_manager_spt'):
            apply_groups = 'sales_manager'
        if self.env.user.has_group('sales_team.group_sale_salesman'):
            apply_groups = 'sales_person'
        if self.env.user.has_group('base.group_system'):
            apply_groups = 'admin'
        res['apply_groups'] = apply_groups
        return res

    def get_users(self,return_users=False):
        users = False
        user_data = {}
        if self.commission_for == 'sales_person':
            users = self.with_context(active_test=False).sales_person_ids
        if self.commission_for == 'sales_manager':
            users = self.with_context(active_test=False).sales_manager_ids
        if return_users:
            return users.sorted(lambda x: x.name)
        for user in users.sorted(lambda x: x.name):
            if user.id in user_data.keys():
                user_data[user.id]['lines'].extend(self.get_commission(user))
            else:
                user_data[user.id] = {
                    'name':user.name,
                    'street':user.partner_id.street,
                    'street2':user.partner_id.street2,
                    'city':user.partner_id.city,
                    'state':user.partner_id.state_id.name,
                    'country':user.partner_id.country_id.name,
                    'phone':user.partner_id.phone,
                    'email':user.partner_id.email,
                    'start_date':self.start_date,
                    'end_date':self.end_date,
                    'commission_rule':user.commission_rule_id.name if self.commission_for == 'sales_person' else user.manager_commission_rule_id.name if self.commission_for == 'sales_manager' else '',
                    'lines':self.get_commission(user),
                    }
        
        return user_data

    def action_pdf_report(self):
        self.validate_dates()
        return self.env.ref('tzc_sales_customization_spt.action_sales_commission_pdf_report').report_action(self)

    def get_commission(self, sale_person):
        report_table_lines = []
        domain= [('user_id','=',sale_person.id)]
        if self.start_date:
            domain.append(('invoice_id.invoice_date', '>=', self.start_date))
        if self.end_date:
            domain.append(('invoice_id.invoice_date', '<=', self.end_date))
        if self.commission_is == 'is_paid':
            domain.append(('state','=','paid'))
        if self.commission_is == 'is_unpaid':
            domain.append(('state','=','draft'))
        if self.commission_is == 'all':
            domain.append(('state','in',['draft','paid']))
        
        invoice_ids = self.env['kits.commission.lines'].sudo().search(domain).mapped('invoice_id')

        state = []
        if self.commission_is == 'is_paid':
            state.append('paid')
        elif self.commission_is == 'is_unpaid':
            state.append('draft')
        elif self.commission_is == 'all':
            state.append('draft')
            state.append('paid')
        # if invoice_ids and ((sale_person.commission_rule_id and self.commission_for =='sales_person') or( sale_person.manager_commission_rule_id and self.commission_for =='sales_manager')):
        for invoice in invoice_ids:
            order = self.env['sale.order'].search([('invoice_ids','in',invoice.ids)],limit=1)
            commission = 0.0
            if self.commission_for == 'sales_person':
                commission = sum(invoice.commission_line_ids.filtered(lambda x: x.commission_for == 'saleperson' and x.user_id == sale_person and x.state in state).mapped('amount'))
            elif self.commission_for == 'sales_manager':
                commission = sum(invoice.commission_line_ids.filtered(lambda x: x.commission_for == 'manager' and x.user_id == sale_person and x.state in state).mapped('amount'))
            else:
                pass
            if commission:
                report_table_lines.append(self.data_dict_pdf(invoice,commission))
        return report_table_lines

    def action_xls_report(self):
        self.validate_dates()
        workbook = Workbook()
        users = self.get_users(return_users=True)
        right_alignment = Alignment(
            vertical='center', horizontal='right', text_rotation=0, wrap_text=True)
        for sale_person in users:
            total_lines = {}
            paid_unpaid_total = {}
            sheet_index = 0
            sheet = workbook.create_sheet(title=sale_person.name.replace('/','_'),index=sheet_index)
            report_table_lines = []
            domain = [('user_id','=',sale_person.id)]
            if self.start_date:
                domain.append(('invoice_id.invoice_date', '>=', self.start_date))
            if self.end_date:
                domain.append(('invoice_id.invoice_date', '<=', self.end_date))
            if self.commission_is == 'is_paid':
                domain.append(('state','=','paid'))
            if self.commission_is == 'is_unpaid':
                domain.append(('state','=','draft'))
            if self.commission_is == 'all':
                domain.append(('state','in',['draft','paid']))
            
            header_font = Font(name='Calibri',size='11',bold=True)
            bd = Side(style='thin', color="000000")
            top_bottom_border = Border(top=bd,bottom=bd)
            # Merge rows (Start Date & End Date & Commissioin Structure)
            sheet.merge_cells('A1:B1')
            sheet.cell(row=1, column=1).value = 'Salesperson : %s'%(sale_person.name if sale_person.name else '')
            sheet.merge_cells('A2:B2')
            sheet.cell(row=2, column=1).value = 'Email : %s'%(sale_person.partner_id.email if sale_person.partner_id and sale_person.partner_id.email else '')
            sheet.merge_cells('A3:B3')
            sheet.cell(row=3, column=1).value = 'Tel : %s'%(str(sale_person.phone) if sale_person.phone else '')
            sheet.merge_cells('A5:B5')
            sheet.cell(row=5, column=1).value = 'Start Date : %s'%(str(self.start_date) if self.start_date else "")
            sheet.merge_cells('A7:B7')
            sheet.cell(row=7, column=1).value = 'End Date : %s'%(str(self.end_date) if self.end_date else '')
            sheet.merge_cells('A9:E9')
            sheet.cell(row=9, column=1).value = 'Commission Structure : %s'%(sale_person.commission_rule_id.name if self.commission_for == 'sales_person' else sale_person.manager_commission_rule_id.name if self.commission_for == 'sales_manager' else '')

            invoice_ids = self.env['kits.commission.lines'].sudo().search(domain).mapped('invoice_id')

            table_header = 11
            sheet.cell(row=table_header, column=1).value = 'Date'
            sheet.cell(row=table_header, column=2).value = 'Order'
            sheet.cell(row=table_header, column=3).value = 'Invoice'
            sheet.cell(row=table_header, column=4).value = 'Customer'
            sheet.cell(row=table_header, column=5).value = 'Country'
            sheet.cell(row=table_header, column=6).value = 'Territory'
            sheet.cell(row=table_header, column=7).value = 'Quantity'
            sheet.cell(row=table_header, column=8).value = 'Currency'
            sheet.cell(row=table_header, column=9).value = 'Gross Sale'
            sheet.cell(row=table_header, column=10).value = 'Discount'
            sheet.cell(row=table_header, column=11).value = 'Tax'
            sheet.cell(row=table_header, column=12).value = 'Net Sale'
            sheet.cell(row=table_header, column=13).value = 'Commission'
            sheet.cell(row=table_header, column=14).value = 'Commission type'

            sheet.cell(row=table_header, column=1).font = header_font
            sheet.cell(row=table_header, column=1).border = top_bottom_border
            sheet.cell(row=table_header, column=2).font = header_font
            sheet.cell(row=table_header, column=2).border = top_bottom_border
            sheet.cell(row=table_header, column=3).font = header_font
            sheet.cell(row=table_header, column=3).border = top_bottom_border
            sheet.cell(row=table_header, column=4).font = header_font
            sheet.cell(row=table_header, column=4).border = top_bottom_border
            sheet.cell(row=table_header, column=5).font = header_font
            sheet.cell(row=table_header, column=5).border = top_bottom_border
            sheet.cell(row=table_header, column=6).font = header_font
            sheet.cell(row=table_header, column=6).border = top_bottom_border
            sheet.cell(row=table_header, column=7).font = header_font
            sheet.cell(row=table_header, column=7).border = top_bottom_border
            sheet.cell(row=table_header, column=8).font = header_font
            sheet.cell(row=table_header, column=8).border = top_bottom_border
            sheet.cell(row=table_header, column=8).alignment = right_alignment
            sheet.cell(row=table_header, column=9).font = header_font
            sheet.cell(row=table_header, column=9).border = top_bottom_border
            sheet.cell(row=table_header, column=9).alignment = right_alignment
            sheet.cell(row=table_header, column=10).font = header_font
            sheet.cell(row=table_header, column=10).border = top_bottom_border
            sheet.cell(row=table_header, column=10).alignment = right_alignment
            sheet.cell(row=table_header, column=11).font = header_font
            sheet.cell(row=table_header, column=11).border = top_bottom_border
            sheet.cell(row=table_header, column=11).alignment = right_alignment
            sheet.cell(row=table_header, column=12).font = header_font
            sheet.cell(row=table_header, column=12).border = top_bottom_border
            sheet.cell(row=table_header, column=12).alignment = right_alignment
            sheet.cell(row=table_header, column=13).font = header_font
            sheet.cell(row=table_header, column=13).border = top_bottom_border
            sheet.cell(row=table_header, column=13).alignment = right_alignment
            sheet.cell(row=table_header, column=14).font = header_font
            sheet.cell(row=table_header, column=14).border = top_bottom_border
            row_index=table_header+1

            # total_qty = 0
            # if (invoice_ids and sale_person.commission_rule_id and self.commission_for =='sales_person') or (sale_person.manager_commission_rule_id and self.commission_for =='sales_manager'):
            for invoice in invoice_ids:
                order = self.env['sale.order'].search([('invoice_ids','in',invoice.ids)],limit=1)
                commission = 0.0

                state = []
                if self.commission_is == 'is_paid':
                    state.append('paid')
                elif self.commission_is == 'is_unpaid':
                    state.append('draft')
                elif self.commission_is == 'all':
                    state.append('draft')
                    state.append('paid')

                if self.commission_for == 'sales_person':
                    commission = sum(invoice.commission_line_ids.filtered(lambda x: x.commission_for == 'saleperson' and x.user_id == sale_person and x.state in state).mapped('amount'))
                elif self.commission_for == 'sales_manager':
                    commission = sum(invoice.mapped('commission_line_ids').filtered(lambda x: x.commission_for == 'manager' and x.user_id == sale_person and x.state in state).mapped('amount'))
                else:
                    pass

                if commission:
                    sheet.cell(row=row_index, column=1).value = (order.date_order).strftime("%d-%m-%Y")
                    sheet.cell(row=row_index, column=2).value = order.name
                    sheet.cell(row=row_index, column=3).value = invoice.name or ''
                    sheet.cell(row=row_index, column=4).value = order.partner_id.name or ''
                    sheet.cell(row=row_index, column=5).value = order.partner_id.country_id.name or ''
                    sheet.cell(row=row_index, column=6).value = order.partner_id.territory.name or ''
                    sheet.cell(row=row_index, column=7).value = order.ordered_qty or 0
                    # total_qty += order.ordered_qty
                    sheet.cell(row=row_index, column=8).value = order.currency_id.name or ''
                    sheet.cell(row=row_index, column=8).alignment = right_alignment
                    sheet.cell(row=row_index, column=9).value = '$ {:,.2f}'.format(round(invoice.amount_without_discount,2) or 0.0)
                    sheet.cell(row=row_index, column=9).alignment = right_alignment
                    sheet.cell(row=row_index, column=10).value = '$ {:,.2f}'.format(round(invoice.amount_discount,2) or 0.0)
                    sheet.cell(row=row_index, column=10).alignment = right_alignment
                    sheet.cell(row=row_index, column=11).value = '$ {:,.2f}'.format(round(invoice.amount_tax,2) or 0.0)
                    sheet.cell(row=row_index, column=11).alignment = right_alignment
                    sheet.cell(row=row_index, column=12).value = '$ {:,.2f}'.format(round(invoice.amount_total,2) or 0.0)
                    sheet.cell(row=row_index, column=12).alignment = right_alignment
                    sheet.cell(row=row_index, column=13).value = '$ {:,.2f}'.format(round(commission, 2) or 0.0)
                    sheet.cell(row=row_index, column=13).alignment = right_alignment
                    if self.commission_is == 'all':
                        if invoice.inv_payment_status in ['full','over']:
                            sheet.cell(row=row_index, column=14).value = 'Paid' 
                        else:
                            sheet.cell(row=row_index, column=14).value = 'Unpaid' 
                    elif self.commission_is == 'is_paid':
                        sheet.cell(row=row_index, column=14).value = 'Paid'
                    elif self.commission_is == 'is_unpaid':
                        sheet.cell(row=row_index, column=14).value = 'Unpaid'
                    row_index+=1

                    if order.currency_id.name in total_lines:
                        total_lines[order.currency_id.name]['qty'] = total_lines[order.currency_id.name]['qty'] + order.ordered_qty
                        total_lines[order.currency_id.name]['gross_sale'] = round(total_lines[order.currency_id.name]['gross_sale']+invoice.amount_without_discount,2)
                        total_lines[order.currency_id.name]['discount'] = round(total_lines[order.currency_id.name]['discount']+invoice.amount_discount,2)
                        total_lines[order.currency_id.name]['tax'] = round(total_lines[order.currency_id.name]['tax']+invoice.amount_tax,2)
                        total_lines[order.currency_id.name]['net_sale'] = round(total_lines[order.currency_id.name]['net_sale']+invoice.amount_total,2)
                        total_lines[order.currency_id.name]['commission'] = round(total_lines[order.currency_id.name]['commission']+commission,2)
                    else:
                        total_lines[order.currency_id.name] = {
                            'qty':round(order.ordered_qty,2),
                            'gross_sale':round(invoice.amount_without_discount,2),
                            'discount':round(invoice.amount_discount,2),
                            'tax':round(invoice.amount_tax,2),
                            'net_sale':round(invoice.amount_total,2),
                            'commission':commission,
                        }
                    
                    if order.currency_id.name in paid_unpaid_total:
                        if self.commission_for == 'sales_person':
                            paid_unpaid_total[order.currency_id.name]['paid'] = paid_unpaid_total[order.currency_id.name]['paid'] + round(sum(invoice.commission_line_ids.filtered(lambda x: x.commission_for == 'saleperson' and x.user_id == sale_person and x.state == 'paid').mapped('amount')),2)
                            paid_unpaid_total[order.currency_id.name]['unpaid'] = paid_unpaid_total[order.currency_id.name]['unpaid'] + round(sum(invoice.commission_line_ids.filtered(lambda x: x.commission_for == 'saleperson' and x.user_id == sale_person and x.state == 'draft').mapped('amount')),2)
                        elif self.commission_for == 'sales_manager':
                            paid_unpaid_total[order.currency_id.name]['paid'] = paid_unpaid_total[order.currency_id.name]['paid'] + round(sum(invoice.mapped('commission_line_ids').filtered(lambda x: x.commission_for == 'manager' and x.user_id == sale_person and x.state == 'paid').mapped('amount')),2)
                            paid_unpaid_total[order.currency_id.name]['unpaid'] = paid_unpaid_total[order.currency_id.name]['unpaid'] + round(sum(invoice.mapped('commission_line_ids').filtered(lambda x: x.commission_for == 'manager' and x.user_id == sale_person and x.state == 'draft').mapped('amount')),2)
                    else:
                        if self.commission_for == 'sales_person':
                            paid_unpaid_total[order.currency_id.name] = {'paid':round(sum(invoice.commission_line_ids.filtered(lambda x: x.commission_for == 'saleperson' and x.user_id == sale_person and x.state == 'paid').mapped('amount')),2),'unpaid':round(sum(invoice.commission_line_ids.filtered(lambda x: x.commission_for == 'saleperson' and x.user_id == sale_person and x.state == 'draft').mapped('amount')),2)}
                        elif self.commission_for == 'sales_manager':
                            paid_unpaid_total[order.currency_id.name] = {'paid':round(sum(invoice.mapped('commission_line_ids').filtered(lambda x: x.commission_for == 'manager' and x.user_id == sale_person and x.state == 'paid').mapped('amount')),2),'unpaid':round(sum(invoice.mapped('commission_line_ids').filtered(lambda x: x.commission_for == 'manager' and x.user_id == sale_person and x.state == 'draft').mapped('amount')),2)}

            sheet.merge_cells('A'+str(row_index)+':N'+str(row_index))
            total_row = row_index + 1
            for total_line in total_lines:
                sheet.cell(row=total_row, column=7).value = total_lines[total_line]['qty'] or 0.00
                sheet.cell(row=total_row, column=7).font = header_font
                sheet.cell(row=total_row, column=8).value = "Total (%s)"%(total_line)
                sheet.cell(row=total_row, column=8).font = header_font
                sheet.cell(row=total_row, column=8).alignment = right_alignment
                sheet.cell(row=total_row, column=9).value = '$ {:,.2f}'.format(total_lines[total_line]['gross_sale'] or 0.00)
                sheet.cell(row=total_row, column=9).font = header_font
                sheet.cell(row=total_row, column=9).alignment = right_alignment
                sheet.cell(row=total_row, column=10).value = '$ {:,.2f}'.format(total_lines[total_line]['discount'] or 0.00)
                sheet.cell(row=total_row, column=10).font = header_font
                sheet.cell(row=total_row, column=10).alignment = right_alignment
                sheet.cell(row=total_row, column=11).value = '$ {:,.2f}'.format(total_lines[total_line]['tax'] or 0.00)
                sheet.cell(row=total_row, column=11).font = header_font
                sheet.cell(row=total_row, column=11).alignment = right_alignment
                sheet.cell(row=total_row, column=12).value = '$ {:,.2f}'.format(total_lines[total_line]['net_sale'] or 0.00)
                sheet.cell(row=total_row, column=12).font = header_font
                sheet.cell(row=total_row, column=12).alignment = right_alignment
                sheet.cell(row=total_row, column=13).value = '$ {:,.2f}'.format(total_lines[total_line]['commission'] or 0.00)
                sheet.cell(row=total_row, column=13).font = header_font
                sheet.cell(row=total_row, column=13).alignment = right_alignment
                total_row += 1

            total_row += 1
            for paid_unpaid in paid_unpaid_total:
                if self.commission_is == 'is_paid':
                    sheet.cell(row=total_row, column=13).value = "Paid Commission (%s)"%(paid_unpaid)
                    sheet.cell(row=total_row, column=13).font = header_font
                    sheet.cell(row=total_row, column=14).value = '$ {:,.2f}'.format(paid_unpaid_total[paid_unpaid]['paid'] or 0.00)
                    sheet.cell(row=total_row, column=14).font = header_font
                    sheet.cell(row=total_row, column=14).alignment = right_alignment
                if self.commission_is == 'is_unpaid':
                    sheet.cell(row=total_row, column=13).value = "Unpaid Commission (%s)"%(paid_unpaid)
                    sheet.cell(row=total_row, column=13).font = header_font
                    sheet.cell(row=total_row, column=14).value = '$ {:,.2f}'.format(paid_unpaid_total[paid_unpaid]['unpaid'] or 0.00)
                    sheet.cell(row=total_row, column=14).font = header_font
                    sheet.cell(row=total_row, column=14).alignment = right_alignment
                if self.commission_is =='all':
                    sheet.cell(row=total_row, column=13).value = "Paid Commission (%s)"%(paid_unpaid)
                    sheet.cell(row=total_row, column=13).font = header_font
                    sheet.cell(row=total_row, column=14).value = '$ {:,.2f}'.format(paid_unpaid_total[paid_unpaid]['paid'] or 0.00)
                    sheet.cell(row=total_row, column=14).font = header_font
                    sheet.cell(row=total_row, column=14).alignment = right_alignment
                    total_row += 1
                    sheet.cell(row=total_row, column=13).value = "Unpaid Commission (%s)"%(paid_unpaid)
                    sheet.cell(row=total_row, column=13).font = header_font
                    sheet.cell(row=total_row, column=14).value = '$ {:,.2f}'.format(paid_unpaid_total[paid_unpaid]['unpaid'] or 0.00)
                    sheet.cell(row=total_row, column=14).font = header_font
                    sheet.cell(row=total_row, column=14).alignment = right_alignment
                total_row += 1

            # Colomn size
            sheet.column_dimensions['A'].width = 15
            sheet.column_dimensions['B'].width = 25
            sheet.column_dimensions['C'].width = 15
            sheet.column_dimensions['D'].width = 30
            sheet.column_dimensions['E'].width = 25
            sheet.column_dimensions['F'].width = 20
            sheet.column_dimensions['G'].width = 20
            sheet.column_dimensions['H'].width = 20
            sheet.column_dimensions['I'].width = 15
            sheet.column_dimensions['J'].width = 15
            sheet.column_dimensions['K'].width = 15
            sheet.column_dimensions['L'].width = 15
            sheet.column_dimensions['M'].width = 30
            sheet.column_dimensions['N'].width = 25
            sheet_index+=1
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        self.file = base64.b64encode(data)
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=sales.commission.report.wizard&download=true&field=file&id=%s&filename=%s.xlsx' % (self.id,'sale_commission_report'),
            'target': 'self',
        }

    def validate_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise UserError(_("Start Date should be lesser than End Date."))

    def data_dict_pdf(self,order,commission):
        data_dict = {}
        sale_order = self.env['sale.order'].search([('invoice_ids','in',order.ids)])
        invoice_num = ''
        commission_is = ''
        if order.inv_payment_status in ['over','full']:
            commission_is = 'Paid'
        else:
            commission_is = 'Unpaid'
        data_dict['gross_sale'] = order.amount_without_discount
        data_dict['date'] = sale_order.date_order.strftime("%d-%m-%Y")
        data_dict['discount'] = order.amount_discount
        data_dict['net_sale'] = order.amount_total
        data_dict['sale_order'] = sale_order.name
        data_dict['customer'] = order.partner_id.name
        data_dict['country'] = order.partner_id.country_id.name
        data_dict['territory'] = order.partner_id.territory.name
        data_dict['qty'] = sale_order.ordered_qty
        data_dict['tax'] = order.amount_tax
        data_dict['currency'] = order.currency_id.name
        data_dict['commission'] = round(commission, 2)
        data_dict['commission_is'] = commission_is

        if order.state == 'posted':
            invoice_num = invoice_num + order.name + ', '
        data_dict['invoice_order'] = invoice_num[:-2]

        return data_dict

    def get_currency_total(self,lines):
        currency_dict = {}
        for line in lines:
            currency = line['currency']
            if currency not in currency_dict.keys():
                currency_dict[currency] = {'gross_sale':line['gross_sale'],'discount':line['discount'],'tax':line['tax'],'net_sale':line['net_sale'],'commission':line['commission']}
            else:
                currency_dict[currency]['gross_sale'] = round(currency_dict[currency]['gross_sale']+line['gross_sale'],2)
                currency_dict[currency]['discount'] = round(currency_dict[currency]['discount']+line['discount'],2)
                currency_dict[currency]['tax'] = round(currency_dict[currency]['tax']+line['tax'],2)
                currency_dict[currency]['net_sale'] = round(currency_dict[currency]['net_sale']+line['net_sale'],2)
                currency_dict[currency]['commission'] = round(currency_dict[currency]['commission']+line['commission'],2)
        
        return currency_dict

    def get_paid_unpaid_commision_total(self,lines):
        paid_unpaid_total = {}
        for line in lines:
            if line['currency'] in paid_unpaid_total:
                paid_unpaid_total[line['currency']]['paid'] = paid_unpaid_total[line['currency']]['paid'] + line['commission'] if line['commission_is'] == 'Paid' else paid_unpaid_total[line['currency']]['paid']
                paid_unpaid_total[line['currency']]['unpaid'] = paid_unpaid_total[line['currency']]['unpaid'] + line['commission'] if line['commission_is'] == 'Unpaid' else paid_unpaid_total[line['currency']]['unpaid']
            else:
                paid_unpaid_total[line['currency']] = {'paid':line['commission'] if line['commission_is'] == 'Paid' else 0.0,'unpaid':line['commission'] if line['commission_is'] == 'Unpaid' else 0.0}

        return paid_unpaid_total
    
    @api.model
    def _fields_view_get(self, view_id=None, view_type=None, toolbar=False, submenu=False):
        res = super(sales_commission_report_wizard, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self._context.get('kits_website_name'):
            doc = etree.XML(res['arch'])
            for node in doc.xpath("//field[@name='website_id']"):
                node.attrib['invisible'] = '1'
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    # def is_accessible_to(self,user):
    #     self = self.sudo()
    #     self.ensure_one()
    #     result = False
    #     if user:
    #         if user.has_group('base.group_system') or user.has_group('tzc_sales_customization_spt.group_sales_manager_spt') or user.has_group('sales_team.group_sale_salesman'):
    #             result = True
    #     return result
