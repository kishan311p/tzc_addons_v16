from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    # display_type = fields.Selection([
    #     ('line_section', "Section"),
    #     ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    is_reward_line = fields.Boolean('Is a program reward line')

    is_virtual = fields.Boolean('Virtual Product')
    virtual_source = fields.Char('Virtual Source')
    redeem_points = fields.Float('Redeem Virtual Points')
    reward_amount = fields.Float('Redeem Amount ')

    b2b_currency_rate = fields.Float('Currency Rate ')
    
    sh_sale_barcode_scanner_is_last_scanned = fields.Boolean(string = "Last Scanned?")

    package_id = fields.Many2one('kits.package.product','Package')
    is_pack_order_line = fields.Boolean('Package order line')
    package_line_id = fields.Many2one('kits.package.order.line',"Package Line",ondelete='cascade')

    state = fields.Selection(related='order_id.state', string='Order Status', readonly=True, copy=False, store=True)
    price_unit = fields.Float(tracking=True)
    is_global_discount = fields.Boolean("Is Additional Discount",related="product_id.is_global_discount", store=True)
    is_shipping_product = fields.Boolean("Is Shipping Product",related="product_id.is_shipping_product", store=True)
    is_admin = fields.Boolean("Is Admin Product",related="product_id.is_admin", store=True)
    fix_discount_price = fields.Float('  Discount  ')    
    # is_fs = fields.Boolean("Is FS?")
    sale_type = fields.Selection([('clearance','Clearance'),('on_sale','On Sale')],'Sale Type')
    unit_discount_price = fields.Float('Our Price')
    product_categ_id = fields.Many2one('product.category',related="product_id.categ_id", string='Category ', readonly=True)
    # is_promotion_applied = fields.Boolean("Is promotion applied?")
    picked_qty = fields.Integer('Delivered',compute='_compute_picked_qty',store=True,precompute=True)
    picked_qty_subtotal = fields.Float('  Subtotal  ',compute="_compute_picked_qty",store=True,precompute=True)
    is_special_discount = fields.Boolean("Is Special Discount",help="This is flag for check product is in special discount or not.")
    primary_image_url = fields.Char("Primary Image URL",related='product_id.primary_image_url')
    case_type = fields.Selection(string="Case Type",related='product_id.case_type')
    restrict_case_order_line = fields.Boolean('Restrict Flag')
    special_discount_offer = fields.Many2one('kits.special.discount.offers', string='Special Discount Offers')
    is_case_product = fields.Boolean('Case Product Flag',help='Field for website purpose to differentiate order line is case or not.',related='product_id.is_case_product')
    is_included_case = fields.Boolean('Included Case Flag')
    
    def _default_extra_cases_domain(self):
        existing_case_product_ids = self.order_id.extra_case_order_line.mapped('product_id').ids
        extra_product_case_ids = self.env['product.product'].search([('is_case_product','=',True),('id','not in',existing_case_product_ids)]).ids
        # extra_product_case_ids = self.env['product.product'].search([('is_case_product','=',True)]).ids
        return extra_product_case_ids

    extra_cases_ids = fields.Many2many('product.product','extra_cases_product_product_rel','extra_cases_id','product_id','Case Product Domain',help='Used for domain purpose in sale order for extra cases.',default=_default_extra_cases_domain)
    
    @api.onchange('product_id')
    def _onchange_extra_case_domain(self):
        existing_case_product_ids = self.order_id.extra_case_order_line.mapped('product_id').ids
        extra_product_case_ids = self.env['product.product'].search([('is_case_product','=',True),('id','not in',existing_case_product_ids)]).ids
        # extra_cases_ids = self.order_id.extra_case_order_line
        # for case_id in extra_cases_ids:
        #     if case_id._origin:
        #         case_id._origin.write({
        #             'extra_cases_ids' : [(6,0,extra_product_case_ids)]
        #         })
        #     else:
        self.write({
            'extra_cases_ids' : [(6,0,extra_product_case_ids)]
        })
        # self.extra_cases_ids.ids = extra_product_case_ids
        


    def _get_virtual_sources(self):
        return []

    @api.onchange('product_id')
    def _onchange_product_id_spt(self):
        for record in range(len(self)):
            record = self[record]
            record.product_uom_qty = record.product_uom_qty
            if record.product_id and record.product_id.is_global_discount:
                record.product_uom_qty = -record.product_uom_qty
            if record.product_id.sale_type:
                record.sale_type = record.product_id.sale_type

    # @api.onchange('product_id')
    # def product_id_change_eto(self):
    #     for record in range(len(self)):
    #         record = self[record]
    #         price_unit = record.price_unit
    #         unit_discount_price = 0
            
    #         if record.order_id:
    #             if record.sale_type and record.order_id.partner_id and record.order_id.partner_id.property_product_pricelist :
    #                 if record.order_id.partner_id.property_product_pricelist.currency_id.name == 'CAD':
    #                    price_unit = record.product_id.on_sale_cad
    #                 else:
    #                    price_unit = record.product_id.on_sale_usd
    #         unit_discount_price = price_unit
    #         if record.discount:
    #         	unit_discount_price = price_unit - (price_unit * record.discount)* 0.01
    #             record.update({'price_unit':price_unit,'unit_discount_price': unit_discount_price})


    @api.depends('product_id','price_unit','unit_discount_price','picked_qty','product_uom_qty','discount','tax_id','move_ids','move_ids.quantity_done')
    def _compute_picked_qty(self):
        move_obj = self.env['stock.move']
        for record in range(len(self)):
            record = self[record]
            picked_qty_subtotal = 0.0
            move_ids = move_obj.search([('id','in',record.move_ids.ids),('state','!=','cancel')])
            record.picked_qty = sum(move_ids.mapped('quantity_done')) if move_ids else 0
            if record.order_id.state not in ['sale', 'done','in_scanning','scanned','scan','shipped','draft_inv','open_inv']:
                picked_qty_subtotal = round( record.price_subtotal,2)
            else:  
                if record.picked_qty and record.product_id.type != 'service': 
                    picked_qty_subtotal = picked_qty_subtotal + (record.picked_qty * record.unit_discount_price)
                if record.product_id.type == 'service': 
                    picked_qty_subtotal =picked_qty_subtotal + (record.product_uom_qty * record.unit_discount_price)
            # if record.product_id.is_case_product:
            #     record.picked_qty_subtotal = round(record.unit_discount_price * record.product_uom_qty,2)
            # else:
            record.picked_qty_subtotal = round(picked_qty_subtotal,2)
                


    @api.onchange('product_id',"product_uom_qty",'price_unit','tax_id','unit_discount_price','discount','picked_qty','fix_discount_price')
    def _onchange_price_total_compute(self):
        self._compute_amount()
    
    @api.depends('product_id',"product_uom_qty",'price_unit','tax_id','unit_discount_price','discount','picked_qty','fix_discount_price')
    def _compute_amount(self):
        res = super(SaleOrderLine,self)._compute_amount()
        for record in range(len(self)):
            record = self[record]
            # product_price = record.price_unit
            # unit_discount_price = record.unit_discount_price
            # if not record.product_id.is_shipping_product and not record.product_id.is_global_discount and not record.product_id.is_admin:
            # Convert price based on currency.
                # product_price_dict = (self.env['kits.b2b.multi.currency.mapping'].with_context(from_order_line=True).get_product_price(record.order_id.partner_id.id,record.product_id.ids,order_id=record.order_id) or {}).get(record.product_id.id,{})
                
                # product_price = product_price_dict.get('price')
                # unit_discount_price = product_price_dict.get('discounted_unit_price')

            # Call method for extra pricing.
            # extra_pricing = record.product_id.inflation_special_discount(record.order_id.partner_id.country_id.ids,bypass_flag=record.order_id.partner_id.b2b_pricelist_id.is_pricelist_excluded)
            # if extra_pricing.get('is_inflation'):
            #     product_price = product_price_dict.get('price')+(product_price_dict.get('price')*extra_pricing.get('inflation_rate') /100)
            #     unit_discount_price = unit_discount_price+(unit_discount_price*extra_pricing.get('inflation_rate') /100)
            # if extra_pricing.get('is_special_discount'):
            #     unit_discount_price = (unit_discount_price - unit_discount_price * extra_pricing.get('special_disc_rate') / 100)
            
            # record.price_unit = product_price
            # if unit_discount_price:
            if record.order_id.state not in record.order_id.draft_states():
                record.price_subtotal = round(record.unit_discount_price * record.picked_qty,2)
            else:
                record.price_subtotal = round(record.unit_discount_price * record.product_uom_qty,2)
        return res

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.

        :return: A python dictionary.
        """
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.order_id.partner_id,
            currency=self.order_id.currency_id,
            product=self.product_id,
            taxes=self.tax_id,
            price_unit=self.price_unit,
            quantity=self.picked_qty or self.product_uom_qty,
            discount=self.discount,
            price_subtotal=self.price_subtotal,
        )
    
    @api.constrains('price_subtotal')
    def _check_pricesubtotal_spt(self):
        for record in range(len(self)):
            record = self[record]
            if record.price_subtotal < 0.0 and not record.product_id.is_global_discount:
                raise UserError(_('Subtotal amount should not be in negative.'))
            
    @api.onchange('discount','price_unit')
    def _onchange_discount_spt(self):
        for record in range(len(self)):
            record = self[record]
            unit_discount_price =round( record.price_unit - ((record.discount *0.01) * record.price_unit),2)
            fix_discount_price = round((record.price_unit*record.discount)/100,2)
            
            record.unit_discount_price = round(unit_discount_price,2)
            record.fix_discount_price = round(fix_discount_price,2)

    @api.onchange('fix_discount_price','price_unit')
    def _onchange_fix_discount_price_spt(self):
        for record in range(len(self)):
            record = self[record]
            unit_discount_price = round(record.price_unit - record.fix_discount_price,2)
            
            try:
                discount = round((record.fix_discount_price*100/record.price_unit),2)
            except:
                discount = 0.0
            
            record.unit_discount_price = round(unit_discount_price,2)
            record.discount = round(discount,2)

    @api.onchange('unit_discount_price','price_unit')
    def _onchange_unit_discounted_price_spt(self):
        for record in range(len(self)):
            record = self[record]
            try:
                discount = round(100-(record.unit_discount_price*100/record.price_unit),2)
            except:
                discount = 0.0
            
            try:
                fix_discount_price = float(str(record.price_unit*discount/100).split('.')[0]+'.'+str(record.price_unit*discount/100).split('.')[1][0:2])
            except:
                fix_discount_price = round((record.price_unit*discount/100),2)

            record.fix_discount_price = round(fix_discount_price,2)
            record.discount = round(discount,2)


    @api.onchange('product_uom','product_uom_qty')
    def product_uom_change_spt(self):
        for record in range(len(self)):
            record = self[record]
            # record.product_uom_qty = record.product_uom_qty
            if record.product_id and record.product_id.is_global_discount:
                record.product_uom_qty = -record.product_uom_qty
    
    @api.onchange('product_id')
    def product_id_change(self):
        # res = super(SaleOrderLine, self).product_id_change()
        for record in range(len(self)):
            record = self[record]
            if not record.is_included_case:
                product_price_dict = (self.env['kits.b2b.multi.currency.mapping'].with_context(from_order_line=True).get_product_price(record.order_id.partner_id.id,record.product_id.ids,order_id=record.order_id) or {}).get(record.product_id.id,{})
                product_price = product_price_dict.get('price')
                unit_discount_price = product_price_dict.get('discounted_unit_price')
                fix_discount_price = product_price_dict.get('fix_discount_price')
                extra_pricing = record.product_id.inflation_special_discount(record.order_id.partner_id.country_id.ids,bypass_flag=record.order_id.partner_id.b2b_pricelist_id.is_pricelist_excluded)
                if record.product_id:
                    update_dict = {'price_unit':round(product_price,2),
                                'unit_discount_price': round(unit_discount_price,2), 
                                #    'fix_discount_price':round(record.fix_discount_price,2),
                                'fix_discount_price':round(fix_discount_price,2),
                                'sale_type':record.product_id.sale_type if record.product_id.sale_type else ''}

                    # active_inflation = self.env['kits.inflation'].search([('is_active','=',True)])
                    # inflation_rule_ids = self.env['kits.inflation.rule'].search([('country_id','in',self.order_id.partner_id.country_id.ids),('brand_ids','in',record.product_id.brand.ids),('inflation_id','=',active_inflation.id)])
                    # inflation_rule = inflation_rule_ids[-1] if inflation_rule_ids else False
                    # if inflation_rule:
                    #     is_inflation = False
                    #     if active_inflation.from_date and active_inflation.to_date :
                    #         if active_inflation.from_date <= datetime.now().date() and active_inflation.to_date >= datetime.now().date():
                    #             is_inflation = True
                    #     elif active_inflation.from_date:
                    #         if active_inflation.from_date <= datetime.now().date():
                    #             is_inflation = True
                    #     elif active_inflation.to_date:
                    #         if active_inflation.to_date >= datetime.now().date():
                    #             is_inflation = True
                    #     else:
                    #         if not active_inflation.from_date:
                    #             is_inflation = True
                    #         if not active_inflation.to_date:
                    #             is_inflation = True
                            
                    if extra_pricing.get('is_inflation'):
                        product_price = round(product_price+(product_price*extra_pricing.get('inflation_rate') /100),2)
                        unit_discount_price = round(unit_discount_price+(unit_discount_price*extra_pricing.get('inflation_rate') /100),2)
                        update_dict.update({'price_unit':product_price,'unit_discount_price':unit_discount_price})

                    # active_fest_id = self.env['tzc.fest.discount'].search([('is_active','=',True)])
                    # special_disocunt_id = self.env['kits.special.discount'].search([('country_id','in',self.order_id.partner_id.country_id.ids),('brand_ids','in',record.product_id.brand.ids),('tzc_fest_id','=',active_fest_id.id)])
                    # price_rule_id = special_disocunt_id[-1] if special_disocunt_id else False
                    # if price_rule_id:
                    #     applicable = False 
                    #     if active_fest_id.from_date and active_fest_id.to_date :
                    #         if active_fest_id.from_date <= datetime.now().date() and active_fest_id.to_date >= datetime.now().date():
                    #             applicable = True
                    #     elif active_fest_id.from_date:
                    #         if active_fest_id.from_date <= datetime.now().date():
                    #             applicable = True
                    #     elif active_fest_id.to_date:
                    #         if active_fest_id.to_date >= datetime.now().date():
                    #             applicable = True
                    #     else:
                    #         if not active_fest_id.from_date:
                    #             applicable = True
                    #         if not active_fest_id.to_date:
                    #             applicable = True
                            
                    if extra_pricing.get('is_special_discount'):
                        special_discount_price = update_dict.get('unit_discount_price') - update_dict.get('unit_discount_price') * extra_pricing.get('special_disc_rate') / 100
                        fix_discount_price_spt = product_price - special_discount_price
                        update_dict.update({'fix_discount_price':fix_discount_price_spt,'unit_discount_price': special_discount_price}) #,'is_special_discount':applicable

                    record.write(update_dict)
                    # record._onchange_fix_discount_price_spt()
                    record._onchange_unit_discounted_price_spt()
                    # record._onchange_discount_spt()

                if record.order_id.partner_id and not record.order_id.partner_id.country_id:
                    record.tax_id = False
        # return res

    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        for record in range(len(self)):
            record = self[record]
            if record.product_id:
                record._compute_picked_qty()

    def _compute_qty_at_date(self):
        res = super(SaleOrderLine, self)._compute_qty_at_date()

        for rec in range(len(self)):
            rec = self[rec]
            rec.free_qty_today = rec.product_id.available_qty_spt

        return res

    @api.depends('qty_invoiced', 'qty_delivered', 'picked_qty', 'order_id.state')
    def _compute_qty_to_invoice(self):
        """
        Compute the quantity to invoice. If the invoice policy is order, the quantity to invoice is
        calculated from the ordered quantity. Otherwise, the quantity delivered is used.
        """
        for line in range(len(self)):
            line = self[line]
            if line.order_id.state in ['sale', 'done','in_scanning','scanned','scan','shipped','draft_inv','open_inv']:
                if line.product_id.is_shipping_product or line.product_id.is_global_discount or line.product_id.is_admin:
                    line.qty_to_invoice = line.product_uom_qty
                else:
                    line.qty_to_invoice = line.picked_qty - line.qty_invoiced
            else:
                line.qty_to_invoice = 0

    @api.model
    def _prepare_add_missing_fields(self, values):
        """ Deduce missing required fields from the onchange """
        res = {}
        onchange_fields = ['name', 'price_unit', 'product_uom', 'tax_id']
        if values.get('order_id') and values.get('product_id') and any(f not in values for f in onchange_fields):
            line = self.new(values)
            line.product_id_change()
            for field in onchange_fields:
                if field not in values:
                    res[field] = line._fields[field].convert_to_write(line[field], line)
        return res

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('display_type', self.default_get(['display_type'])['display_type']):
                values.update(product_id=False, price_unit=0, product_uom_qty=0, product_uom=False, customer_lead=0)
            values.update(self._prepare_add_missing_fields(values))

        lines = super().create(vals_list)
        for line in range(len(lines)):
            line = lines[line]
            if line.product_id and line.order_id.state in ['sale', 'done','in_scanning','scanned','scan','shipped','draft_inv','open_inv']:
                msg = _("Extra line with %s ") % (line.product_id.display_name,)
                line.order_id.message_post(body=msg)
                # create an analytic account if at least an expense product
                if line.product_id.expense_policy not in [False, 'no'] and not line.order_id.analytic_account_id:
                    line.order_id._create_analytic_account()
        return lines
    
    def write(self,vals):
        if self.is_shipping_product and not(self.env.user.has_group('base.group_system') or self.env.user.has_group('stock.group_stock_manager')):
            raise UserError('You cannot change Shipping Cost')
        if self.state in ['draft','sent','received'] and 'product_uom_qty' in vals:
            case_product_id = self.product_id.case_product_id
            if case_product_id:
                qty = sum(self.order_id.non_case_order_line.filtered(lambda x: x.product_id.case_product_id==case_product_id).mapped('product_uom_qty'))
                case_order_line_id = self.order_id.case_order_line.filtered(lambda x : x.product_id==case_product_id)
                if case_order_line_id:
                    case_order_line_id.product_uom_qty = qty

        return super().write(vals)

    @api.depends('move_ids.state', 'move_ids.scrapped', 'move_ids.product_uom_qty', 'move_ids.product_uom','picked_qty')
    def _compute_qty_delivered(self):
        for rec in self:
            if rec.state=='shipped':
                rec.qty_delivered = rec.picked_qty
            elif rec.state=='cancel':
                rec.qty_delivered = rec.picked_qty
            else:
                pass

    #@api.onchange('price_unit')
    #def onchange_price_unit_case(self):
    #    for rec in self:
    #        rec.price_unit = rec.price_unit
    #        self._cr.commit() 

    @api.depends('product_id', 'product_uom', 'product_uom_qty')
    def _compute_price_unit(self):
        for line in self:
            # as case product doesn't have pricelist so we use lst_price else it will become 0
            if line.product_id.is_case_product and not line.is_included_case:
                product_price_dict = (self.env['kits.b2b.multi.currency.mapping'].with_context(from_order_line=True).get_product_price(line.order_id.partner_id.id,line.product_id.ids,order_id=line.order_id) or {}).get(line.product_id.id,{})
                product_price = product_price_dict.get('price')
                line.price_unit = product_price
            # check if there is already invoiced amount. if so, the price shouldn't change as it might have been
            # manually edited
            # if line.qty_invoiced > 0:
            #     continue
            # if not line.product_uom or not line.product_id or not line.order_id.pricelist_id:
            #     line.price_unit = 0.0
            # else:
                # else:
                #     price = line.with_company(line.company_id)._get_display_price()
                # line.price_unit = line.product_id._get_tax_included_unit_price(
                #     line.company_id,
                #     line.order_id.currency_id,
                #     line.order_id.date_order,
                #     'sale',
                #     fiscal_position=line.order_id.fiscal_position_id,
                #     product_price_unit=price,
                #     product_currency=line.currency_id
                # )

    @api.onchange('order_id.state','state','price_unit','unit_discount_price','product_id','product_uom_qty')
    def onchange_restrict_case(self):
        for rec in self:
            if self._context.get('from_sale_order') and rec.order_id.state not in ['draft','sent','received']:
                raise UserError('You cannot add case')

    def _prepare_invoice_line(self, **optional_values):
        self.ensure_one()
        res = super(SaleOrderLine, self)._prepare_invoice_line(**optional_values)
        # add value in account move line for included case.
        res['is_included_case'] = self.is_included_case
        return res
    
    def unlink(self):
        for rec in self:
            if rec.state in ['draft','sent','received']:
                case_product_id = self.product_id.case_product_id
                if case_product_id:
                    qty = sum(self.order_id.non_case_order_line.filtered(lambda x: x.product_id.case_product_id==case_product_id).mapped('product_uom_qty')) - rec.product_uom_qty
                    case_order_line_id = self.order_id.case_order_line.filtered(lambda x : x.product_id==case_product_id)
                    if case_order_line_id:
                        case_order_line_id.product_uom_qty = qty
        
        return super(SaleOrderLine,self).unlink()
                

    # @api.onchange('product_uom_qty')
    # def update_order_line_case_qty(self):
    #     for rec in range(len(self)):
    #         rec = self[rec]
    #         if rec.state in ['draft','sent','received']:
    #             case_product_id = rec.product_id.case_product_id
    #             if case_product_id:
    #                 qty = sum(rec.order_id.non_case_order_line.filtered(lambda x: x.product_id.case_product_id==case_product_id).mapped('product_uom_qty'))
    #                 case_order_line_id = rec.order_id.case_order_line.filtered(lambda x : x.product_id==case_product_id)
    #                 if case_order_line_id:
    #                     case_order_line_id.write({
    #                        'product_uom_qty' : qty 
    #                     }) 
