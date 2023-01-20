# -*- coding: utf-8 -*-
# Part of SnepTech See LICENSE file for full copyright and licensing details.##
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import datetime

class flash_menu_spt(models.Model):
    _name = 'flash.menu.spt'
    _description = 'Flash Sale'
    
    @api.constrains('state')
    def _check_state(self):
        for record in self:
            state = record.state
            if state == 'is_publised':
                flash_sale_count = self.search_count([('state','=','is_publised')])
                if flash_sale_count >1:
                    message_spt = "You can not have multiple published flash sale at a time, please close all the published flash sale first."
                    raise ValidationError(message_spt)


    def _get_default_currency_id(self):
        return self.env.company.currency_id.id
    
    # product_ids = fields.Many2many('product.product','flash_menu_product_product_rel','wizard_id','product_tmpl_id',string='Products',domain="[('eto_sale_method','=','fs')]")
    

    product_ids = fields.Many2many('product.product','flash_menu_product_product_rel','wizard_id','product_tmpl_id',string='Products')
    

    partner_ids = fields.Many2many('res.partner','flash_menu_res_partner_real','wizard_id','partner_id',string='Customers',domain="[('customer_type','=','b2b_fs')]")
    state = fields.Selection([
            ('draft', 'Draft'),
            ('confrimed', 'Confrimed'),
            ('is_publised', 'Publised'),
            ('is_expired', 'Expired'),
            ('cancel', 'Cancel'),
        ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    min_quantity = fields.Integer(
        'Min. Quantity', default=0,
        help="For the rule to apply, bought/sold quantity must be greater "
             "than or equal to the minimum quantity specified in this field.\n"
             "Expressed in the default unit of measure of the product.")
    pricelist_id = fields.Many2one('product.pricelist', 'Pricelist')
    pricelist_usd_id = fields.Many2one('product.pricelist', 'Pricelist USD')

    compute_price = fields.Selection([
        ('fixed', 'Fixed Price'),
        ('percentage', 'Percentage (discount)'),
        ('formula', 'Formula')], index=True, default='percentage',required=True)
    base = fields.Selection([
        ('list_price', 'Sales Price'),
        ('standard_price', 'Cost'),
        ('pricelist', 'Other Pricelist')], "Based on",
        default='list_price', required=True,
        help='Base price for computation.\n'
             'Sales Price: The base price will be the Sales Price.\n'
             'Cost Price : The base price will be the cost price.\n'
             'Other Pricelist : Computation of the base price based on another Pricelist.')
    currency_id = fields.Many2one('res.currency', 'Currency', default=_get_default_currency_id, required=True)
    name = fields.Char('Pricelist Name', required=True)
    fixed_price = fields.Float('Fixed Price', digits='Product Price')
    percent_price = fields.Float('Percentage Price')
    date_start = fields.Date('Start Date', help="Starting date for the pricelist item validation")
    date_end = fields.Date('End Date', help="Ending valid for the pricelist item validation")
    active = fields.Boolean('Active', default=True, help="If unchecked, it will allow you to hide the pricelist without removing it.")

    price_surcharge = fields.Float(
        'Price Surcharge', digits='Product Price',
        help='Specify the fixed amount to add or substract(if negative) to the amount calculated with the discount.')
    price_discount = fields.Float('Price Discount', default=0, digits=(16, 2))
    price_round = fields.Float(
        'Price Rounding', digits='Product Price',
        help="Sets the price so that it is a multiple of this value.\n"
             "Rounding is applied after the discount and before the surcharge.\n"
             "To have prices that end in 9.99, set rounding 10, surcharge -0.01")
    price_min_margin = fields.Float(
        'Min. Price Margin', digits='Product Price',
        help='Specify the minimum amount of margin over the base price.')
    price_max_margin = fields.Float(
        'Max. Price Margin', digits='Product Price',
        help='Specify the maximum amount of margin over the base price.')

    @api.constrains('price_min_margin', 'price_max_margin')
    def _check_margin(self):
        if any(item.price_min_margin > item.price_max_margin for item in self):
            raise ValidationError(_('The minimum margin should be lower than the maximum margin.'))
        return True
    @api.onchange('compute_price')
    def _onchange_compute_price(self):
        if self.compute_price != 'fixed':
            self.fixed_price = 0.0
        if self.compute_price != 'percentage':
            self.percent_price = 0.0
        if self.compute_price != 'formula':
            self.update({
                'price_discount': 0.0,
                'price_surcharge': 0.0,
                'price_round': 0.0,
                'price_min_margin': 0.0,
                'price_max_margin': 0.0,
            })


    def action_cancel(self):
        for record in self:
            record.state = 'cancel'

    def action_draft(self):
        for record in self:
            record.state = 'draft'


    def action_process(self):
        # catalog_obj = self.env['sale.catalog']
        # catalog_obj.connect_server()
        # method = catalog_obj.get_method('action_process_for_flash_menu_spt_model')
        # if method['method']:
        #     localdict = {'UserError':UserError,'self': self,'_':_,}
        #     exec(method['method'], localdict)

        pricelist_obj = self.env['product.pricelist']
        pricelist_item_obj = self.env['product.pricelist.item']
        for record in self:
            if not record.product_ids:
                raise UserError(_('Set Products.'))
            elif not record.partner_ids:
                raise UserError(_('Set Patners.'))
            elif not record.date_start or not record.date_end:
                raise UserError(_('Set Start Date and End Date.'))
            else:
                pricelist_id = pricelist_obj.create({
                    'name' : record.name,
                    'currency_id': record.currency_id.id,

                })
                pricelist_usd_id = pricelist_obj.create({
                    'name' : record.name +' International',
                    'currency_id': self.env['res.currency'].search([('name','=',"USD")]).id,

                })
                record.pricelist_id = pricelist_id.id
                record.pricelist_usd_id = pricelist_usd_id.id

                for product_id in record.product_ids:
                    pricelist_item_obj.create({
                        'pricelist_id' : pricelist_id.id,
                        'min_quantity' : record.min_quantity,
                        'applied_on' : '0_product_variant',
                        'compute_price' : record.compute_price,
                        'base' : record.base,
                        'fixed_price' : record.fixed_price,
                        'date_start' : record.date_start,
                        'percent_price' : record.percent_price,
                        'date_end' : record.date_end,
                        'price_surcharge' : record.price_surcharge,
                        'price_discount' : record.price_discount,
                        'price_round' : record.price_round,
                        'price_min_margin' : record.price_min_margin,
                        'price_max_margin' : record.price_max_margin,
                        'product_id' : product_id.id,
                        
                    })
                    pricelist_item_obj.create({
                        'pricelist_id' : pricelist_usd_id.id,
                        'min_quantity' : record.min_quantity,
                        'applied_on' : '0_product_variant',
                        'compute_price' : record.compute_price,
                        'base' : record.base,
                        'fixed_price' : record.fixed_price,
                        'date_start' : record.date_start,
                        'percent_price' : record.percent_price,
                        'date_end' : record.date_end,
                        'price_surcharge' : record.price_surcharge,
                        'price_discount' : record.price_discount,
                        'price_round' : record.price_round,
                        'price_min_margin' : record.price_min_margin,
                        'price_max_margin' : record.price_max_margin,
                        'product_id' : product_id.id,
                        
                    })
                    
                record.state = 'confrimed' 



    def action_is_publised(self):
        for record in self:
            property_product_pricelist_usd = self.env.ref('tzc_sales_customization_spt.usd_public_pricelist_spt')
            flash_sale_category = self.env.ref('tzc_sales_customization_spt.tzc_flash_sale_ecommerce_category')
            flash_sale_category.product_tmpl_ids = [(6,0,record.product_ids.ids)]
            for partner in record.partner_ids:
                if partner.country_id.code == 'CA':
                    partner.temp_pricelist_id = partner.property_product_pricelist.id
                    partner.property_product_pricelist = record.pricelist_id.id
                else:
                    partner.temp_pricelist_id = property_product_pricelist_usd.id
                    partner.property_product_pricelist = record.pricelist_usd_id.id
            record.state = 'is_publised'
    
    def open_pricelist_spt(self):
        for record in self:
            if not record.pricelist_id:
                raise UserError(_('No related pricelist found make sure you are in confirmed the records'))
            else:
                return {
                    'name': _('Price List'),
                    'view_mode': 'form',
                    'res_model': 'product.pricelist',
                    'view_type': 'form',
                    'type': 'ir.actions.act_window',
                    'res_id': record.pricelist_id.id,
                    'target': 'new',
                }
    
    def open_pricelist_usd_spt(self):
        for record in self:
            if not record.pricelist_usd_id:
                raise UserError(_('No related pricelist found make sure you are in confirmed the records'))
            else:
                return {
                    'name': _('Price List'),
                    'view_mode': 'form',
                    'res_model': 'product.pricelist',
                    'view_type': 'form',
                    'type': 'ir.actions.act_window',
                    'res_id': record.pricelist_usd_id.id,
                    'target': 'new',
                }
    
    
    def button_expired(self):
        for record in self:
            for partner_id in record.partner_ids:
                partner_id.property_product_pricelist = partner_id.temp_pricelist_id.id
            flash_sale_category = self.env.ref('tzc_sales_customization_spt.tzc_flash_sale_ecommerce_category')
            flash_sale_category.product_tmpl_ids = [(6,0,[])]
            record.state = 'is_expired'

    def check_expiry_date(self):
        for record in self.search([('state','=','is_published'),('date_end','<',datetime.date.today())]):
            record.button_expired()
