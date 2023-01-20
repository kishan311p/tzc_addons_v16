from odoo import models,fields,api,_

class kits_bulk_discount_on_package_products(models.TransientModel):
    _name = 'kits.bulk.discount.on.package.products'
    _description = 'Bulk Discount on Package product'

    def _get_brand_domain(self):
        brands = self.env['kits.package.product'].browse(self._context.get('default_pack_product_id')).product_line_ids.mapped('product_id').mapped('brand').ids
        return [('id','in',brands)]
    
    def _get_categ_domain(self):
        categs = self.env['kits.package.product'].browse(self._context.get('default_pack_product_id')).product_line_ids.mapped('product_id').mapped('categ_id').ids
        return [('id','in',categs)]

    # def _get_sale_type_selection(self):
    #     package_id = self.env['kits.package.product'].browse(self._context.get('default_pack_product_id'))
    #     sale_type = list()
    #     if package_id and package_id.product_line_ids:
    #         sale_type = package_id.product_line_ids.mapped('sale_type')
    #     return_sale_type = [s for s in self.env['product.product']._fields.get('sale_type').selection if s[0] in sale_type]
    #     return return_sale_type or list()


    pack_product_id = fields.Many2one('kits.package.product','Package Product')
    discount_based_on = fields.Selection([('fixed_price','Fixed Price'),('discount_amount','Discount In Amount'),('discount_percentage','Discount In Percentage')],string="Discount Based On",default="fixed_price")
    price = fields.Float('Discounted Price')
    discount_on = fields.Selection([('on_line','Product Lines'),('on_brand','Brand')],default='on_line',string='Discount On')
    discount_percentage = fields.Float('Discount (%)')
    brand_ids = fields.Many2many('product.brand.spt',domain=_get_brand_domain,string="Brand")
    categ_ids = fields.Many2many('product.category',domain=_get_categ_domain,string="Category")
    sale_type = fields.Selection([('regular','Regular'),('on_sale','On Sale'),('clearance','Clearance'),('all','All')],string='Sale Type',default="regular",required=True)
    is_additional_discount = fields.Boolean('Add Additional Discount')
    additional_discount = fields.Float(' Discount (%)')

    def action_process(self):
        if self.pack_product_id and self.pack_product_id.product_line_ids:
            line_ids = False
            if self.discount_on == 'on_line':
                domain = [('product_id.type','!=','service')]
                if self.categ_ids:
                    domain.append(('product_id.categ_id','in',self.categ_ids.ids))

                if self.sale_type == 'all' and self.env.user.has_group('base.group_system'):
                    domain.append(('product_id.sale_type','in',('on_sale','clearance',False)))

                line_ids = self.pack_product_id.product_line_ids.search(domain)
            elif self.discount_on == 'on_brand':
                brand_domain = [('product_id.type','!=','service')]
                if self.categ_ids:
                    brand_domain.append(('product_id.categ_id','in',self.categ_ids.ids))
                if self.brand_ids:
                    brand_domain.append(('product_id.brand','in',self.brand_ids.ids))

                if (self.sale_type == 'on_sale' or self.sale_type == 'clearance') and self.env.user.has_group('base.group_system'):
                    brand_domain.append(('product_id.sale_type','=',self.sale_type))
                elif self.sale_type == 'regular' and self.env.user.has_group('base.group_system'):
                    brand_domain.append(('product_id.sale_type','=',False))
                elif self.sale_type == 'all' and self.env.user.has_group('base.group_system'):
                    pass      

                line_ids = self.pack_product_id.product_line_ids.search(brand_domain)      
            if self.sale_type in ('on_sale','clearance') and self.env.user.has_group('base.group_system'):
                line_ids = line_ids.filtered(lambda x: x.sale_type == self.sale_type)
            elif self.sale_type == 'all' and self.env.user.has_group('base.group_system'):
                pass
            else:
                line_ids = line_ids.filtered(lambda x: not x.sale_type)
            if not self.is_additional_discount:
                if line_ids:
                    if self.discount_based_on == 'fixed_price':
                        line_ids.write({'usd_price':self.price})
                        line_ids._onchange_usd_price()
                    elif self.discount_based_on == 'discount_amount':
                        line_ids.write({'fix_discount_price':self.price})
                        line_ids._onchange_fix_discount_price()
                    elif self.discount_based_on == 'discount_percentage':
                        line_ids.write({'discount':self.discount_percentage})
                        line_ids._onchange_discount()
                    else:
                        pass
            else:
                if line_ids:
                    for line in line_ids:
                        price = round(line.usd_price-(line.usd_price*self.additional_discount*0.01),2)
                        line.write({'usd_price':price})
                        line._onchange_usd_price()
