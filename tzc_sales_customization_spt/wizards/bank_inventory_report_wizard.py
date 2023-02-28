from odoo import models, fields, api, _
import calendar
from datetime import datetime, timedelta
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Border, Side, Alignment, Protection, Font
import base64
from io import BytesIO
from dateutil import tz
from odoo.exceptions import UserError

class bank_inventory_report_wizard(models.TransientModel):
    _name = "bank.inventory.report.wizard"
    _description = 'Bank Inventory Report Wizard'

    years = {'2015':'2015'}

    def _get_years(self):
        last = max(self.years.keys())
        current = datetime.now().year
        if int(last) < current:
            self.years.update(dict([[str(i),str(i)] for i in range(int(last)+1,current+1)]))
        return [(year,year) for year in self.years]

    start_month = fields.Selection([('1', 'Jan'), ('2', 'Feb'), ('3', 'March'), ('4', 'April'), ('5', 'May'), ('6', 'Jun'), (
        '7', 'July'), ('8', 'Aug'), ('9', 'Sep'), ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dec')], string="Month From", required=True)
    end_month = fields.Selection([('1', 'Jan'), ('2', 'Feb'), ('3', 'March'), ('4', 'April'), ('5', 'May'), ('6', 'Jun'), (
        '7', 'July'), ('8', 'Aug'), ('9', 'Sep'), ('10', 'Oct'), ('11', 'Nov'), ('12', 'Dec')], string="Month To", required=True)
    start_year = fields.Selection(_get_years,"Year From", required=True)
    end_year = fields.Selection(_get_years,"Year To", required=True)
    file = fields.Binary()

    def action_print_report_file(self):
        product_obj = self.env['product.product']
        sol_obj = self.env['sale.order.line']
        header = ['NAME', 'SKU', 'Brand', 'MODEL', 'CATEGORY','USD PRICE']
        if not (int(self.start_year) == datetime.now().year and int(self.start_month) == datetime.now().month ) and (not (self.start_month,self.start_year) > (self.end_month,self.end_year)):
            last_start_date = calendar.monthrange(
                int(self.start_year), int(self.start_month))[1]
            last_end_date = calendar.monthrange(
                int(self.end_month), int(self.end_month))[1]
            start = '%s-%s-01' % (self.start_year,self.start_month)
            end = '%s-%s-01' % (self.end_year, self.end_month)
            months = [i.strftime("%b-%Y")
                      for i in pd.date_range(start=start, end=end, freq='MS')]
            f_name = 'Inventory Bank Report'  # FileName
            header.extend(months)
            lines = []
            product_ids = product_obj.search([])
            active_id = self.id
            time_format = "%Y%b%d%H:%M:%S"
            tz_from, tz_to = tz.gettz(datetime.now().tzinfo), (tz.gettz(self.env.user.tz))
            end_date = datetime.now().replace(tzinfo=tz_from).astimezone(tz=tz_to)
            for product in product_ids:
                now_date = datetime.now().date()
                name = product.name_get()
                # name = product.variant_name
                sku = product.default_code
                brand = product.brand.name
                model = product.model.name
                category = product.categ_id.name
                # cad_price = product.lst_price
                usd_price = product.lst_price
                on_hand = product.qty_available
                line_data = [name[0][1], sku, brand, model, category, usd_price]
                months_on_hand = []
                for month in months:
                    total_delivered = 0.00
                    long_month_name = month.split('-')[0]
                    m = datetime.strptime(long_month_name, "%b").month
                    year = month.split('-')[1]
                    date_str = str(year)+long_month_name+str(calendar.monthrange(int(year), m)[1])+"23:59:00"
                    on_date = datetime.strptime(''.join(date_str), time_format)
                    start_date = on_date.replace(tzinfo=tz_from).astimezone(tz=tz_to)
                    query = f"""SELECT COALESCE(SUM(SOL.QTY_DELIVERED),0)
                                FROM SALE_ORDER_LINE SOL
                                LEFT JOIN PRODUCT_PRODUCT PP ON SOL.PRODUCT_ID = PP.ID
                                WHERE SOL.CREATE_DATE BETWEEN '{start_date}' AND '{end_date}'
                                    AND SOL.PRODUCT_ID = {product.id}"""
                    self._cr.execute(query)
                    try:
                        result = self._cr.fetchall()[0]
                        total_delivered = result[0]
                        total_delivered = float(total_delivered)
                    except:
                        total_delivered = 0.00
                    total_delivered += on_hand
                    months_on_hand.append(total_delivered)
                    print(total_delivered, on_hand)
                line_data.extend(months_on_hand)
                lines.append(line_data)

            df = pd.DataFrame(lines, columns=header)
            # writer = pd.ExcelWriter('sample.xlsx', engine='xlsxwriter')
            io_obj = BytesIO()
            df.to_excel(io_obj, index=False, sheet_name="Products")
            io_obj.seek(0)
            data = io_obj.read()
            io_obj.close()
            self.file = base64.b64encode(data)
            return {
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=bank.inventory.report.wizard&download=true&field=file&id=%s&filename=%s.xlsx' % (active_id, f_name),
                'target': 'self',
            }
        else:
            raise UserError(_('Please check values..'))
