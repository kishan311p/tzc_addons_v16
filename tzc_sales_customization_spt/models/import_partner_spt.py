# -*- coding: utf-8 -*-
# Part of SnepTech See LICENSE file for full copyright and licensing details.##
##############################################################################
from odoo.exceptions import UserError
from odoo import models, fields, api, _
from io import BytesIO
import base64
import xlrd
import xlsxwriter

class import_partner_spt(models.Model):
    _name = 'import.partner.spt'
    _description = 'Import Partners'

    name = fields.Char('Name', default='New')
    create_date = fields.Datetime('Date',readonly="1")

    attach_file = fields.Binary("Attached File",readonly=True, states={'draft': [('readonly', False)]})
    attach_file_name = fields.Char("Attached File Name")
    
    run_time_file_name = fields.Char("Run Time File Name")
    run_time = fields.Binary("Run Time Error",default='')
    state = fields.Selection([
        ('draft','Draft'),
        ('done','Done'),
    ], string='State', default='draft')
    partner_ids = fields.Many2many('res.partner','import_partner_model_real','import_id','partner_id','Partners')
    number_of_partner = fields.Integer('Number Of Partners', compute='_get_number_of_partner')
    
    data_on = fields.Selection([
        ('create','Create'),
        ('update','Update'),  
    ],readonly=True, states={'draft': [('readonly', False)]}, string='Operation',required=True,default="create")
    
    
    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('import.partner.spt') or 'New'
        return super(import_partner_spt, self).create(vals)

    
    def _get_number_of_partner(self):
        for record in self:
            record.number_of_partner = len(record.partner_ids)

    
    def action_view_partner(self):
        self.ensure_one()
        try:
            list_view = self.env.ref('base.view_partner_tree')
            form_view = self.env.ref('base.view_partner_form')
        except ValueError:
            list_view = False
            form_view = False
        return {
            'name': 'Contacts',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'res.partner',
            'view_id': False,
            'views': [(list_view.id, 'tree'),(form_view.id, 'form')],
            'type': 'ir.actions.act_window',
            'target':'current',
            'domain':[('id','in',self.partner_ids.ids)],
        }   

    def process_spt(self):
        # catalog_obj = self.env['sale.catalog']
        # catalog_obj.connect_server()
        # method = catalog_obj.get_method('process_spt')
        # if method['method']:
        #     localdict = {'self':self,'base64':base64,'xlrd':xlrd,'UserError':UserError,'_':_,}
        #     exec(method['method'], localdict)
        # record = localdict['record']
        partner_obj = self.env['res.partner']
        for record in self:
            check_header = ''
            partner_list = []
            wrong_lines =[]
            index_heading_dict = {}
            fields_dict = {
            'Name' : 'name','Internal ID' : 'internal_id',
            'Phone' : 'phone','Mobile' : 'mobile','Street1' : 'street','Street2' : 'street2',
            'Email' : 'email','Is Company' : 'is_company','State' : 'state_id','City' : 'city',
            'Zip' : 'zip_code','Country' : 'country_id','Is Customer' : 'customer_rank','Is Vendor' : 'supplier_rank',
            'Sales Person' : 'user_id','Website' : 'website','Total Sales' : 'previous_total_sales',
            'Internal Flag' : 'internal_flag','Is ETO' : 'eto','Customer Sales Rank' : 'customer_sales_rank',
            'Business Type' : 'business_type_ids',  
            }
            if record.attach_file:
                file_datas = base64.b64decode(record.attach_file)
                workbook = xlrd.open_workbook(file_contents =file_datas) 
                sheet = workbook.sheet_by_index(0)
                file_data = [[sheet.cell_value(r, c) for c in range(
                sheet.ncols)] for r in range(sheet.nrows)]
                heading = file_data.pop(0)
                for heading_data in heading:
                    if heading_data not in fields_dict.keys():
                        check_header = check_header+','+heading_data 
                if check_header:
                    raise UserError(_('Incorrect %s headers found,first remove headers then process will be done.'%(check_header[1:])))

                [index_heading_dict.update({fields_dict[col] : heading.index(col)}) for col in heading if col in fields_dict.keys()]
                heading.append('Error')
                wrong_lines.append(heading)
                if 'Internal ID' not in heading:
                    raise UserError(_('Please enter internal id in sheet.'))
                
                for line in file_data:
                    partner_id = partner_obj.search([('internal_id','=',str(line[index_heading_dict['internal_id']]).strip())])
                    if not partner_id :
                        if 'Name' not in heading:
                            raise UserError(_('Please enter partner name in sheet.'))
                        else:
                            partner_id = partner_obj.create({'name':line[index_heading_dict['name']].strip(),'internal_id':str(line[index_heading_dict['internal_id']]).strip(),'user_id':self.env.uid})
                            partner_list.append(partner_id.id)
                            print(partner_id.name)
                self.update_partners(index_heading_dict,file_data,wrong_lines,partner_list) 
                # partner_list = localdict['partner_list']
                # wrong_lines = localdict['wrong_lines']
            if record:       
                record.partner_ids = [(6,0,list(set(partner_list)))]
                record.run_time_file_name = ''
                record.run_time = False
                if len(wrong_lines) > 1:
                    out = BytesIO()
                    workbook = xlsxwriter.Workbook(out) 
                    worksheet = workbook.add_worksheet('contacts')
                    col = row =0
                    heading = wrong_lines.pop(0)
                    for heading_data in heading:
                        worksheet.write(row,col,heading_data)
                        worksheet.set_column(row,col, len(heading_data)*10)

                        col+=1
                    for worksheet_line in wrong_lines:
                        row +=1
                        col = 0
                        for worksheet_line_data in worksheet_line:
                            worksheet.write(row,col,worksheet_line_data)
                            col +=1

                    workbook.close()
                    out.seek(0)
                    data = out.read()
                    out.close()
                    record.run_time_file_name = 'Wrong Contact.xlsx'
                    record.run_time = base64.b64encode(data)
                record.state = 'done'

    def update_partners(self,index_heading_dict={},file_data=[],wrong_lines=[],partner_list=[]):
        # catalog_obj = self.env['sale.catalog']
        # catalog_obj.connect_server()
        # method = catalog_obj.get_method('update_partners')
        # if method['method']:
        #     localdict = {'self':self,'index_heading_dict':index_heading_dict,'file_data': file_data,'wrong_lines': wrong_lines,'partner_list':partner_list,'base64':base64,'xlrd':xlrd,'UserError':UserError,'_':_,}
        #     exec(method['method'], localdict)

        partner_obj = self.env['res.partner']
        state_obj = self.env['res.country.state']
        country_obj = self.env['res.country']
        user_obj = self.env['res.users']
        business_type_obj = self.env['business.type.spt']
        internal_flag_obj = self.env['internal.flag.spt']
        for line in file_data:
            try:
                print(str(file_data.index(line))+':'+str(line[index_heading_dict['internal_id']]))
                name=''
                if 'name' in index_heading_dict.keys() and line[index_heading_dict['name']] not in ['n/a','N/A']:
                    name = str(line[index_heading_dict['name']].strip())
                internal_id=''
                if 'internal_id' in index_heading_dict.keys() and line[index_heading_dict['internal_id']] not in ['n/a','N/A']:
                    internal_id = str(line[index_heading_dict['internal_id']].strip())
                parent_id= False
                
                phone=''
                if 'phone' in index_heading_dict.keys() and line[index_heading_dict['phone']] not in ['n/a','N/A']:
                    phone = line[index_heading_dict['phone']]
                    phone = str(int(phone)) if isinstance(phone,float) else str(phone) 
                    phone = str(line[index_heading_dict['phone']]).strip()
                mobile=''
                if 'mobile' in index_heading_dict.keys() and line[index_heading_dict['mobile']] not in ['n/a','N/A']:
                    mobile = line[index_heading_dict['mobile']]
                    mobile = str(int(mobile)) if isinstance(mobile,float) else str(mobile) 
                    mobile = str(line[index_heading_dict['mobile']]).strip()
                street=''
                if 'street' in index_heading_dict.keys() and line[index_heading_dict['street']] not in ['n/a','N/A']:
                    street = str(line[index_heading_dict['street']].strip())
                street2=''
                if 'street2' in index_heading_dict.keys() and line[index_heading_dict['street2']] not in ['n/a','N/A']:
                    street2 = str(line[index_heading_dict['street2']].strip())
                email=''
                if 'email' in index_heading_dict.keys() and line[index_heading_dict['email']] not in ['n/a','N/A']:
                    email = str(line[index_heading_dict['email']].strip())
                is_company= False
                if 'is_company' in index_heading_dict.keys() and line[index_heading_dict['is_company']] not in ['n/a','N/A']:
                    if  line[index_heading_dict['is_company']] == 1:
                        is_company = True
                state_id= False
                if 'state_id' in index_heading_dict.keys() and line[index_heading_dict['state_id']] not in ['n/a','N/A']:
                    state_id = state_obj.search([('name','=', line[index_heading_dict['state_id']].strip())])
                    if state_id:
                        state_id = state_id.id                           
                city=''
                if 'city' in index_heading_dict.keys() and line[index_heading_dict['city']] not in ['n/a','N/A']:
                    city = str(line[index_heading_dict['city']].strip())
                zip_code=''
                if 'zip_code' in index_heading_dict.keys() and line[index_heading_dict['zip_code']] not in ['n/a','N/A']:
                    zip_code = line[index_heading_dict['zip_code']]
                    zip_code = str(int(zip_code)) if isinstance(zip_code,float) else str(zip_code) 
                    zip_code = str(line[index_heading_dict['zip_code']]).strip()
                country_id= False
                if 'country_id' in index_heading_dict.keys() and line[index_heading_dict['country_id']] not in ['n/a','N/A']:
                    country_id = country_obj.search([('name','=', line[index_heading_dict['country_id']].strip())])
                    if country_id:
                        country_id = country_id.id 
                    else:
                        line.append('Country is not in system first create then update line.')
                customer_rank= 0
                if 'customer_rank' in index_heading_dict.keys() and line[index_heading_dict['customer_rank']] not in ['n/a','N/A']:
                    if line[index_heading_dict['customer_rank']] ==1:
                        context_dict = {}
                        context_dict.update(partner_obj._context)
                        context_dict['res_partner_search_mode'] = 'customer'
                        partner_obj.env.context = context_dict
                        customer_rank = 1
                supplier_rank= 0
                if 'supplier_rank' in index_heading_dict.keys() and line[index_heading_dict['supplier_rank']] not in ['n/a','N/A']:
                    if line[index_heading_dict['supplier_rank']] ==1:
                        context_dict = {}
                        context_dict.update(partner_obj._context)
                        context_dict['res_partner_search_mode'] = 'supplier'
                        partner_obj.env.context = context_dict
                        supplier_rank = 1
                user_id= False
                user_ids = []
                if 'user_id' in index_heading_dict.keys() and line[index_heading_dict['user_id']] not in ['n/a','N/A']:
                    user_id = user_obj.search([('name','=', line[index_heading_dict['user_id']].strip())])
                    if user_id:
                        user_id = user_id.id
                        user_ids.append(user_id)
                    else:
                        line.append('User is not in system first create then update line.')
                website= ''
                if 'website' in index_heading_dict.keys() and line[index_heading_dict['website']] not in ['n/a','N/A']:
                    website = str(line[index_heading_dict['website']].strip())
                previous_total_sales=0.0
                if 'previous_total_sales' in index_heading_dict.keys() and isinstance(line[index_heading_dict['previous_total_sales']],float) and line[index_heading_dict['previous_total_sales']] not in ['n/a','N/A']:
                    previous_total_sales = float(line[index_heading_dict['previous_total_sales']])
                internal_flag_id=''
                if 'internal_flag_id' in index_heading_dict.keys() and line[index_heading_dict['internal_flag_id']] not in ['n/a','N/A']:
                    internal_flag_id = internal_flag_obj.search([('name','=',line[index_heading_dict['internal_flag_id']].strip())])
                    if internal_flag_id:
                        internal_flag_id = internal_flag_id.id
                    else:
                        internal_flag_id = internal_flag_obj.create({'name':line[index_heading_dict['internal_flag_id']].strip()})
                        internal_flag_id = internal_flag_id.id
                eto=''        
                if 'eto' in index_heading_dict.keys() and line[index_heading_dict['eto']] not in ['n/a','N/A']:
                    if line[index_heading_dict['eto']].strip().lower() == 'fs':
                        eto = 'fs'
                    elif line[index_heading_dict['eto']].strip().lower() == 'reg' or line[index_heading_dict['eto']].strip().lower() == 'registered':
                        eto = 'registered'
                    else:
                        line.append('ETO field data check first then update line.')
                customer_sales_rank= 0
                if 'customer_sales_rank' in index_heading_dict.keys() and line[index_heading_dict['customer_sales_rank']] not in ['n/a','N/A']:
                    customer_sales_rank = float(line[index_heading_dict['customer_sales_rank']])
                business_type_ids=[]
                if 'business_type_ids' in index_heading_dict.keys() and line[index_heading_dict['business_type_ids']] not in ['n/a','N/A']:
                    for business_type in line[index_heading_dict['business_type_ids']].strip().split('|'):
                        business_type_id = business_type_obj.search([('name','=',business_type.strip())])
                        if business_type_id:
                            business_type_ids.append(business_type_id.id)
                        else:
                            business_type_id = business_type_obj.create({'name': business_type.strip()})
                            business_type_ids.append(business_type_id.id)
                    if business_type_ids:
                        business_type_ids = business_type_ids
                partner_dict = {
                    'name': name if name else None,
                    'internal_id': internal_id if internal_id else None,
                    # 'parent_id': parent_id if parent_id else None,
                    'phone': phone if phone else None,
                    'mobile': mobile if mobile else None,
                    'street': street if street else None,
                    'street2': street2 if street2 else None,
                    'email': email if email else None,
                    'is_company': is_company if is_company else None,
                    'state_id': state_id if state_id else None,

                'city': city if city else None,
                    'zip': zip_code if zip_code else None,
                    'country_id': country_id if country_id else None,
                    'customer_rank': customer_rank if customer_rank else None,
                    'supplier_rank': supplier_rank if supplier_rank else None,
                    'user_id': user_id if user_id else None,
                    # 'user_ids': [(6,0,user_ids)] if user_ids else [] ,
                    # 'website': website if website else None,
                    'previous_total_sales': previous_total_sales if previous_total_sales else None,
                    'internal_flag_id': internal_flag_id if internal_flag_id else None,
                    'eto': eto if eto else None,
                    'customer_sales_rank': customer_sales_rank if customer_sales_rank else None,
                    'business_type_ids': [(6,0,business_type_ids)] if business_type_ids else None,
                }
                partner_id = partner_obj.search([('internal_id','=',line[index_heading_dict['internal_id']].strip())])
                if len(wrong_lines[0]) <= len(line) :
                    wrong_lines.append(line)
                else:
                    if partner_id:
                        partner_id.ensure_one()
                        if partner_dict['country_id']:
                            pricelist = self.env.ref('tzc_sales_customization_spt.usd_public_pricelist_spt')
                            if  country_obj.browse(partner_dict['country_id']).name == 'Canada':
                                pricelist = self.env.ref('product.list0')
                            partner_dict['property_product_pricelist'] = pricelist.id
                        for field_data in list(partner_dict.keys()):
                            if partner_dict[field_data] == None and field_data not in list(index_heading_dict.keys()):
                                del partner_dict[field_data]
                        
                        partner_id.write(partner_dict)
                        partner_list.append(partner_id.id)
                    else:
                        line.append('Partner not found.')
                

            except Exception as e:
                error = str(e)
                if error[2:12] == 'This email' and partner_id:
                    partner_id.email = None 
                    error = str(e)[2:-6]
                if '(' in error:
                        error = error.replace('(','')
                if ')' in error:
                        error = error.replace(')','')
                line.append(error)
                wrong_lines.append(line)
