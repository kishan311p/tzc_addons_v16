from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from openpyxl.workbook.workbook import Workbook
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
import base64
from io import BytesIO
import requests

class shipping_cost_analysis_wizard(models.TransientModel):
    _name = "shipping.cost.analysis.wizard"
    _description = "Shipping Cost Analysis Wizard"

    start_date = fields.Date()
    end_date = fields.Date()
    include_calculated_cost = fields.Boolean('Calculate shipping cost via API ?')
    file = fields.Binary()
    carrier_id = fields.Many2one('delivery.carrier','Shipping Method')

    def validate_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise UserError(_("Start Date should be lesser than End Date."))

    def action_xls_report(self):
        self.validate_dates()
        domain = [('state', 'in', ['shipped','draft_inv','open_inv','paid'])]
        if self.start_date:
            domain.append(('date_order', '>=', self.start_date))
        if self.end_date:
            domain.append(('date_order', '<=', self.end_date))
        sale_order = self.env['sale.order'].search(domain)
        f_name = 'Shipping Cost Analysis'
        workbook = Workbook()
        sheet = workbook.create_sheet(title="Shipping Cost", index=0)
        header_font = Font(name='Calibri',size='11',bold=True)
        bd = Side(style='thin', color="000000")
        top_bottom_border = Border(top=bd,bottom=bd)
        left_alignment = Alignment(
            vertical='center', horizontal='left', text_rotation=0, wrap_text=True)
        right_alignment = Alignment(
            vertical='center', horizontal='right', text_rotation=0, wrap_text=True)
        
        # Critria
        header_row = 0
        if self.carrier_id:
            header_row = 1
            # start date
            sheet.merge_cells('A'+str(header_row)+':B'+str(header_row))
            sheet.cell(row=header_row, column=1).value = 'Start Date : {}'.format(str(self.start_date) if self.start_date else '')
            sheet.cell(row=header_row, column=1).font = header_font

            # shipping provider name
            sheet.merge_cells('D'+str(header_row)+':G'+str(header_row))
            sheet.cell(row=header_row, column=4).value = 'Shipping Provider : %s'%(self.carrier_id.name or '')
            sheet.cell(row=header_row, column=4).font = header_font

            header_row += 1
            # end date
            sheet.merge_cells('A'+str(header_row)+':B'+str(header_row))
            sheet.cell(row=header_row, column=1).value = 'End Date : {}'.format(str(self.end_date) if self.end_date else '')
            sheet.cell(row=header_row, column=1).font = header_font

        table_header = header_row + 2
        sheet.cell(row=table_header, column=1).value = 'Shipping Date'
        sheet.cell(row=table_header, column=2).value = 'Order'
        sheet.cell(row=table_header, column=3).value = 'Order Status'
        sheet.cell(row=table_header, column=4).value = 'Salesperson'
        sheet.cell(row=table_header, column=5).value = 'Order Amount'
        sheet.cell(row=table_header, column=6).value = 'Currency'
        sheet.cell(row=table_header, column=7).value = 'Quantity'
        sheet.cell(row=table_header, column=8).value = 'Volume (m3)'
        sheet.cell(row=table_header, column=9).value = 'Actual Weight (kg)'
        sheet.cell(row=table_header, column=10).value = 'Calculated Weight (kg)'
        sheet.cell(row=table_header, column=11).value = 'Customer ID'
        sheet.cell(row=table_header, column=12).value = 'Customer'
        sheet.cell(row=table_header, column=13).value = 'Address'
        sheet.cell(row=table_header, column=14).value = 'City'
        sheet.cell(row=table_header, column=15).value = 'Zip'
        sheet.cell(row=table_header, column=16).value = 'Country'
        sheet.cell(row=table_header, column=17).value = 'Carrier'
        sheet.cell(row=table_header, column=18).value = 'Tracking Number'
        sheet.cell(row=table_header, column=19).value = 'Shipping Cost'
        sheet.cell(row=table_header, column=20).value = 'Carrier Method'
        sheet.cell(row=table_header, column=21).value = 'Calculated Shipping Cost'
        sheet.cell(row=table_header, column=22).value = 'Difference'
        sheet.cell(row=table_header, column=23).value = 'Error'

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
        sheet.cell(row=table_header, column=5).alignment = right_alignment
        sheet.cell(row=table_header, column=6).font = header_font
        sheet.cell(row=table_header, column=6).border = top_bottom_border
        sheet.cell(row=table_header, column=6).alignment = right_alignment
        sheet.cell(row=table_header, column=7).font = header_font
        sheet.cell(row=table_header, column=7).border = top_bottom_border
        sheet.cell(row=table_header, column=8).font = header_font
        sheet.cell(row=table_header, column=8).border = top_bottom_border
        sheet.cell(row=table_header, column=9).font = header_font
        sheet.cell(row=table_header, column=9).border = top_bottom_border
        sheet.cell(row=table_header, column=10).font = header_font
        sheet.cell(row=table_header, column=10).border = top_bottom_border
        sheet.cell(row=table_header, column=11).font = header_font
        sheet.cell(row=table_header, column=11).border = top_bottom_border
        sheet.cell(row=table_header, column=12).font = header_font
        sheet.cell(row=table_header, column=12).border = top_bottom_border
        sheet.cell(row=table_header, column=13).font = header_font
        sheet.cell(row=table_header, column=13).border = top_bottom_border
        sheet.cell(row=table_header, column=14).font = header_font
        sheet.cell(row=table_header, column=14).border = top_bottom_border
        sheet.cell(row=table_header, column=15).font = header_font
        sheet.cell(row=table_header, column=15).border = top_bottom_border
        sheet.cell(row=table_header, column=16).font = header_font
        sheet.cell(row=table_header, column=16).border = top_bottom_border
        sheet.cell(row=table_header, column=17).font = header_font
        sheet.cell(row=table_header, column=17).border = top_bottom_border
        sheet.cell(row=table_header, column=18).font = header_font
        sheet.cell(row=table_header, column=18).border = top_bottom_border
        sheet.cell(row=table_header, column=19).font = header_font
        sheet.cell(row=table_header, column=19).border = top_bottom_border
        sheet.cell(row=table_header, column=19).alignment = right_alignment
        sheet.cell(row=table_header, column=20).font = header_font
        sheet.cell(row=table_header, column=20).border = top_bottom_border
        sheet.cell(row=table_header, column=21).font = header_font
        sheet.cell(row=table_header, column=21).border = top_bottom_border
        sheet.cell(row=table_header, column=22).font = header_font
        sheet.cell(row=table_header, column=22).border = top_bottom_border
        sheet.cell(row=table_header, column=22).alignment = right_alignment
        sheet.cell(row=table_header, column=23).font = header_font
        sheet.cell(row=table_header, column=23).border = top_bottom_border

        row_index=table_header+1
        for order in sale_order.filtered(lambda x:x.shipping_id.name and x.shipping_id.name.lower() != 'pick up'):

            product_volume = 0.0
            order_data = {}
            error_msg = ''
            order_data['order_name'] = order.name or ''
            order_data['state'] = dict((order._fields['state'].selection)).get(order.state)
            order_data['shipping_date'] = order.shipped_date.strftime("%d-%m-%Y") if order.shipped_date else ''
            invoice_id = order.invoice_ids.filtered(lambda r: r.state not in ['cancel'])
            order_data['total_amount'] = invoice_id.amount_total or 0
            order_data['total_amount'] = order.amount_total if order.state == 'shipped' else invoice_id.amount_total
            order_data['currency'] = order.currency_id.name or ''
            order_data['shipping_cost'] = order.amount_is_shipping_total or 0
            order_data['qty'] = order.delivered_qty or 0
            order_data['volume_param'] = order.order_line[0].product_id.volume_uom_name or ''
            order_data['weight_param'] = order.order_line[0].product_id.weight_uom_name or ''
            order_data['customer_id'] = order.partner_id.internal_id or ''
            order_data['partner'] = order.partner_id.name or ''
            order_data['salesperson'] = order.user_id.name or ''
            order_data['country'] = order.partner_id.country_id.name or ''
            order_data['city'] = order.partner_id.city
            order_data['zip'] = order.partner_id.zip
            order_data['address'] = '{},'.format(order.partner_id.street)+'{}'.format(order.partner_id.street2 or '')
            for pro_volume in order.order_line:
                product_volume = product_volume + round((pro_volume.product_id.length * pro_volume.product_id.width * pro_volume.product_id.height)/100,2)
            order_data['volume'] = round(product_volume,2)
            order_data['calculated_weight'] = round(order.weight_total_kg,2)
            order_data['actual_weight'] = round(order.actual_weight,2)
            order_data['carrier'] = order.picking_ids.filtered(lambda r:r.state not in ['cancel'] and 'WH/OUT' in r.name).shipping_id.name
            order_data['tracking_no'] = order.picking_ids.filtered(lambda r:r.state not in ['cancel'] and 'WH/OUT' in r.name).tracking_number_spt or ''
            if self.carrier_id:
                response = self.get_shipping_method(order)
                order_data['carrier_method'] = self.carrier_id.name or ''
                if response:
                    if not response['error_message'] and response['price'] != False and response['success'] == True:
                        order_data['calcu_shipping_cost'] = round(response['price'],2)
                        order_data['differ'] = abs(order_data['shipping_cost'] - order_data['calcu_shipping_cost']) if order_data['calcu_shipping_cost'] else 0.0
                    else:
                        order_data['calcu_shipping_cost'] = 'N\A'
                        order_data['differ'] = 0.0
                    if response.get('error_message'):
                        product_name = ',\n'.join(order.order_line.filtered(lambda x: not x.product_id.weight and not x.product_id.is_admin and not x.product_id.is_shipping_product and not x.product_id.is_global_discount).mapped('product_id.display_name'))
                        # FEDEX Api error.
                        if len(response['error_message'].split(':')) >= 3 and int(response['error_message'].split(':')[1][1:]) == 809:
                            if product_name:
                                error_msg += "These products have no Weight : \n" + product_name
                            undelivered_products = ',\n'.join(order.order_line.filtered(lambda x: not x.picked_qty and not x.product_id.is_admin and not x.product_id.is_shipping_product and not x.product_id.is_global_discount).mapped('product_id.display_name'))
                            if undelivered_products:
                                error_msg += "These products are not picked yet : \n" + undelivered_products
                            self.create_error_log(order,error_msg)
                            order_data['error'] = error_msg
                        elif len(response['error_message'].split(':')) >= 3 and (int(response['error_message'].split(':')[1][1:]) == 521 or int(response['error_message'].split(':')[1][1:]) == 522 or int(response['error_message'].split(':')[1][1:]) == 711 or int(response['error_message'].split(':')[1][1:]) == 868):
                            self.create_error_log(order,response.get('error_message'))
                            order_data['error'] = response['error_message'].split(':')[-1].strip() 
                        # UPS Api error.
                        elif 'missing field' in (response['error_message']).lower():
                            self.create_error_log(order,response.get('error_message').split('\n')[1][1:-1])
                            order_data['error'] = response.get('error_message').split('\n')[1][1:-1]
                        elif 'the estimated price cannot be computed because the weight of your product' in (response['error_message']).lower():
                            if order.order_line.filtered(lambda x: not x.product_id.weight and not x.product_id.is_admin and not x.product_id.is_shipping_product and not x.product_id.is_global_discount):
                                error_msg += "These products have no Weight : \n" + product_name
                            self.create_error_log(order,error_msg)
                            order_data['error'] = error_msg
                        elif 'the requested service is unavailable between the selected locations' in (response['error_message']).lower():
                            self.create_error_log(order,response.get('error_message').split(':')[1][1:])
                            order_data['error'] = response['error_message'].split(':')[1][1:]
                        else:
                            order_data['error'] = response.get('error_message')
                else:
                    order_data['calcu_shipping_cost'] = 'N\A'
                    order_data['differ'] = 0.0
            sheet.cell(row=row_index, column=1).value = order_data['shipping_date']
            sheet.cell(row=row_index, column=2).value = order_data['order_name']
            sheet.cell(row=row_index, column=3).value = order_data['state']
            sheet.cell(row=row_index, column=4).value = order_data['salesperson']
            sheet.cell(row=row_index, column=5).value = "{:,.2f}".format(order_data['total_amount']) or 0.0
            sheet.cell(row=row_index, column=5).alignment = right_alignment
            sheet.cell(row=row_index, column=6).value = order_data['currency']
            sheet.cell(row=row_index, column=6).alignment = right_alignment
            sheet.cell(row=row_index, column=7).value = order_data['qty']
            sheet.cell(row=row_index, column=7).alignment = left_alignment
            sheet.cell(row=row_index, column=8).value = order_data['volume'] or 0.0
            sheet.cell(row=row_index, column=8).alignment = left_alignment
            sheet.cell(row=row_index, column=9).value = order_data['actual_weight'] or 0.0
            sheet.cell(row=row_index, column=9).alignment = left_alignment
            sheet.cell(row=row_index, column=10).value = order_data['calculated_weight'] or 0.0
            sheet.cell(row=row_index, column=10).alignment = left_alignment
            sheet.cell(row=row_index, column=11).value = order_data['customer_id']
            sheet.cell(row=row_index, column=12).value = order_data['partner']
            sheet.cell(row=row_index, column=13).value = order_data['address'] or ''
            sheet.cell(row=row_index, column=13).alignment = left_alignment
            sheet.cell(row=row_index, column=14).value = order_data['city'] or ''
            sheet.cell(row=row_index, column=14).alignment = left_alignment
            sheet.cell(row=row_index, column=15).value = order_data['zip'] or ''
            sheet.cell(row=row_index, column=15).alignment = left_alignment
            sheet.cell(row=row_index, column=16).value = order_data['country']
            sheet.cell(row=row_index, column=16).alignment = left_alignment
            sheet.cell(row=row_index, column=17).value = order_data['carrier'] if order_data['carrier'] else "None"
            sheet.cell(row=row_index, column=18).value = order_data['tracking_no']
            sheet.cell(row=row_index, column=19).value = "{:,.2f}".format(order_data['shipping_cost']) or 0.0
            sheet.cell(row=row_index, column=19).alignment = right_alignment
            sheet.cell(row=row_index, column=20).value = order_data['carrier_method']
            sheet.cell(row=row_index, column=20).alignment = left_alignment
            sheet.cell(row=row_index, column=21).value = "{:,.2f}".format(order_data['calcu_shipping_cost']) if type(order_data['calcu_shipping_cost']) == float else order_data['calcu_shipping_cost']
            sheet.cell(row=row_index, column=21).alignment = right_alignment
            sheet.cell(row=row_index, column=22).value = "{:,.2f}".format(order_data['differ']) or 0.0
            sheet.cell(row=row_index, column=22).alignment = right_alignment
            sheet.cell(row=row_index, column=23).value = order_data.get('error')
            sheet.cell(row=row_index, column=23).alignment = left_alignment
            row_index += 1
        sheet.column_dimensions['A'].width = 15
        sheet.column_dimensions['B'].width = 15
        sheet.column_dimensions['C'].width = 15
        sheet.column_dimensions['D'].width = 25
        sheet.column_dimensions['E'].width = 15
        sheet.column_dimensions['F'].width = 15
        sheet.column_dimensions['G'].width = 15
        sheet.column_dimensions['H'].width = 15
        sheet.column_dimensions['I'].width = 20
        sheet.column_dimensions['J'].width = 24
        sheet.column_dimensions['K'].width = 25
        sheet.column_dimensions['L'].width = 25
        sheet.column_dimensions['M'].width = 30
        sheet.column_dimensions['N'].width = 15
        sheet.column_dimensions['O'].width = 15
        sheet.column_dimensions['P'].width = 15
        sheet.column_dimensions['Q'].width = 15
        sheet.column_dimensions['R'].width = 25
        sheet.column_dimensions['S'].width = 15
        sheet.column_dimensions['T'].width = 38
        sheet.column_dimensions['U'].width = 17
        sheet.column_dimensions['V'].width = 15
        sheet.column_dimensions['W'].width = 40
        
        fp = BytesIO()
        workbook.save(fp)
        fp.seek(0)
        data = fp.read()
        fp.close()
        self.file = base64.b64encode(data)
        return {
            'type': 'ir.actions.act_url',
            'url': 'web/content/?model=shipping.cost.analysis.wizard&download=true&field=file&id=%s&filename=%s.xlsx' % (self.id,f_name),
            'target': 'self',
        }

    def get_shipping_method(self,order):
        shipping_method = self.carrier_id
        res = False
        if shipping_method and hasattr(shipping_method, '%s_rate_shipment' % shipping_method.delivery_type.lower()):
            res = getattr(shipping_method, '%s_rate_shipment' % shipping_method.delivery_type.lower())(order)

        return res

    def create_error_log(self,order,error_msg):
        street = [order.partner_id.street if order.partner_id.street else '']
        address = street.extend([order.partner_id.street2 if order.partner_id.street2 else ''])
        vals = {'so_date':order.date_order,
                'sale_order':order.name,
                'customer_id':order.partner_id.internal_id,
                'customer_name':order.partner_id.name,
                'email':order.partner_id.email,
                'city':order.partner_id.city,
                'state_id':order.partner_id.state_id.id if order.partner_id.state_id else False,
                'postal_code':order.partner_id.zip,
                'country_id':order.partner_id.country_id.id if order.partner_id.country_id else False,
                'street':''.join(street),
                'shipping_method_id':self.carrier_id.id or '',
                'error':error_msg}
        self.env['kits.shipping.error.log'].create(vals)

    # def _get_postal_code(self,country,state,zip,city):
    #     address_obj = self.env['kits.country.data.import']
    #     if not zip:
    #         if city:
    #             zip = address_obj.search([('city','ilike',city)]).filtered(lambda x:x.city.lower() == city.lower()).zip
    #         elif state:
    #             state_id = address_obj.search([('state_id.name','ilike',state.name)])
    #             zip = state_id[0].zip
    #         elif country:
    #             url = "https://countriesnow.space/api/v0.1/countries/capital"
    #             response = requests.post(url,{"country": country.name})
    #             if response.json()['error'] is not True:
    #                 capital_state = address_obj.search([('state_id.name','ilike',response.json()['data']['capital'])])
    #                 if capital_state:
    #                     zip = capital_state[0].zip
    #     return zip
