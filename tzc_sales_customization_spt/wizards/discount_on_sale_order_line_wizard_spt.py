from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime

class discount_on_sale_order_line_wizard_spt(models.TransientModel):
    _name = 'discount.on.sale.order.line.wizard.spt'
    _description = 'Discount Price'
    
    # def _get_sale_type_selection(self):
    #     sale_id = self.env['sale.order'].browse(self._context.get('default_sale_id'))
    #     sale_type = list()
    #     if sale_id and sale_id.order_line:
    #         sale_type = sale_id.order_line.mapped('sale_type')
    #     sale_type_selection = self.env['sale.order.line']._fields['sale_type'].selection
    #     return_sale_type = [s for s in sale_type_selection if s[0] in sale_type]
    #     return return_sale_type

  
    categ_ids = fields.Many2many('product.category','discount_on_sale_order_line_wizard_product_category_real','wizard_id','category_id',string='Category')
    brand_ids = fields.Many2many('product.brand.spt','discount_on_sale_order_line_wizard_product_brand_real','wizard_id','brand_id',string='Brands')
    product_ids = fields.Many2many('product.product','discount_on_sale_order_line_wizard_product_product_real','wizard_id','product_id',string='Products')
    discount = fields.Float('Discount (%)')
    sale_id = fields.Many2one('sale.order','Sale Order')
    sale_type = fields.Selection([('regular','Regular'),('on_sale','On Sale'),('clearance','Clearance'),('all','All')],string='Sale Type',default="regular")
    is_additional_discount = fields.Boolean('Add Additional Discount')
    additional_dis_per = fields.Float('Discount (%) ')
    
    base_on = fields.Selection([
        ('order_line', 'Order Line'),
        ('brand', 'Brand')],'Discount On', defualt="brand",required=True)

    apply_on = fields.Selection([
        ('percentage', 'Discount In Percentage'),('fix_discount','Discounted Amount'),
        ('fix','Fixed Price')],'Discount Based On', defualt="fix",required=True)

    fix_discount_price = fields.Float('Discount')
    fix_price = fields.Float('Fix Price')    

    @api.model
    def default_get(self, default_fields):
        res = super(discount_on_sale_order_line_wizard_spt, self).default_get(default_fields)
        if 'base_on' in res.keys():
            self.onchange_base_on()
        return res
    
    @api.onchange('base_on','sale_id')
    def onchange_base_on(self):
        domain ={}
        for record in self:
            if record.sale_id:
                categ_ids = record.sale_id.order_line.filtered(lambda x:x.product_id.type != 'service').mapped('product_id.categ_id')
                if categ_ids:
                    # domain[0]['categ_ids'] =  [('id', 'in', categ_ids.ids or [])]
                    domain['categ_ids'] = [('id', 'in', categ_ids.ids or [])]
                if record.base_on == 'brand':
                    brand_ids = record.sale_id.order_line.mapped('product_id.brand')
                    if brand_ids:
                        # domain[0]['brand_ids'] =  [('id', 'in', brand_ids.ids or [])]
                        domain['brand_ids']= [('id', 'in', brand_ids.ids or [])]
                    return {'domain': domain}
        return {}

    def action_process(self):
            order_line_obj = self.env['sale.order.line'] 
        # if not self.mapped('sale_id.code_promo_program_id'):
        # if not self.mapped('sale_id.applied_coupon_ids'):
            for record in self:
                if record.sale_id:
                    order_line_ids = []
                    if record.base_on == 'order_line':
                        domain = [('order_id','=',record.sale_id.id),('product_id.type','!=','service'),('package_id','=',False)]
                        if record.categ_ids:
                            domain.append(('product_id.categ_id','in',record.categ_ids.ids))
                        
                        if record.sale_type == 'all' and self.env.user.has_group('base.group_system'):
                            domain.append(('product_id.sale_type','in',('on_sale','clearance',False)))

                        order_line_ids = order_line_obj.search(domain)
                    else:
                        brand_domain = [('order_id','=',record.sale_id.id),('product_id.type','!=','service'),('package_id','=',False)]
                        if record.categ_ids:
                            brand_domain.append(('product_id.categ_id','in',record.categ_ids.ids))
                        if record.brand_ids:
                            brand_domain.append(('product_id.brand','in',record.brand_ids.ids))
                        
                        if (record.sale_type == 'on_sale' or record.sale_type == 'clearance') and self.env.user.has_group('base.group_system'):
                            brand_domain.append(('product_id.sale_type','=',record.sale_type))
                        elif record.sale_type == 'regular' and self.env.user.has_group('base.group_system'):
                            brand_domain.append(('product_id.sale_type','=',False))
                        elif record.sale_type == 'all' and self.env.user.has_group('base.group_system'):
                            pass
                        order_line_ids = order_line_obj.search(brand_domain)
                    if self.sale_type in ('on_sale','clearance') and self.env.user.has_group('base.group_system'):
                        order_line_ids = order_line_ids.filtered(lambda x: x.sale_type == self.sale_type )
                    elif self.sale_type == 'all' and self.env.user.has_group('base.group_system'):
                        pass
                    else:
                        order_line_ids = order_line_ids.filtered(lambda x:x if not x.sale_type and not x.package_id else None)
                    if not record.is_additional_discount:
                        if record.apply_on == 'fix_discount':
                            for line in order_line_ids:
                                line.write({
                                'fix_discount_price' : record.fix_discount_price
                            })
                            order_line_ids._onchange_fix_discount_price_spt()
                        elif record.apply_on ==  'fix':
                            for line in order_line_ids:
                                line.write({
                                'unit_discount_price' : record.fix_price
                            })
                            order_line_ids._onchange_unit_discounted_price_spt()
                        else:
                            for line in order_line_ids:
                                line.write({
                                'discount' : record.discount,
                            })
                            order_line_ids._onchange_discount_spt()
                        order_line_ids.order_id.write({'updated_by':self.env.user.id,'updated_on':datetime.now()})
                        order_line_ids.order_id._amount_all()
                    else:
                        for line in order_line_ids:
                            unit_discount_price = round(line.unit_discount_price - ((line.unit_discount_price*record.additional_dis_per)/100),2)
                            line.write({'unit_discount_price':unit_discount_price})
                            line.order_id.write({'updated_by':self.env.user.id,'updated_on':datetime.now()})
                            line._onchange_unit_discounted_price_spt()
        # else:
        #     raise UserError(_("This order contains promotion program,You can't apply bulk discount.")) 
 
