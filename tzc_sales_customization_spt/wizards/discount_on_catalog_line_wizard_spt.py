# -*- coding: utf-8 -*-
# Part of SnepTech See LICENSE file for full copyright and licensing details.##
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class discount_on_catalog_line_wizard_spt(models.TransientModel):
    _name = 'discount.on.catalog.line.wizard.spt'
    _description = 'Discount Price On Catalog'
    
    # def _get_sale_type_selection(self):
    #     catalog_id = self.env['sale.catalog'].browse(self._context.get('default_catalog_id'))
    #     sale_type = list()
    #     if catalog_id and catalog_id.line_ids:
    #         sale_type = catalog_id.line_ids.mapped('sale_type')
    #     sale_type_selection = self.env['sale.catalog.line']._fields['sale_type'].selection
    #     return_sale_type = [s for s in sale_type_selection if s[0] in sale_type]
    #     return return_sale_type
  
    categ_ids = fields.Many2many('product.category','discount_on_catalog_line_wizard_product_category_real','wizard_id','category_id',string='Category')
    brand_ids = fields.Many2many('product.brand.spt','discount_on_catalog_line_wizard_product_brand_real','wizard_id','brand_id',string='Brands')
    product_ids = fields.Many2many('product.product','discount_on_catalog_line_wizard_product_product_real','wizard_id','product_id',string='Products')
    discount = fields.Float('Discount (%)')
    catalog_id = fields.Many2one('sale.catalog','Sale Catalog')
    sale_type = fields.Selection([('regular','Regular'),('on_sale','On Sale'),('clearance','Clearance'),('all','All')],string='Sale Type',default="regular")
    is_additional_discount = fields.Boolean('Add Additional Discount')
    additional_discount = fields.Float('Discount (%) ')
    
    base_on = fields.Selection([
        ('line_ids', 'Order Line'),
        ('brand', 'Brand')],'Discount On', default="brand",required=True)

    apply_on = fields.Selection([
        ('percentage', 'Discount In Percentage'),
        ('fix','Fixed Price')],'Discount Based On', default="fix",required=True)

    fix_price = fields.Float('Fix Price')    

    @api.model
    def default_get(self, default_fields):
        res = super(discount_on_catalog_line_wizard_spt, self).default_get(default_fields)
        if 'base_on' in res.keys():
            self.onchange_base_on()
        return res
    
    @api.onchange('base_on','catalog_id')
    def onchange_base_on(self):
        domain ={}
        for record in self:
            if record.catalog_id:
                categ_ids = record.catalog_id.line_ids.mapped('product_pro_id.categ_id')
                if categ_ids:
                    domain['categ_ids'] = [('id', 'in', categ_ids.ids or [])]
                if record.base_on == 'brand':
                    brand_ids = record.catalog_id.line_ids.mapped('product_pro_id.brand')
                    if brand_ids:
                        domain['brand_ids']= [('id', 'in', brand_ids.ids or [])]
                    return {'domain': domain}
        return {}

    def action_process(self):
        # catalog_obj = self.env['sale.catalog']
        # catalog_obj.connect_server()
        # method = catalog_obj.get_method('action_process_discount_on_catalog_line_wizard_model')
        # if method['method']:
        #     localdict = {'self': self,}
        #     exec(method['method'], localdict)
        line_ids_obj = self.env['sale.catalog.line'] 
        for record in self:
            if record.catalog_id:
                line_ids = []
                if record.base_on == 'line_ids':
                    domain = [('catalog_id','=',record.catalog_id.id),('product_pro_id.type','!=','service')]
                    if record.categ_ids:
                        domain.append(('product_pro_id.categ_id','in',record.categ_ids.ids))

                    if record.sale_type == 'all' and self.env.user.has_group('base.group_system'):
                        domain.append(('product_pro_id.sale_type','in',('on_sale','clearance',False)))
                    
                    line_ids = line_ids_obj.search(domain)
                else:
                    brand_domain = [('catalog_id','=',record.catalog_id.id),('product_pro_id.type','!=','service')]
                    if record.categ_ids:
                        brand_domain.append(('product_pro_id.categ_id','in',record.categ_ids.ids))
                    if record.brand_ids:
                        brand_domain.append(('product_pro_id.brand','in',record.brand_ids.ids))

                    if (record.sale_type == 'on_sale' or record.sale_type == 'clearance') and self.env.user.has_group('base.group_system'):
                        brand_domain.append(('product_pro_id.sale_type','=',record.sale_type))
                    elif record.sale_type == 'regular' and self.env.user.has_group('base.group_system'):
                        brand_domain.append(('product_pro_id.sale_type','=',False))
                    elif record.sale_type == 'all' and self.env.user.has_group('base.group_system'):
                        pass
                    line_ids = line_ids_obj.search(brand_domain)
                if self.sale_type in ('on_sale','clearance') and self.env.user.has_group('base.group_system'):
                    line_ids = line_ids.filtered(lambda x: x.sale_type == self.sale_type)
                elif self.sale_type == 'all' and self.env.user.has_group('base.group_system'):
                    pass
                else:
                    line_ids = line_ids.filtered(lambda x:x if not x.sale_type else None)
                if not record.is_additional_discount:
                    if record.apply_on ==  'fix':
                        line_ids.write({
                            'unit_discount_price' : record.fix_price
                        })
                        line_ids._onchange_fix_discount_price()
                    else:
                        line_ids.write({
                            'discount' : record.discount,
                        })
                        line_ids._onchange_discount()
                else:
                    for line in line_ids:
                        price = round(line.unit_discount_price - (line.unit_discount_price*record.additional_discount*0.01),2)
                        line.write({'unit_discount_price':price})
                        line._onchange_fix_discount_price()
