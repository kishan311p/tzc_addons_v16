from odoo import models,fields,api,_
import base64
import xlsxwriter
import xlrd
from io import BytesIO

class import_order_lines_wizard_spt(models.TransientModel):
    _name = "import.order.lines.wizard.spt"
    _description = 'Import Order Lines Wizard'

    attached_file = fields.Binary("Attach File",required=True)
    attached_file_name = fields.Char("Attach File Name")
    so_id = fields.Many2one('sale.order',"Sale Id")
    readtime_error_file = fields.Binary("Read Error")
    
    order_line_ids = fields.Many2many("sale.order.line","import_order_lines_wizard_sale_order_line_rel","import_order_lines_wizard_id","sale_order_line_id","Order Lines")

    def action_process_file(self):
        sol_obj = self.env['sale.order.line']
        product_obj = self.env['product.product']
        sol_ids = []
        for record in self:
            products_dict = {}
            if record.attached_file:
                file_datas = base64.b64decode(record.attached_file)
                workbook = xlrd.open_workbook(file_contents=file_datas)
                sheet = workbook.sheet_by_index(0)
                file_data = [[sheet.cell_value(r,c) for c in range(sheet.ncols)] for r in range(sheet.nrows)]
                fields_dict = {'SKU':0,"QTY":0}
                # sale_order_vals={"partner_id":False,"product_ids":{}}
                error_lines= ["Error"]
                # countinue with product find and prepare sol line vals
                fields_list = file_data[0]
                [fields_dict.update({field:fields_list.index(field)}) for field in fields_list]
                file_data.pop(0)
                # last_line = file_data.pop(-1)
                for line in file_data:
                    try:
                        sku = fields_dict["SKU"] if str(fields_dict['SKU']) else False
                        qty = fields_dict["QTY"] if fields_dict["QTY"] and isinstance(fields_dict['QTY'],int) else False
                        product_id = False
                        product_qty = 0
                        if line[sku] and line[sku] not in (" ",'N/A',"n/a","","#N/A",):
                            sku = str(int(line[sku])) if isinstance(line[sku],int) or  isinstance(line[sku],float) else str(line[sku])
                            product_id = product_obj.search([("default_code",'=',sku)])
                            # product_id = product_obj.search([("barcode",'=',barcode)])
                            if not product_id:
                                error_lines.append("Product with code %s not found in Odoo."%(sku))
                
                        #read time qty > 0
                        if qty and line[qty] and line[qty] > 0:
                            product_qty = line[qty]
                        if product_id and product_qty:
                            if product_id in products_dict:
                                products_dict[product_id]['product_uom_qty'] += product_qty
                            else:
                                products_dict[product_id] = {'product_id':product_id.id,'sale_type': product_id.sale_type,'product_uom_qty':product_qty,"name":product_id.name,'price_unit':product_id.lst_price,"order_id":record.so_id.id}

                    except Exception as e:
                        error_lines.append(str(e))
                        print(str(e))
          
            #create order lines
            products_list = list(products_dict)
            if products_list and len(products_list) > 0 and len(error_lines) == 1:
                for product in products_list:
                    sol_id = sol_obj.search([('product_id','=',products_dict[product]['product_id']),('product_uom_qty','=',products_dict[product]['product_uom_qty']),('order_id','=',False)])
                    if sol_id and sol_id.id:
                        sol_id.write(products_dict[product])
                    else:
                        sol_id = sol_obj.search([('product_id','=',products_dict[product]['product_id']),('order_id','=',record.so_id.id)])
                        if sol_id and sol_id.id:
                            sol_id.write(products_dict[product])
                        else:
                            sol_id = sol_obj.create(products_dict[product])
                        sol_id.product_id_change()
                        sol_id.product_uom_change()
                    try:
                        sol_ids.append(sol_id.id)
                    except Exception as e:
                        error_lines.append(str(e))
            # return error file
            record.readtime_error_file = False
            if len(error_lines) > 1:
                out = BytesIO()
                workbook = xlsxwriter.Workbook(out) 
                worksheet = workbook.add_worksheet('wrong')
                heading_line = error_lines.pop(0)
                col = row =0
                worksheet.write(row,col,heading_line)
                worksheet.set_column(row,col, len(heading_line)*10)
                col+=1
                for worksheet_line in error_lines:
                    row +=1
                    col = 0
                    worksheet.write(row,col,worksheet_line)
                workbook.close()
                out.seek(0)
                data = out.read()
                out.close()
                file_name = "Import Error %s"%(record.so_id.name)
                record.readtime_error_file = base64.b64encode(data)
            if record.readtime_error_file:
                return {
                    'type': 'ir.actions.act_url',
                    'url': 'web/content/?model=import.order.lines.wizard.spt&download=true&field=readtime_error_file&id=%s&filename=%s.xlsx' % (record.id, file_name),
                    'target': 'self',
                    }
