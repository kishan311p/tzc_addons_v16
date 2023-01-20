from odoo import api, fields, models, _
from odoo.exceptions import UserError
from datetime import datetime,timedelta

class kits_multi_website_sale_order_line(models.Model):
    _name = "kits.multi.website.sale.order.line"
    _description = "Kits Multi Website Sale Order Line"

    name = fields.Char('name',related='product_id.variant_name',store=True)
    original_price = fields.Float("Original Price")
    discounted_unit_price = fields.Float("Our Frame Price")
    discounted_glass_price = fields.Float("Our Glass Price")
    product_id = fields.Many2one("product.product", "Product")
    unit_price = fields.Float("Frame Price")
    quantity = fields.Integer("Quantity", default=1)
    subtotal = fields.Float("Subtotal", compute="_compute_subtotal")
    sale_order_id = fields.Many2one('kits.multi.website.sale.order','Sale Order')
    power_type_id = fields.Many2one('kits.multi.website.power.type',string="Power Type",domain="[('website_id','=',website_id)]")
    glass_type_id = fields.Many2one("kits.multi.website.glass.type","Glass Type")
    glass_price = fields.Float("Glass Price")
    left_eye_power = fields.Float("Left Eye Power")
    right_eye_power = fields.Float("Right Eye Power")
    discount = fields.Integer("Discount(%)")
    tax_ids = fields.Many2many("account.tax","multi_website_sale_order_account_tax_rel","sale_order_id","account_tax_id","Taxes")
    discount_amount = fields.Float("Discount Amount")
    promo_code = fields.Char("Promo Code")
    is_shipping_product = fields.Boolean("Is Shipping Product",related="product_id.is_shipping_product", store=True)
    promo_code_amount = fields.Float("Promo Code Amount")
    tax_amount = fields.Float("Tax Amount")
    currency_id = fields.Many2one("res.currency", "Currency")
    tax_percent = fields.Float("Tax Percent")
    website_id = fields.Many2one("kits.b2c.website", "Website",related='sale_order_id.website_id',store=True)
    is_power_glass = fields.Boolean('Is Power Glass',related='power_type_id.is_power_glass',store=True)
    is_select_for_lenses = fields.Boolean('Is Allow For Add Lenses')
    pricing_expiration_time = fields.Datetime('Pricing Expiration Time')
    prescription_id = fields.Many2one('kits.multi.website.prescription', string='Prescription')
    prescription_state = fields.Selection([('unverified', 'Unverified'),('verified', 'Verified')], string='state',compute="_change_prescription_state")
    prescription_filename = fields.Char('Filename',related='prescription_id.file_name')
    state = fields.Selection([('draft','Added In The Cart'), ('sale','Order Placed'),('waiting_for_prescription','Waiting For Prescription'),('prescription_added','Prescription Added'), ('glass_add','Sent for Adding Glasses'), ('receive','Frame Received'),('ready_to_ship','Ready To Ship'),('ship','Ship'), ('shipped','Shipped'), ('cancel','Cancel'),('requested','Returned Requested'),('return','Returned'),('rejected','Rejected'), ('done','Order Completed')], default="draft", string="State")
    show_add_glass_button =  fields.Boolean('show add glass button')
    show_receive_button =  fields.Boolean('show receive button')
    
    return_request_date = fields.Datetime("Return Request Date")
    return_approved_date = fields.Datetime("Return Approved Date")
    return_pickup_date = fields.Datetime("Return Pikcup Date")
    return_received_date = fields.Datetime("Return Receive Date")
    return_examined_date = fields.Datetime("Return Examine Date")
    return_returned_date = fields.Datetime("Return Return Date")
    return_refunded_date = fields.Datetime("Return Refund Date")
    return_scrapped_date = fields.Datetime("Return Scrap Date")
    return_rejected_date = fields.Datetime("Return Rejected Date")
    is_return_available = fields.Boolean(compute='_compute_is_return_available', string='is_return_available',store=True)

    def _change_prescription_state(self):
        for rec in self:
            rec.prescription_state = rec.prescription_id.state if rec.prescription_id else False

    @api.depends('state','return_scrapped_date','return_refunded_date','return_returned_date', 'return_examined_date','return_received_date','return_pickup_date','return_approved_date','return_request_date')
    def _compute_is_return_available(self):
        for record in self:
            if record.website_id.return_product_days and record.sale_order_id.expected_delivry_date and ((fields.datetime.now()- record.sale_order_id.expected_delivry_date).days < record.website_id.return_product_days):
                record.is_return_available = True
            else:
                record.is_return_available = False
            
    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_sale_order_line, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        elif self._context.get('params') and self._context.get('params').get('id') and self._context.get('params').get('model') :
            if self._context.get('params').get('model') == 'kits.multi.website.sale.order':
                website_id  = self.env[self._context.get('params').get('model')].sudo().browse(self._context.get('params').get('id')).website_id
                res['website_id'] =  website_id.id if website_id else False
        return res

    @api.depends('unit_price','quantity','glass_type_id','glass_price', 'discount','tax_ids','discounted_glass_price','discounted_unit_price','promo_code')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = 0
            record.discount_amount = 0
            record.tax_amount = 0
            record.tax_percent = 0
            record.original_price  = (record.unit_price + record.glass_price) * record.quantity
            record.subtotal  = ((record.discounted_unit_price + record.discounted_glass_price) * record.quantity) -  record.promo_code_amount
            record.discount_amount =  (((record.unit_price + record.glass_price)-(record.discounted_unit_price + record.discounted_glass_price)) * record.quantity)
            # record.discount_amount = record.promo_code_amount
            # if record.discounted_unit_price or record.quantity or record.glass_type_id:
            #     record.subtotal = (record.discounted_unit_price + record.discounted_glass_price) * record.quantity
            if record.tax_ids:
                fpos_id = self.env['account.fiscal.position']._get_fpos_by_region(country_id=record.sale_order_id.customer_id.country_id.id, state_id=record.sale_order_id.customer_id.state_id.id, zipcode=False, vat_required=False)
                if fpos_id:
                    fpos_tax = fpos_id.map_tax(record.tax_ids)
                    record.tax_percent = fpos_tax.amount
                    tax = fpos_tax.compute_all(record.discounted_unit_price + record.discounted_glass_price, quantity=record.quantity, currency=False,
                                                    product=False, partner=False)
                    if 'total_included' in tax.keys() and tax.get('total_included'):    
                        record.tax_amount = tax.get('total_included') - record.subtotal
                        # record.subtotal = tax.get('total_included')
            # if record.discount: 
            #     discount = (record.discount / 100) * record.subtotal
            #     record.discount_amount = discount
            #     record.subtotal -= discount



    @api.onchange('product_id','glass_type_id')
    def _get_product_price(self):
        for record in self:
            unit_price =  0.0
            discounted_unit_price =  0.0
            glass_price = 0.00
            discounted_glass_price = 0.00
            if record.website_id and record.product_id and record.website_id.sale_pricelist_id and record.sale_order_id and record.sale_order_id.customer_id:
                unit_price = record.website_id.msrp_pricelist_id._get_product_price(record.product_id, record.quantity, record.product_id.uom_id)
                discounted_unit_price = record.website_id.sale_pricelist_id._get_product_price(record.product_id, record.quantity, record.product_id.uom_id)
            if record.glass_type_id:
                glass_price = record.glass_type_id.price
                discounted_glass_price = record.glass_type_id.discounted_price
            record.unit_price = unit_price
            record.discounted_unit_price = discounted_unit_price
            record.glass_price = glass_price
            record.discounted_glass_price = discounted_glass_price
            record._compute_tax_id()
            record._convert_rates()

    @api.onchange('power_type_id')
    def _onchange_power_type_id(self):
        for record in self:
            glass_type_ids = self.env['kits.multi.website.glass.type'].search([('website_id','=',record.sale_order_id.website_id.id)])
            if record.power_type_id:
                glass_type_ids = self.env['kits.multi.website.glass.type'].search([('power_type_id','=',record.power_type_id.id),('website_id','=',record.website_id.id)],limit=1)

            return{'domain': {'glass_type_id': [('id','in',glass_type_ids.ids)]}}

    @api.onchange("quantity")
    def check_qty(self):
        for record in self:
            if record.quantity < 1:
                raise UserError("Quantity of Product must at least be 1")

    def _convert_rates(self):
        for record in self:
            currency_mapping_id = self.env['kits.currency.mapping'].search([('currency_id','=',record.sale_order_id.currency_id.id)])
            if currency_mapping_id:
                to_currency = currency_mapping_id.currency_id
                record.unit_price = round(currency_mapping_id._convert_rates(record.product_id.list_price, to_currency),2) if record.product_id else 00
                record.glass_price = round(currency_mapping_id._convert_rates(record.glass_type_id.price, to_currency),2) if record.glass_type_id else 00
                record.discounted_glass_price = round(currency_mapping_id._convert_rates(record.glass_type_id.discounted_price, to_currency),2) if record.glass_type_id else 00
                record.discounted_unit_price = round(currency_mapping_id._convert_rates( record.website_id.sale_pricelist_id._get_product_price(record.product_id, record.quantity, record.product_id.uom_id), to_currency),2) if record.product_id else 00
    
    def action_download_prescription(self):
        self.ensure_one()
        if self.prescription_id.prescription_file_data:
            f_name = (self.prescription_id.file_name or 'file').replace(' ','_')
            wizard = self.env['kits.file.download.wizard'].create({
                'file': self.prescription_id.prescription_file_data
            })
            active_id = wizard.id
            return {
                    'type': 'ir.actions.act_url',
                    'url': 'web/content/?model=kits.file.download.wizard&download=true&field=file&id=%s&filename=%s' % (active_id, f_name),
                    'target': 'self',
            }
        else:
            raise UserError(_('File Data not Found'))
    

    def _compute_tax_id(self):
        for line in self:
            fpos = line.sale_order_id.fiscal_position_id or line.sale_order_id.customer_id.property_account_position_id
            taxes = line.product_id.taxes_id
            line.tax_ids = fpos.map_tax(taxes) if fpos else taxes

    def add_priscription(self):
        self.ensure_one()
        return{
            'name': ('Prescription'),
            'res_model': 'kits.add.prescription.wizard',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('kits_multi_website.kits_add_prescription_wizard_form_view').id, 'form')],
            'context': {'default_customer_id':self.sale_order_id.customer_id.id},
            'target': 'new',
        }
    
    def sent_for_add_glass(self):
        for record in self:
            if record.is_power_glass and record.prescription_id and record.prescription_id.state == 'unverified':
                raise UserError(_('Please verify prescription'))
            record.state = 'glass_add'
            record.show_add_glass_button = False
            record.show_receive_button = True
            if all(record.sale_order_id.sale_order_line_ids.mapped(lambda line :True if line.state == 'glass_add' or (not line.power_type_id and not line.power_type_id and not line.is_power_glass)  else False)):
                record.sale_order_id.state= 'glass_add'

    def receive_glass(self):
        for record in self:
            record.state = 'receive'
            record.show_receive_button = False

            if all(record.sale_order_id.sale_order_line_ids.mapped(lambda line :True if line.state == 'receive' or (not line.power_type_id and not line.power_type_id and not line.is_power_glass)  else False)):
                record.sale_order_id.state= 'receive'
                if not record.sale_order_id.expected_delivry_date:
                    if record.sale_order_id.paid_shipping_cost_id and not record.sale_order_id.expected_delivry_date :
                        record.sale_order_id.expected_delivry_date = datetime.now() + timedelta(days=record.sale_order_id.paid_shipping_cost_id.days)
                    else:
                        if record.sale_order_id.shipping_rule_id:
                            record.sale_order_id.expected_delivry_date = datetime.now() + timedelta(days=record.sale_order_id.shipping_rule_id.free_shipping_days)
    
    @api.constrains('promo_code')
    def _constrains_promo_code_amount(self):
        for record in self:
            if record.promo_code:
                mapping_id = self.env['kits.currency.mapping'].sudo().search([('currency_id','=',record.currency_id.id)],limit=1)
                coupon_id = self.env['kits.multi.website.coupon'].search([('promo_code','=',record.promo_code)],limit=1)
                promo_code_amount = (record.quantity * (record.discounted_glass_price+record.discounted_unit_price)) * (coupon_id.discount_amount*0.01) if coupon_id.apply_on=='percentage' else coupon_id.discount_amount
                record.promo_code_amount =round( promo_code_amount *  mapping_id.currency_rate,2) if mapping_id else promo_code_amount
            else:
                record.promo_code_amount =0

    def name_get(self):
        result = []
        for record in self:
            name = ''
            if record.product_id:
                name = record.product_id.variant_name
            result.append((record.id,name))
        return result    

    def prescription_wizard(self):
        for record in self:
            return{
                'name': ('Prescription'),
                'res_model': 'kits.multi.website.prescription',
                'type': 'ir.actions.act_window',
                'views': [(self.env.ref('kits_multi_website.kits_multi_website_prescription_form_view_1').id, 'form')],
                'res_id' :record.prescription_id.id,
                'target': 'new',
            }
