# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import base64
import requests
import json
from werkzeug.urls import url_encode
from datetime import datetime,timedelta
from datetime import date
from lxml import etree

class SaleCatalog(models.Model):
    _name = 'sale.catalog'
    _description = 'Catalog'
    _inherit = ['mail.thread','mail.activity.mixin','portal.mixin']
    _order = 'id desc'

    name = fields.Char('Name',required=True, copy=False)
    description = fields.Text('Description   ',states={'draft': [('readonly', False)]},copy=True,default="An exclusive eyewear catalog has been created for you. Click on the View Catalog button below to view the entire catalog.")
    description_1 = fields.Text(' Description',states={'draft': [('readonly', False)]})
    description_2 = fields.Text('Description ',states={'draft': [('readonly', False)]})
    line_ids = fields.One2many('sale.catalog.line', 'catalog_id', states={'draft': [('readonly', False)]},copy=True,string='Catalog Lines')
    order_ids = fields.One2many('sale.order', 'catalog_id',states={'draft': [('readonly', False)]},copy=False, string='Sale Orders')
    sale_order_count = fields.Integer(compute='_get_sale_order_count',store=True,compute_sudo=True)
    sale_order_ids = fields.One2many('sale.order','catalog_id',string="Orders")
    pending_catalog_count = fields.Integer(compute='_get_pending_catalog_count',store=True,compute_sudo=True)
    catalog_sent_count = fields.Integer(compute='_get_pending_catalog_count',store=True,compute_sudo=True)
    # pending_catalog_ids = fields.One2many('pending.catalog.spt','catalog_id','Pending Catalogs')
    customer_count = fields.Integer(compute='_get_customer_count',store=True)
    partner_ids = fields.Many2many('res.partner', string='Customers',copy=True)
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    active = fields.Boolean('Active', default=True,copy=True)
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('validate', 'Validate'),
            ('manage_qtys', 'Stock Validated'),
            ('pending', 'Pending'),
            ('done', 'Done'),
            ('cancel', 'Cancel'),
        ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    send_out = fields.Datetime('Send Out')
    user_id = fields.Many2one('res.users', string='Responsible', required=False, default=lambda self: self.env.user)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist')
    catalog_total = fields.Char(string="Total Amount",compute='_compute_catalog_total',store=True)
    expiry_date = fields.Date(string="Expiry Date")
    visitors = fields.Integer('#Visitors',compute='_get_visitors',store=True,compute_sudo=True)
    # visitor_ids = fields.One2many('catalog.visitors.spt','catalog_id','Visitors')
    base_on_qty = fields.Selection(selection=[
            ('available_qty', 'Available QTY'),
            ('total_qty', 'On Hand QTY'),
            ('allow_out_of_stock', 'Allow Out Of Stock'),
        ], string='Based On' , tracking=True,
        default='available_qty')
    cron_interval_time = fields.Integer(compute='compute_get_interval_time',compute_sudo=True)
    cron_interval_type = fields.Char(compute='compute_get_interval_time',compute_sudo=True)
    accept_decline_flag = fields.Boolean('Accept/Decline Flag')
    execution_time = fields.Datetime('Execution Time')
    customer_id = fields.Many2one('res.partner')

    @api.onchange('user_id')
    def _onchange_get_manager(self):
        for rec in self:
            partner_ids = self.env['res.partner'].search([('user_id','=',rec.user_id.id),('customer_type','=','b2b_regular'),('active','=',True)])
            rec.partner_ids = [(6,0,partner_ids.mapped('id'))]

    @api.onchange('user_id')
    def _onchange_partner_ids(self):
        partner_ids = []
        if self.user_id:
            partner_ids = self.user_id.get_filtere_contact().ids

        return {'domain':{'partner_ids':[('id','in',partner_ids)]}}

    def compute_get_interval_time(self):
        for rec in self:
            rec.cron_interval_time = False
            rec.cron_interval_type = ''
            cron_id = self.env.ref('tzc_sales_customization_spt.ir_cron_send_pendding_catalog_spt')
            if cron_id:
                rec.cron_interval_time = cron_id.interval_number
                rec.cron_interval_type = dict(cron_id._fields['interval_type'].selection).get(cron_id.interval_type)

    # @api.depends('visitor_ids','visitor_ids.visits')
    # def _get_visitors(self):
    #     # visitors_obj = self.env['catalog.visitors.spt']
    #     for rec in self:
    #         rec.visitors = sum(self.visitor_ids.mapped('visits'))
    #         # visitor_ids = visitors_obj.search([('catalog_id','=',rec.id),('visits','>',0)])
    #         # visit += sum([visit.visits for visit in visitor_ids])
    #         # rec.visitors = visit

    @api.depends('line_ids','line_ids.product_price','line_ids.product_qty','line_ids.price_subtotal','pricelist_id','pricelist_id.currency_id','pricelist_id.currency_id.name','pricelist_id.currency_id.symbol')
    def _compute_catalog_total(self):
        for record in self:
            total = ''
            if record.pricelist_id and record.pricelist_id.currency_id:
                total = total + '('+record.pricelist_id.currency_id.name+') ' + str(record.pricelist_id.currency_id.symbol)+" "
            total = total + str(round(sum(record.line_ids.mapped('price_subtotal')),2))
            record.catalog_total = total

    @api.depends('partner_ids')
    def _get_customer_count(self):
        for record in self:
            record.customer_count = len(record.partner_ids)

    @api.onchange('pricelist_id')
    def _onchange_pricelist_id(self):
        pricelist_obj = self.env['product.pricelist.item']
        for record in self:
           for line in record.line_ids:
                product_price = line .product_pro_id.lst_price
                pricelist_item_id = pricelist_obj.search([('product_id','=',line.product_pro_id.id),('pricelist_id','=',record.pricelist_id.id)],limit=1)
                line.product_price = pricelist_item_id.fixed_price or product_price
                line.product_price_msrp = line.product_pro_id.price_msrp
                line.product_price_wholesale = line.product_pro_id.price_wholesale
                line.unit_discount_price = line.product_pro_id.lst_price
                if line.sale_type:
                    if line.sale_type == 'on_sale':
                        line.unit_discount_price = line.product_pro_id.on_sale_usd
                    else:
                        line.unit_discount_price = line.product_pro_id.clearance_usd

                if line.discount:
                    line.unit_discount_price = line.product_price - (line.product_price * line.discount) * 0.01
                
                active_inflation = self.env['kits.inflation'].search([('is_active','=',True)])
                inflation_rule_ids = self.env['kits.inflation.rule'].search([('country_id','in',self.env.user.country_id.ids),('brand_ids','in',line.product_pro_id.brand.ids),('inflation_id','=',active_inflation.id)])
                inflation_rule = inflation_rule_ids[-1] if inflation_rule_ids else False
                if inflation_rule:
                    is_inflation = False
                    if active_inflation.from_date and active_inflation.to_date :
                        if active_inflation.from_date <= datetime.now().date() and active_inflation.to_date >= datetime.now().date():
                            is_inflation = True
                    elif active_inflation.from_date:
                        if active_inflation.from_date <= datetime.now().date():
                            is_inflation = True
                    elif active_inflation.to_date:
                        if active_inflation.to_date >= datetime.now().date():
                            is_inflation = True
                    else:
                        if not active_inflation.from_date:
                            is_inflation = True
                        if not active_inflation.to_date:
                            is_inflation = True
                        
                    if is_inflation:
                        line.product_price = round(product_price+(product_price*inflation_rule.inflation_rate /100),2)
                        line.unit_discount_price = round(line.unit_discount_price+(line.unit_discount_price*inflation_rule.inflation_rate /100),2)
                        line.product_price_msrp = round(line.product_price_msrp+(line.product_price_msrp*inflation_rule.inflation_rate /100),2)
                        line.product_price_wholesale = round(line.product_price_wholesale+(line.product_price_wholesale*inflation_rule.inflation_rate /100),2)

                active_fest_id = self.env['tzc.fest.discount'].search([('is_active','=',True)])
                special_disocunt_id = self.env['kits.special.discount'].search([('country_id','in',self.env.user.partner_id.country_id.ids),('brand_ids','in',line.product_pro_id.brand.ids),('tzc_fest_id','=',active_fest_id.id)])
                price_rule_id = special_disocunt_id[-1] if special_disocunt_id else False
                if price_rule_id:
                    applicable = False
                    if active_fest_id.from_date and active_fest_id.to_date :
                        if active_fest_id.from_date <= datetime.now().date() and active_fest_id.to_date >= datetime.now().date():
                            applicable = True
                    elif active_fest_id.from_date:
                        if active_fest_id.from_date <= datetime.now().date():
                            applicable = True
                    elif active_fest_id.to_date:
                        if active_fest_id.to_date >= datetime.now().date():
                            applicable = True
                    else:
                        if not active_fest_id.from_date:
                            applicable = True
                        if not active_fest_id.to_date:
                            applicable = True
                        
                    if applicable:
                        line.unit_discount_price = round((line.unit_discount_price - line.unit_discount_price * price_rule_id.discount / 100),2)
                        line.is_special_discount = True
                        line.product_price_msrp = round(line.product_price_msrp-(line.product_price_msrp*price_rule_id.discount /100),2)
                        line.product_price_wholesale = round(line.product_price_wholesale-(line.product_price_wholesale*price_rule_id.discount /100),2)

                line._compute_amount()

    def catalog_manage_qty(self):
        self.ensure_one()
        # product_ids = self.env['product.product'].search([('id','in',self.line_ids.mapped('product_pro_id').ids),('available_qty_spt','<=',0.0)])
        product_ids = self.line_ids.mapped("product_pro_id").filtered(lambda x: x.available_qty_spt <= 0.0)
        if product_ids:
            return {
                'name': 'Manage Zero Quantity',
                'view_mode': 'form',
                'target': 'new',
                'context':{'default_product_ids':[(6,0,product_ids.ids)],'default_catalog_id' : self.id },
                'res_model': 'sale.catalog.qty.wizard.spt',
                'type': 'ir.actions.act_window',
            }
        else:
            self.state = 'validate'
            # added
            self._cr.commit()
            return self.catalog_manage_qty_with_available_qty()


    def _check_catalog_access(self,user_id,catalog_id):
        #user_id: record set of current user
        #catalog_id: int catalog id
        catalog = self.browse(catalog_id)
        if user_id.partner_id.id in catalog.partner_ids.ids:
            return catalog
        else:
            return False

    @api.model
    def default_get(self, fields):
        vals = super(SaleCatalog, self).default_get(fields)
        usd_public_pricelist = self.env.ref('tzc_sales_customization_spt.usd_public_pricelist_spt')
        vals['name'] = self.env['ir.sequence'].next_by_code('sale.catalog') or 'New'
        vals['pricelist_id'] = usd_public_pricelist.id
        return vals

    @api.depends('state','write_date')
    def _get_pending_catalog_count(self):
        for record in self:
            order_ids = self.env['sale.catalog.order'].search([('catalog_id','=',record.id)])
            record.pending_catalog_count = len(order_ids.filtered(lambda x:x.state == 'pending'))
            record.catalog_sent_count = len(order_ids.filtered(lambda x:x.state == 'sent'))

    @api.depends('sale_order_ids')
    def _get_sale_order_count(self):
        for record in self:
            record.sale_order_count = len(record.sale_order_ids)

    def action_apply_discount(self):
        for record in self:
            record.line_ids.update({
                'discount' : record.discount
            })
            record.line_ids._onchange_discount()

    def cancel_catalog(self):
        for record in self:
            catalog_order_ids = self.env['sale.catalog.order'].search_count([('catalog_id','in',record.ids)])
            catalog_order_ids.unlink()
            record.state = 'cancel'

    def reset_catalog(self):
        self.state = 'draft'


    def check_catalog_stock_spt(self):
        catalog_line_obj = self.env['sale.catalog.line']
        for record in self:
            warning_message = ""
            for product in record.line_ids.mapped('product_pro_id'):
                total_order_qty = 0
                for line in catalog_line_obj.search([('catalog_id','=',record.id),('product_pro_id.is_shipping_product','=',False),('product_pro_id','=',product.id)]):
                    total_order_qty = total_order_qty + line.product_qty
                
                if total_order_qty > 0.0 and (total_order_qty > product.available_qty_spt):
                    warning_message += 'Product %s having only %s quantity in stock,You can not add %s quantity. \n' % (product.display_name,int(product.available_qty_spt),int(total_order_qty))        
            if warning_message:
                raise UserError(_(warning_message))
    
    def check_stock_for_catalog_spt(self,catalog_id,catalog_lines):
        product_obj = self.env['product.product'].sudo()
        warning = False
        catalog = self.env['sale.catalog'].sudo().search([('id','=',catalog_id)])
        if catalog.expiry_date and catalog.expiry_date < date.today() :
            raise UserError('This catalog is expired..')
        for line_vals in catalog_lines:
            if 'product_id' in line_vals:
                product = product_obj.browse(int(line_vals['product_id']))
                if 'quantity' in  line_vals:
                    order_qty = line_vals['quantity'] or 0
                else:
                    order_qty = 0

                available_qty_spt = (product.available_qty_spt - product.minimum_qty) if product.on_consignment else product.available_qty_spt
                if order_qty > 0 and order_qty > available_qty_spt:
                    warning = True
                    break
        return warning
    
    def check_stock_of_catalogs(self, catalog_lines):
        catalog_data = []
        for line in catalog_lines:
            product_id = self.env['product.product'].search([('id','=',line.get('product_id'))])
            qty = product_id.available_qty_spt - product_id.minimum_qty if product_id.on_consignment else product_id.available_qty_spt
            data = {
                'product_id':line.get('product_id'),
                'quantity': 0 if qty<0 else qty,
                'unit':product_id.uom_name,
                'warning': True if line.get('quantity') > qty else False,
            }
            catalog_data.append(data)

        return catalog_data


    def send_catalogs_to_customers_spt(self):
        # pending_catalog_obj = self.env['pending.catalog.spt']
        for record in self:
            #check customer is added or not
            if not record.partner_ids:
                raise UserError(_("Please Select Customer First, Under The Customers Tab"))
            
            #check stock
            if not self._context.get('out_of_stock'):
                record.check_catalog_stock_spt()
            
            # #create pending catalog
            # for customer in record.partner_ids:
            #     pending_catalog_obj.create({
            #         'customer_id':customer.id,
            #         'catalog_id':record.id,
            #         'state':'draft',
            #     })
            record.send_out = datetime.now()
            record.state = 'pending'
    


    def catalog_manage_qty_with_available_qty(self):
        self.ensure_one()
        catalog_line_obj = self.env['sale.catalog.line']
        warning_message = ""
        for product in self.line_ids.mapped('product_pro_id'):
                total_order_qty = 0
                # for line in catalog_line_obj.search([('catalog_id','=',self.id),('product_pro_id.is_shipping_product','=',False),('product_pro_id','=',product.id)]):
                for line in self.line_ids.filtered(lambda line: line.product_pro_id.is_shipping_product == False and line.product_pro_id == product):
                    total_order_qty = total_order_qty + line.product_qty
                
                if total_order_qty > 0.0 and (total_order_qty > product.available_qty_spt):
                    warning_message += '<p>Product %s having only %s quantity in stock,You can not add %s quantity.</p>' % (product.display_name,int(product.available_qty_spt),int(total_order_qty))        

        if warning_message:
            return {
                'name': 'Manage Zero Quantity',
                'view_mode': 'form',
                'target': 'new',
                'context':{'default_name':warning_message,'default_catalog_id' : self.id },
                'res_model': 'product.qty.wizard.spt',
                'type': 'ir.actions.act_window',
            }
        else:
            self.state = 'manage_qtys'
            self.send_catalogs_to_customers_spt()

    def action_state_in_process(self):
        for record in self:
            record.state = 'process'

    
    def action_discount_wizard(self):
        self.ensure_one()
        if self.state not in ['done','cancel']:
            return {
                'name': 'Bulk Discount',
                'view_mode': 'form',
                'target': 'new',
                'context':{'default_catalog_id':self.id,'default_base_on':'brand','default_apply_on':'fix'},
                'res_model': 'discount.on.catalog.line.wizard.spt',
                'type': 'ir.actions.act_window',
            }
        else:
            raise UserError(_("You can not give discount after %s."%(self.state)))

    def action_sent_catalog_spt(self):
        return {
                "name":_("Sent Catalog"),
                "type":"ir.actions.act_window",
                "res_model":"sale.catalog.order",
                "view_mode":"tree",
                'domain': [('catalog_id','in',self.ids),('state','=','sent')]
        }
        

    # def action_catalog_visitors_spt(self):
    #     self.ensure_one()

    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': _('Catalog Visitors'),
    #         'res_model': 'catalog.visitors.spt',
    #         'view_mode': 'tree',
    #         'domain': [('catalog_id','=',self.id)],
    #     }

    def line_ordering_by_product(self):
        product_list = []
        user = self.env.user
        # product_list = self.line_ids.mapped('product_pro_id.name')
        # product_list =  self.line_ids.mapped(lambda line:line.product_pro_id.name if user.country_id not in line.product_pro_id.geo_restriction else '')
        for line in self.line_ids:
            product_name = line.product_pro_id.name_get()[0][1].strip()
            product_list.append(product_name)
        #to filter blank values comes where geo ristricted product comes
        product_list = list(filter(None, product_list))
        product_list = list(set(product_list))
        product_list.sort()
        return product_list

    def line_product_dict(self,product_name):
        product_dict = {}
        user = self.env.user
        if self.accept_decline_flag:
            self.accept_decline_flag = False
            self.line_ids = self.line_ids.filtered(lambda x:x.product_qty != 0)
            
        for line in self.line_ids:
            line_dict = {} 
            product_name = line.product_pro_id.name_get()[0][1].strip()
            if user.country_id.id not in line.product_pro_id.geo_restriction.ids:
                if line.product_pro_id.name in product_dict.keys():
                    product_dict[product_name]['line_ids'].append(line) 
                else:
                    line_dict['line_ids'] = [line]
                    product_dict[product_name] = line_dict
        return product_dict



    def send_catalog(self):
        SCO_Obj = self.env['sale.catalog.order']
        for record in self:
            if record.state != 'done':
                for customer_id in record.partner_ids:
                    sco_id =  SCO_Obj.create({
                        'catalog_id': record.id,
                        'customer_id': customer_id.id,
                        'state' : 'sent'
                    })
                    customer_template_id = self.env.ref('tzc_sales_customization_spt.tzc_email_template_catalog_spt')
                    customer_template_id.with_context(customer_id=customer_id).send_mail(record.id,email_values={'email_to': customer_id.email},force_send=True)
                    sales_person_template_id = self.env.ref('tzc_sales_customization_spt.tzc_email_template_catalog_confirmation_spt')
                    sales_person_template_id.with_context(customer_id=customer_id).send_mail(record.id,force_send=True)
                
            if not record.execution_time:
                last_record = self.search([('state','=','done')],limit=1)
                if last_record:
                    if record.execution_time:
                        record.execution_time = last_record.execution_time + timedelta(minutes=int(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.order_delay', default=0)))            
                    else:
                        record.execution_time = datetime.now()


            record.state = 'pending'
        
            record._get_pending_catalog_count()

    def action_mapping_qty(self):
        for record in self:
            for line in record.line_ids:
                if record.base_on_qty == 'available_qty':
                    if line.product_pro_id.on_consignment:
                        line.product_qty = line.product_pro_id.actual_stock if line.product_pro_id.actual_stock > 0 else 0
                    else:
                        line.product_qty = line.qty_available_spt
                else:
                    line.product_qty = line.product_qty_available


    def action_order_quotation(self):
        self.ensure_one()
        return{
            "name":_("Create Quotation"),
            "type":"ir.actions.act_window",
            "res_model":"create.catalog.quotation.wizard.spt",
            "view_mode":"form",
            'target': 'new',
            'context' : {
                'default_catalog_id' : self.id,
                'default_domain_parnter_ids' : [(6,0,self.partner_ids.ids)],
            }
        }

    def action_download_excel_report(self):
        return {
            'name':_('Download Catalog'),
            'type':'ir.actions.act_window',
            'res_model':'kits.wizard.download.catalog.excel',
            'view_mode':'form',
            'context':{'default_catalog_id':self.id,'from_action':False,'default_partner_ids' : [(6,0,self.partner_ids.ids)]},
            'target':'new',
        }

    # def action_donwload_catalog_excel_report(self):
    #     return {
    #         'name' : _('Catalog Report'),
    #         'type' : 'ir.actions.act_window',
    #         'res_model' : 'kits.wizard.download.catalog.excel',
    #         'view_mode' : 'form',
    #         'context' : {'default_catalog_id' : self.id,'from_action':True},
    #         'target' : 'new',
    #     }
    
    def get_sorted_products(self,lines):
        return lines.sorted(lambda x: x.product_pro_id.variant_name)

    @api.model
    def _fields_view_get(self,view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(SaleCatalog,self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.fromstring(res['arch'])
            for user_id in doc.xpath('//field[@name="user_id"]'):
                user_id.attrib['readonly'] = '0' if self.env.user.has_group('base.group_system') else '1'
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def create_address_line_for_sale(self, source_id, take_name=False):
        address = ''
        if take_name == True:
            if source_id.name:
                address += str(source_id.name)
            if source_id.street:
                if source_id.name:
                    address += '\n'+str(source_id.street)
                else:
                    address += source_id.street
        else:
            if source_id.street:
                address += str(source_id.street) 
        if source_id.street2:
            address += '\n'+str(source_id.street2)
        if source_id.city:
            address+= '\n'+str(source_id.city)
        if source_id.zip and take_name:
            address += ', '+source_id.zip
        if source_id.state_id:
            if take_name:
                address += '\n'+str(source_id.state_id.name)
            else:
                address += ' '+str(source_id.state_id.name)
        if source_id.country_id:
            if take_name:
                if source_id.state_id:
                    address += ', '+str(source_id.country_id.name)
                else:
                    address += '\n'+str(source_id.country_id.name)
            else:
                address += ' '+str(source_id.country_id.name)
                
        if source_id.zip and not take_name:
            address += ' '+source_id.zip
        address += '\nTel. '
        if source_id.phone:
            address += source_id.phone
        address += '\nEmail. '
        if source_id.email:
            address += source_id.email 
        return address

    def get_access_token_spt(self,customer_id=False):
        self.ensure_one()
        auth_param = url_encode(customer_id.signup_get_auth_param()[customer_id.id])
        return auth_param

    def get_catalog_line_pro_price(self):
        product_prices = self.env['kits.b2b.multi.currency.mapping'].get_product_price(self._context.get('customer_id').id,self.line_ids.mapped('product_pro_id').ids)
        return product_prices
