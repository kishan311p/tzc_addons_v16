from odoo import fields,models,api,_
import xlsxwriter
from io import BytesIO
import base64



class kits_b2c_sales_report(models.TransientModel):
    _name = 'kits.b2c.sales.report'
    _description = 'sales report'
    
    country_ids = fields.Many2many('res.country', string='Countries')
    sku = fields.Char('SKU')
    brand_ids = fields.Many2many('product.brand.spt', string='Brands')
    start_date = fields.Date('From')
    end_date = fields.Date('To')
    report_file = fields.Binary('File')
    product_type = fields.Selection([('e','Eyeglass'),('s','Sunglass')],'Product Type')
    website_ids = fields.Many2many('kits.b2c.website', string='Website')

    def print_report_excel(self):
        f_name = 'Sale Report'
        out = BytesIO()
        workbook = xlsxwriter.Workbook(out) 
        worksheet = workbook.add_worksheet('Report')
        cell_format = workbook.add_format({'bold': True,'border':1})
        price_cell_format = workbook.add_format({'bold': True,'border':1,'align': 'right'})
        merge_format = workbook.add_format({'bold': 1,'align': 'center','valign': 'vcenter',})
        cell_merge_format = workbook.add_format({'align': 'left','valign': 'vcenter',})
        worksheet.set_column('A:A', 35)
        worksheet.set_column('B:B', 15)
        worksheet.set_column('C:C', 20)
        worksheet.set_column('D:D', 20)
        worksheet.write(0,0,'Product',cell_format)
        worksheet.write(0,1,"Quantity",price_cell_format)
        worksheet.write(0,2,"Average Unti Price",price_cell_format)
        worksheet.write(0,3,"Brand",cell_format)
        worksheet.write(0,4,"Orders",cell_format)
        data = self.calculate_datas()
        row = 0
        for key in data:
            row +=1
            worksheet.write(row,0,key)
            worksheet.write(row,1,data[key]['qty'])
            worksheet.write(row,2,data[key]['price'])
            worksheet.write(row,3,data[key]['brand'])
            worksheet.write(row,4,data[key]['name'])

        workbook.close()
        out.seek(0)
        data = out.read()
        out.close()
        self.report_file = base64.b64encode(data)
        return{
                'type': 'ir.actions.act_url',
                'url': 'web/content/?model=kits.b2c.sales.report&download=true&field=report_file&id=%s&filename=%s' % (self.id, f_name),
                'target': 'self',
            }
    
    def print_report_pdf(self):
        return self.env.ref('kits_multi_website.action_report_kits_b2c_sales_report').report_action(self.id)
        
    def calculate_datas(self):
        data = {}
        domain=[('state','not in',['cancel'])]
        self.ensure_one()
        if self.website_ids:
            domain.append(('website_id','in',self.website_ids.ids))
        if self.country_ids:
            domain.append(('sale_order_id.customer_id.country_id','in',self.country_ids.ids))
        if self.sku:
            domain.append(('product_id.default_code','in',self.sku.split(',')))
        if self.brand_ids:
            domain.append(('product_id.brand','in',self.brand_ids.ids))
        if self.start_date:
            domain.append(('sale_order_id.create_date','>=',fields.Date.to_string(self.start_date)))
        if self.end_date:
            domain.append(('sale_order_id.create_date','<=',fields.Date.to_string(self.end_date)))
        if self.product_type:
            if self.product_type == 'e':
                domain.append(('product_id.categ_id.name','in',['e','E','Eyeglasses','Eyeglas']))
            if self.product_type == 's':
                domain.append(('product_id.categ_id.name','in',['s','S','Sunglasses','Sunglas']))
        lines=self.env['kits.multi.website.sale.order.line'].search(domain,order='name')
        for line in lines:
            if line.product_id.type == 'product':
                if line.product_id.display_name in data.keys():
                    key = line.product_id.display_name
                    data[key]['qty'].append(line.quantity) 
                    data[key]['name'].append(line.sale_order_id.name) 
                    data[key]['price'].append(line.subtotal/line.quantity) 
                else:
                    data[line.product_id.display_name] = {'qty':[line.quantity],'brand':line.product_id.brand.name,'name':[line.sale_order_id.name],'price':[line.subtotal/line.quantity]}
        for key in data:
            data[key]['qty'] = sum(data[key]['qty'])
            data[key]['name'] = ','.join(set(data[key]['name'])) 
            data[key]['price'] = round((sum(data[key]['price'])/len(data[key]['price'])) ,2)
        return data