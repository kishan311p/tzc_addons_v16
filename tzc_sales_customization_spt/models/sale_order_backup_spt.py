from odoo import models, fields, api, _
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

class sale_order_backup_spt(models.Model):
    _name = 'sale.order.backup.spt'
    _description= "Sale Order Backup"
    
    order_id = fields.Many2one('sale.order','Sale Order')
    new_order_id = fields.Many2one('sale.order','New Sale Order')
    name = fields.Char('Order Reference')
    partner_id = fields.Many2one('res.partner','Customer')
    partner_invoice_id = fields.Many2one('res.partner','Invoice Address')
    partner_shipping_id = fields.Many2one('res.partner','Delivery Address')
    date_order = fields.Datetime('Order Date')
    # applied_promo_code = fields.Char('Applied Promo Code')
    payment_term_id = fields.Many2one('account.payment.term','Payment Terms')
    line_ids = fields.One2many('sale.order.backup.line.spt','order_backup_id','Order Lines', index=True, copy=False)
    total_subtotal = fields.Monetary(' Subtotal ',compute="_compute_order_total")
    total_tax = fields.Monetary(' Tax',compute="_compute_order_total")
    total_shipping_cost = fields.Monetary('Shipping Cost',compute="_compute_order_total")
    total_admin_cost = fields.Monetary('Admin Fee',compute="_compute_order_total")
    total_discount = fields.Monetary('Discount  ',compute="_compute_order_total")
    global_discount = fields.Monetary('Additional Discount',compute="_compute_order_total")
    total_amount = fields.Monetary(' Total',compute="_compute_order_total")
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True)
    user_id = fields.Many2one('res.users','Salesperson')
    pricelist_id = fields.Many2one(
        'product.pricelist', string='Pricelist ',# Unrequired company
     readonly=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="If you change the pricelist, only newly added lines will be affected.")
    
    # Glasses
    def _non_case_domain(self):
        return [('id','in',self.line_ids.filtered(lambda x: x.product_id.is_case_product==False).ids)]
    non_case_line_ids = fields.One2many('sale.order.backup.line.spt','order_backup_id','Product Lines', index=True, copy=False,domain=_non_case_domain)
    # Cases.
    def _include_case_domain(self):
        return [('id','in',self.line_ids.filtered(lambda x: x.product_id.is_case_product==True and x.is_included_case==True).ids)]
    included_cases_line_ids = fields.One2many('sale.order.backup.line.spt','order_backup_id','Include Case Lines', index=True, copy=False,domain=_include_case_domain)
    
    def _extra_case_domain(self):
        return [('id','in',self.line_ids.filtered(lambda x: x.product_id.is_case_product==True and x.is_included_case==False).ids)]
    extra_cases_line_ids = fields.One2many('sale.order.backup.line.spt','order_backup_id','Extra Case Lines', index=True, copy=False,domain=_extra_case_domain)

    def _compute_order_total(self):
        for record in self:
            total_subtotal=0
            total_tax=0
            total_shipping_cost=0
            total_admin_cost=0
            total_discount=0
            global_discount=0
            for line in record.line_ids:
                line_tax = 0
                if line.product_id.type != 'service':
                    total_subtotal =round( total_subtotal+ (line.price_unit * line.product_uom_qty),2)
                    total_discount = round(total_discount + (abs((line.price_unit - line.unit_discount_price)) * line.product_uom_qty),2)
                    for tax in line.tax_id:
                        line_tax = line_tax +((tax.amount*line.price_unit)/100) * line.product_uom_qty
                else:
                    if line.product_id.is_shipping_product:
                        total_shipping_cost = total_shipping_cost+ line.unit_discount_price
                    
                    if line.product_id.is_admin:
                        total_admin_cost = total_admin_cost+ line.unit_discount_price

                    
                    if line.product_id.is_global_discount:
                        global_discount = global_discount+ line.unit_discount_price
                
                total_tax = total_tax + line_tax
                    
            record.total_subtotal = round(total_subtotal,2)
            record.total_tax = round(total_tax,2)
            record.total_shipping_cost = round(total_shipping_cost,2)
            record.total_admin_cost = round(total_admin_cost,2)
            record.total_discount = round(total_discount,2)
            record.global_discount = round(global_discount)
            record.total_amount = round(total_subtotal + total_tax + total_shipping_cost + total_admin_cost - total_discount  - global_discount,2)
            
    def generate_new_order(self):
        catalog_obj = self.env['sale.catalog']
        catalog_obj.connect_server()
        method = catalog_obj.get_method('generate_new_order')
        if method['method']:
            localdict = {'self': self,'_':_,}
            exec(method['method'], localdict)  
            sale_id = localdict['sale_id']
            return {
                'name': 'Original Order',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'res_id': sale_id.id,
            }

    
    def action_get_new_order(self):
        for record in self:
            return {
                'name': 'Original Order',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'res_id': record.new_order_id.id,
            }

    # kits_package_product
    pack_order_backup = fields.Boolean('Backup Package Order')
    backup_package_lines = fields.One2many('kits.package.order.line','backup_order','Backup Package Lines')

    def generate_new_order(self):
        # catalog_obj = self.env['sale.catalog']
        # catalog_obj.connect_server()
        # method = catalog_obj.get_method('generate_new_order')
        # if method['method']:
        #     localdict = {'self': self,'_':_,}
        #     exec(method['method'], localdict)  
        #     sale_id = localdict['sale_id']

        sale_order_obj = self.env['sale.order']
        sale_order_line_obj = self.env['sale.order.line']
        pack_line_obj = self.env['kits.package.order.line']
        for record in self:
            sale_id = sale_order_obj.create({
                'partner_id' : record.partner_id.id,
                'partner_invoice_id' : record.partner_invoice_id.id,
                'partner_shipping_id' : record.partner_shipping_id.id,
                'payment_term_id' : record.payment_term_id.id,
                'date_order' : record.date_order,
                # 'applied_promo_code' : record.applied_promo_code,
                'user_id': record.user_id.id,
                'pricelist_id' : record.pricelist_id.id,
                'currency_id':record.currency_id.id,
                'b2b_currency_id':record.currency_id.id,
            })
            for line in record.line_ids.filtered(lambda x: not x.is_pack_order_line):
                sale_order_line_obj.create({
                    'product_id':line.product_id.id,
                    'product_uom_qty':line.product_uom_qty,
                    'price_unit':line.price_unit,
                    'unit_discount_price':line.unit_discount_price,
                    'fix_discount_price':line.fix_discount_price,
                    'discount':line.discount,
                    'name':line.name,
                    'order_id':sale_id.id,
                    'tax_id':[(6,0,line.tax_id.ids)],
                    'sale_type':line.sale_type,
                    'is_included_case':line.is_included_case
                })
            for pack_line in record.backup_package_lines:
                pack_line_obj.create({
                'order_id':sale_id.id,
                'product_id':pack_line.product_id.id,
                'qty':pack_line.qty,
                'sale_price':pack_line.sale_price,
                'discount_amount':pack_line.discount_amount,
                'pack_price':pack_line.pack_price,
            })
            record.new_order_id = sale_id.id
            return {
                'name': 'Original Order',
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'current',
                'res_model': 'sale.order',
                'type': 'ir.actions.act_window',
                'res_id': sale_id.id,
            }

