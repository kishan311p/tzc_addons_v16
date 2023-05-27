from odoo import api, fields, models, _
from odoo.exceptions import UserError
import json
from odoo.tools.safe_eval import safe_eval
from lxml import etree
from datetime import datetime,timedelta

class kits_multi_website_sale_order(models.Model):
    _name = "kits.multi.website.sale.order"
    _inherit = ['mail.thread']
    _description = "Kits Multi Website Sale Order"
    _order = "id desc"

    name = fields.Char("Name")
    customer_id = fields.Many2one("kits.multi.website.customer", "Customer") 
    order_placed_date = fields.Datetime("Order Placed Date")
    order_date = fields.Datetime("Order Confirmed Date")
    expected_delivry_date = fields.Datetime("Expected Delivery Date")
    total = fields.Float("Total",compute="_compute_total")
    sale_order_line_ids = fields.One2many('kits.multi.website.sale.order.line','sale_order_id','Sale Order Line')
    state = fields.Selection([('quotation','Quotation'),('order_placed','Order Placed'),('waiting_for_prescription','Waiting For Prescription'),('prescription_added','Prescription Added'), ('glass_add','Sent for Adding Glasses'), ('receive','Frame Received'),('ready_to_ship','Ready To Ship'),('ship','Ship'), ('shipped','Shipped'), ('cancel','Cancel'), ('return','Returned'), ('scrap','Scrap'), ('done','Done')], default="quotation", string="State")
    website_id = fields.Many2one("kits.b2c.website", "Website")
    has_moves = fields.Boolean("Has Moves",compute="_compute_moves_and_invoice")
    has_invoice = fields.Boolean("Has Invoice",compute="_compute_moves_and_invoice")
    amount_without_discount = fields.Float("Subtotal",compute="_compute_all")
    amount_discount = fields.Float("Discount",compute="_compute_all")
    amount_tax = fields.Float("Tax",compute="_compute_all")
    fiscal_position_id = fields.Many2one("account.fiscal.position", "Fiscal Position")
    promo_code = fields.Char("Promo Code")
    promo_code_discount = fields.Float("Promo Code Discount")
    discounted_shipping_cost = fields.Float("Discounted Shipping Cost")
    shipping_discount = fields.Float("Shipping Discount")
    shipping_rule_id = fields.Many2one("kits.free.shipping.rule", "Free Shipping Rule")
    currency_id = fields.Many2one("res.currency", "Currency", related="customer_id.preferred_currency_id",store=True)
    invoice_state = fields.Selection([('not_inv','Not Invoice'),('paid','Paid'),('not_paid','Not Paid')],default='not_inv',string='Invoice Status',copy=False)

    # customer_address = fields.Text("Address",related="invoice_address_id.address")
    customer_street = fields.Char("Street",related="invoice_address_id.street")
    customer_street2 = fields.Char("Street2",related="invoice_address_id.street2")
    customer_city = fields.Char("City",related="invoice_address_id.city")
    customer_zip = fields.Char("Zip",related="invoice_address_id.zip")
    customer_state_id = fields.Many2one("res.country.state", "State",related="invoice_address_id.state_id")
    customer_country_id = fields.Many2one("res.country", "Country",related="invoice_address_id.country_id")
    customer_phone = fields.Char("Phone",related="invoice_address_id.phone")


    # delivery_address = fields.Text("Address",related="delivery_address_id.address")
    delivery_street = fields.Char("Street",related="delivery_address_id.street")
    delivery_street2 = fields.Char("Street2",related="delivery_address_id.street2")
    delivery_city = fields.Char("City",related="delivery_address_id.city")
    delivery_zip = fields.Char("Zip",related="delivery_address_id.zip")
    delivery_state_id = fields.Many2one("res.country.state", "State",related="delivery_address_id.state_id")
    delivery_country_id = fields.Many2one("res.country", "Country",related="delivery_address_id.country_id")
    delivery_phone = fields.Char("Phone",related="delivery_address_id.phone")

    delivery_address_id = fields.Many2one("kits.multi.website.address","Delivery")
    invoice_address_id = fields.Many2one("kits.multi.website.address","Invoice Address")
    paid_shipping_cost_id = fields.Many2one('kits.paid.shipping.rule.line','Delivey Days')
    delivery_day_count = fields.Integer('Delivery Day Count',compute="_delivery_day_count")
    user_id = fields.Many2one('res.users','Salesperson')
    return_request_ids = fields.One2many('kits.multi.website.return.request', 'sale_order_id', string='return_request_ids')
    return_request_count = fields.Integer('Return Request Count',compute="_delivery_day_count")

    def check_is_return_available(self):
        for rec in self:
            for line in rec.sale_order_line_ids:
                if line.state in ['ready_to_ship','done','ship','shipped','requested','return','rejected']:
                    line._compute_is_return_available()
        return {}


    @api.depends('paid_shipping_cost_id','expected_delivry_date','shipping_rule_id')
    def _delivery_day_count(self):
        for rec in self:
            delivery_day_count = 0
            if rec.expected_delivry_date:
                if rec.paid_shipping_cost_id and rec.state not in ['quotation','order_placed','waiting_for_prescription','prescription_added','glass_add']:
                    delivery_day_count = (rec.expected_delivry_date - fields.datetime.now()).days
                elif rec.shipping_rule_id and rec.state not in ['quotation','order_placed','waiting_for_prescription','prescription_added','glass_add']:
                    delivery_day_count =(rec.expected_delivry_date - fields.datetime.now()).days
                else:
                    delivery_day_count = 0
            
            rec.delivery_day_count = delivery_day_count
            rec.return_request_count = len(rec.return_request_ids)

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        for record in self:
            if record.customer_id and record.customer_id.address_ids:
                record.invoice_address_id= record.customer_id.address_ids.filtered(lambda cus:cus.is_invoice_address_default == True) or record.customer_id.address_ids[0]

                record.delivery_address_id= record.customer_id.address_ids.filtered(lambda cus:cus.is_delivery_address_default == True) or record.customer_id.address_ids[0]

    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_sale_order, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
            if website_id:
                res['user_id'] = website_id.user_id.id
        return res

    # @api.onchange('shipping_cost')
    # def _set_discount_shipping_cost(self):
    #     for record in self:
    #         record.discounted_shipping_cost = record.shipping_cost

    @api.onchange('currency_id')
    def _set_currency_to_order_lines(self):
        for record in self:
            if record.sale_order_line_ids:
                record.sale_order_line_ids.write({
                    'currency_id': record.currency_id.id,
                })
                record.sale_order_line_ids._convert_rates()


    @api.onchange('sale_order_line_ids')
    def _onchange_order_line(self):
        for record in self:
            record.sale_order_line_ids.currency_id = record.currency_id

    @api.model
    def create(self, vals):
        res = super(kits_multi_website_sale_order, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('unique.multi.website.sale.order.sequence')
        for rec in res:
            order_id = self.search([('customer_id','=',rec.customer_id.id),('state','=','quotation'),('id','!=',rec.id)],limit=1)
            if order_id:
                raise UserError(_('%s order is already found in system so you can not create another order.'%(order_id.name)))
                
        return res

    @api.depends('sale_order_line_ids.subtotal','discounted_shipping_cost')
    def _compute_total(self):
        for record in self:
            record.total = 0
            if record.sale_order_line_ids:
                record.total = sum(record.sale_order_line_ids.mapped('subtotal')) + record.discounted_shipping_cost if record.discounted_shipping_cost else sum(record.sale_order_line_ids.mapped('subtotal'))

    def action_pack_product(self):
        for record in self:
            all_line_state = []
            for line in record.sale_order_line_ids:
                line.state = 'ready_to_ship'
                all_line_state.append(line.state)
            if  'waiting_for_prescription' in all_line_state:
                record.state = 'waiting_for_prescription'
            if 'prescription_added' in all_line_state:
                record.state = 'prescription_added'
            else:
                record.state = 'ready_to_ship'
                if record.paid_shipping_cost_id and not record.expected_delivry_date :
                    record.expected_delivry_date = datetime.now() + timedelta(days=record.paid_shipping_cost_id.days)
                else:
                    if record.shipping_rule_id:
                        record.expected_delivry_date = datetime.now() + timedelta(days=record.shipping_rule_id.free_shipping_days)



    def action_confirm(self):
        for record in self:
            state_list = []
            unavailable_products = []
            error_list = []
            update_delivry_date = True
            if not record.sale_order_line_ids:
                raise UserError("Please add a product first!")
            for line in record.sale_order_line_ids:
                line.state = 'sale' if (not line.power_type_id and not line.glass_type_id and not line.is_power_glass ) or (not line.is_select_for_lenses) or ((line.power_type_id and line.glass_type_id and not line.is_power_glass))else 'waiting_for_prescription' if not line.prescription_id else 'prescription_added'
                state_list.append(line.state)
                if line.product_id.qty_available == 0 and line.product_id.type == 'product':
                    unavailable_products.append(line.product_id)
                    error_list.append(f"No Quantity is available for product {line.product_id.display_name}")
                elif line.quantity > line.product_id.qty_available and line.product_id.type == 'product':
                    unavailable_products.append(line.product_id)
                    error_list.append(f"Only {line.product_id.qty_available} quantity is available for Product {line.product_id.display_name}")
                if (line.is_select_for_lenses and not line.is_power_glass and line.glass_type_id and line.power_type_id) or (line.is_power_glass and line.prescription_id):
                    line.show_add_glass_button = True
                if line.state != 'sale':
                    update_delivry_date = False
                if not unavailable_products:
                    vals = {
                        'date': fields.date.today(),
                        'location_id': self.env['stock.location'].search([('name','=','Stock')]).id,
                        'location_dest_id': self.env['stock.location'].search([('name','=','Customers')]).id,
                        'name': line.product_id.name,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_id.uom_id.id,
                        'product_uom_qty': line.quantity,
                        'company_id': self.env.user.company_id.id,
                        'sale_order_id': record.id,
                        'origin': record.name,
                        'sale_order_line_id' : line.id

                    }
                    stock_move_id = self.env['stock.move'].create(vals)
                    stock_move_id._action_confirm()
                    stock_move_id._action_assign()
                    stock_move_id.write({'quantity_done': line.quantity})
                    stock_move_id._action_done()
            if error_list:
                raise UserError("\n".join(error_list))
            
            free_shipping_rule_ids = self.env['kits.free.shipping.rule'].search([('country_ids','in',record.customer_id.country_id.id)])
            shipping_rules_list = []
            shipping_rule_id = False
            if free_shipping_rule_ids:
                for shipping_rule in free_shipping_rule_ids:
                    pass_through = self.check_shipping_rule_validity(shipping_rule)
                    if pass_through:
                        shipping_rules_list.append(shipping_rule)
                if len(shipping_rules_list) == 1:
                    shipping_rule_id = shipping_rules_list[0]    
            else:
                universal_shipping_rule_id = self.env['kits.free.shipping.rule'].search([('country_ids','=',False)])
                if universal_shipping_rule_id:
                    universal_shipping_rule_id_pass_through = self.check_shipping_rule_validity(universal_shipping_rule_id)
                    if universal_shipping_rule_id_pass_through:
                        shipping_rule_id = universal_shipping_rule_id
            state = 'order_placed'
            if 'prescription_added' in state_list:
                state = 'prescription_added'
            if 'waiting_for_prescription' in state_list:
                state = 'waiting_for_prescription'

            if update_delivry_date:
                if record.paid_shipping_cost_id and not record.expected_delivry_date :
                    record.expected_delivry_date = datetime.now() + timedelta(days=record.paid_shipping_cost_id.days)
                else:
                    if record.shipping_rule_id:
                        record.expected_delivry_date = datetime.now() + timedelta(days=record.shipping_rule_id.free_shipping_days)

            record.write({
                # 'state' : 'sale', 
                'state':  state  ,
                'order_date': fields.datetime.now(),
                'shipping_rule_id': shipping_rule_id
            })
            if not record.order_placed_date:
                record.write({'order_placed_date': fields.datetime.now()})
        return True 
            
    def check_shipping_rule_validity(self,shipping_rule):
        pass_through = True
        if shipping_rule.start_date and shipping_rule.end_date:
            if not fields.date.today() >= shipping_rule.start_date or not fields.date.today() <= shipping_rule.end_date:
                pass_through = False
        elif shipping_rule.start_date and not shipping_rule.end_date:
            if fields.date.today() < shipping_rule.start_date:
                pass_through = False
        elif not shipping_rule.start_date and shipping_rule.end_date:
            if fields.date.today() > shipping_rule.end_date: 
                pass_through = False
        return pass_through

    def action_reset_to_quotation(self):
        for record in self:
            record.write({
                'state' : 'quotation', 
            })

    def action_cancel(self):
        for record in self:
            move_ids = self.env['stock.move'].search([('sale_order_id','=',record.id), ('state','!=','cancel')])
            move_ids.write({
                'quantity_done': 0,
            })
            move_ids._action_cancel()
            invoice_ids = self.env['kits.multi.website.invoice'].search([('sale_order_id','=',record.id), ('state','not in',['cancel','paid'])])
            invoice_ids.write({
                'state': 'cancel',
            })
            record.shipping_rule_id = False
            record.discounted_shipping_cost = 0
            record.shipping_discount = 0
            record.write({
                'state' : 'cancel', 
            })
            record.sale_order_line_ids.write({
                'state' : 'cancel', 
            })

    def _compute_moves_and_invoice(self):
        for record in self:
            record.has_moves = False
            record.has_invoice = False
            move_ids = self.env['stock.move'].search([('sale_order_id','=',record.id)],limit=1)
            if move_ids:
                record.has_moves = True
            invoice_ids = self.env['kits.multi.website.invoice'].search([('sale_order_id','=',record.id)],limit=1)
            if invoice_ids:
                record.has_invoice = True
    
    def compute_all(self):
        for record in self:
            record._compute_all()
        return True

    @api.depends('sale_order_line_ids.tax_ids','sale_order_line_ids','sale_order_line_ids.discount_amount','sale_order_line_ids.tax_amount', 'promo_code_discount')
    def _compute_all(self):
        for record in self:
            amount_discount = 0.00
            amount_tax =  0.00
            amount_without_discount =  0.00
            promo_code_discount =  0.00
            line_ids = record.sale_order_line_ids
            for line in range(0,len(line_ids)):
                line = line_ids[line]
                amount_discount += line.discount_amount
                amount_tax += line.tax_amount
                promo_code_discount += line.promo_code_amount
                amount_without_discount += ((line.unit_price+line.glass_price)* line.quantity)
                # record.amount_discount = sum(record.sale_order_line_ids.mapped('discount_amount'))
                # record.amount_tax = sum(record.sale_order_line_ids.mapped('tax_amount'))
                # record.amount_without_discount = sum(record.sale_order_line_ids.mapped("subtotal")) + record.amount_discount - record.amount_tax   
            # record.amount_discount += record.promo_code_discount + record.shipping_discount if record.shipping_discount else record.promo_code_discount
            record.amount_discount = amount_discount + promo_code_discount
            record.total = amount_without_discount + amount_tax + record.discounted_shipping_cost - record.promo_code_discount - amount_discount
            record.amount_tax = amount_tax  
            record.promo_code_discount = promo_code_discount  
            record.amount_without_discount = amount_without_discount

    def action_open_moves(self):
        tree_view_id = self.env.ref('stock.view_move_tree')
        form_view_id = self.env.ref('stock.view_move_form')
        return{
            'name': ('Stock Moves'),
            'res_model': 'stock.move',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id.id, 'tree'), (form_view_id.id, 'form')],
            'domain': [('sale_order_id','=',self.id)],
            'target': 'current',
        }

    def action_sent_for_adding_glasses(self):
        for record in self:
            record.write({
                'state': 'glass_add'
            })
            record.sale_order_line_ids.write({'state': 'glass_add',
                'show_add_glass_button': False,
                'show_receive_button': True})


    def action_receive_frame(self):
        for record in self:
            record.write({
                'state': 'receive',
            }) 
            if  all(record.sale_order_line_ids.mapped(lambda line :True if line.state == 'receive' or line.state == 'glass_add' or line.state == 'sale'  else False)):
                record.sale_order_line_ids.write({'state': 'receive','show_receive_button': False})
                if not record.expected_delivry_date:
                    if record.paid_shipping_cost_id and not record.expected_delivry_date :
                        record.expected_delivry_date = datetime.now() + timedelta(days=record.paid_shipping_cost_id.days)
                    else:
                        if record.shipping_rule_id:
                            record.expected_delivry_date = datetime.now() + timedelta(days=record.shipping_rule_id.free_shipping_days)
            else:
                raise UserError(_('All lines should be sent for adding glasses or receive state.'))


    def action_create_invoice(self):
        for record in self:
            if record.state != 'order_placed':
                record.state='done'
            invoice_lines_list = []
            for line in record.sale_order_line_ids:
                if record.state != 'order_placed':
                    line.state = 'done'
                invoice_lines_list.append((0,0,{
                    'product_id': line.product_id.id,
                    'unit_price': line.unit_price,
                    'quantity': line.quantity,
                    'power_type_id': line.power_type_id.id,
                    'glass_type_id': line.glass_type_id.id,
                    'glass_price': line.glass_price,
                    'left_eye_power': line.left_eye_power,
                    'right_eye_power': line.right_eye_power,
                    'discount': line.discount,
                    'tax_ids': [(6,0,line.tax_ids.ids)],
                    'tax_amount': line.tax_amount,
                    'discount_amount': line.discount_amount,
                }))
            invoice_vals = {
                'customer_id': record.customer_id.id,
                'invoice_date': fields.date.today(),
                'sale_order_id': record.id,
                'invoice_line_ids': self.env.context.get('product_list') if 'product_list' in self.env.context.keys() and self.env.context.get('product_list') else invoice_lines_list,
                # 'shipping_cost': 0 if ("invoice_type" in self.env.context.keys() and self.env.context.get("invoice_type") == 'refund') else record.shipping_cost,
                'fiscal_position_id': record.fiscal_position_id.id if record.fiscal_position_id else False,
                'promo_code_discount': record.promo_code_discount,
                'discounted_shipping_cost': 0 if ("invoice_type" in self.env.context.keys() and self.env.context.get("invoice_type") == 'refund') else record.discounted_shipping_cost,
                'shipping_discount': 0 if ("invoice_type" in self.env.context.keys() and self.env.context.get("invoice_type") == 'refund') else record.shipping_discount,
                'website_id': record.website_id.id if record.website_id else False,
                'invoice_type': 'invoice',
            }
            if ('invoice_type' in self.env.context.keys() and self.env.context.get('invoice_type')) and ('refund_amount' in self.env.context.keys() and self.env.context.get('refund_amount')):
                invoice_vals.update({
                    'invoice_type': self.env.context.get('invoice_type'),
                })
                invoice_id = self.env['kits.multi.website.invoice'].with_context(refund_amount=self.env.context.get('refund_amount')).create(invoice_vals) 
            else:
                invoice_id = self.env['kits.multi.website.invoice'].create(invoice_vals) 
            if invoice_id.invoice_type == 'invoice':
                record.write({
                    'invoice_state': 'not_paid',
                })
        form_view_id = self.env.ref("kits_multi_website.kits_multi_website_invoice_form_view")
        return{
            'name': ('Invoices'),
            'res_model': 'kits.multi.website.invoice',
            'type': 'ir.actions.act_window',
            'views': [(form_view_id.id, 'form')],
            'res_id': invoice_id.id,
            'target': 'current',
        }

    def action_open_invoices(self):
        form_view_id = self.env.ref("kits_multi_website.kits_multi_website_invoice_form_view")
        tree_view_id = self.env.ref("kits_multi_website.kits_multi_website_invoice_tree_view")
        inv_id = self.env['kits.multi.website.invoice'].search([('sale_order_id','=',self.id)],limit=1)
        return{
            'name': ('Invoices'),
            'res_model': 'kits.multi.website.invoice',
            'type': 'ir.actions.act_window',
            'views': [(form_view_id.id, 'form')],
            'res_id':inv_id.id,
            'target': 'current',
        }

    @api.onchange('customer_id')
    def _onchange_customer(self):
        for record in self:
            fpos_id = self.env['account.fiscal.position']._get_fpos_by_region(country_id=record.customer_id.country_id.id, state_id=record.customer_id.state_id.id, zipcode=False, vat_required=False)
            if fpos_id:
                record.fiscal_position_id = fpos_id
            record.sale_order_line_ids._compute_tax_id()
            record.sale_order_line_ids._compute_subtotal()
            record._compute_all()

    def action_apply_promo_code(self):
        for record in self:
            if not record.promo_code:
                raise UserError("Please Enter Promo Code!")
            if not record.sale_order_line_ids:
                raise UserError("Please add a product first!")
            coupon_id = self.env['kits.multi.website.coupon'].search([('promo_code','=',record.promo_code)],limit=1)
            if coupon_id:
                if coupon_id.start_date and coupon_id.end_date:
                    if not fields.date.today() >= coupon_id.start_date or not fields.date.today() <= coupon_id.end_date:
                        raise UserError("Coupon Validity has Expired!")
                elif coupon_id.start_date and not coupon_id.end_date:
                    if fields.date.today() < coupon_id.start_date:
                        raise UserError('Coupon is not Eligible')
                elif not coupon_id.start_date and coupon_id.end_date:
                    if fields.date.today() > coupon_id.end_date: 
                        raise UserError('Coupon is not Eligible')
                    
                customer_ids = self.env['kits.multi.website.customer'].search([])
                product_ids = self.env['product.product'].search([])
                if coupon_id.coupon_customer_domain:
                    domain = safe_eval(coupon_id.coupon_customer_domain)
                    customer_ids = self.env['kits.multi.website.customer'].search(domain)
                if coupon_id.coupon_product_domain:
                    domain = safe_eval(coupon_id.coupon_product_domain)
                    product_ids = self.env['product.product'].search(domain)
                
                if record.customer_id not in customer_ids:
                    raise UserError(f"{record.customer_id.name} is not eligible for this Promo Code!")

                customer_coupon_line_id = self.env['kits.multi.website.coupon.customer.line'].search([('customer_id','=',record.customer_id.id), ('coupon_id','=',coupon_id.id)])
                if coupon_id.can_be_used and customer_coupon_line_id.coupon_used_count and customer_coupon_line_id.coupon_used_count >= coupon_id.can_be_used:
                    raise UserError(f"You can only apply this Promo Code for {coupon_id.can_be_used} times!")

                if coupon_id.min_purchase and record.amount_without_discount < coupon_id.min_purchase:
                    raise UserError(f"Minimum Purchase for this Coupon to be eligible is {coupon_id.min_purchase}")
                
                product_list = []
                total_product_qty = 0
                line_dict = {}
                for line in record.sale_order_line_ids:
                    if not line.is_shipping_product:
                        if line.promo_code and line.promo_code == coupon_id.promo_code:
                            raise UserError("%s coupon apply only once."%(line.promo_code))    
                        else:
                            if line.product_id.id in line_dict.keys():
                                line_dict[line.product_id.id].append(line)
                            else:
                                line_dict[line.product_id.id] = [line]

                for key in line_dict.keys():
                    total_qty =0
                    min_qty = coupon_id.min_qty
                    for line in line_dict[key]:
                        if line.product_id.id in product_ids.ids:
                            if min_qty:
                                if total_qty+line.quantity <= min_qty :
                                    product_list.append(line.product_id.id)
                                else:
                                    raise UserError("Coupon is not Eligible because of less quantity!")

                            else:
                                line.promo_code = coupon_id.promo_code
                                product_list.append(line.product_id.id)

                            total_product_qty += line.quantity

                if not product_list:
                    raise UserError("No Product Eligible for this Promo Code")
                
                # if coupon_id.min_qty and total_product_qty < coupon_id.min_qty:
                #     raise UserError("Coupon is not Eligible because of less quantity!")
            
                # record.promo_code_discount = coupon_id.discount_amount*0.01 if coupon_id.apply_on == 'percentage' else coupon_id.discount_amount
                if customer_coupon_line_id:
                    customer_coupon_line_id.coupon_used_count += 1
                else:
                    coupon_id.write({
                        'coupon_customer_line_ids': [(0,0,{'customer_id':record.customer_id.id,'coupon_used_count':1})],
                    })
            else:
                raise UserError("Invalid Promo Code!")
        return True

    def action_remove_promo_code(self):
        for record in self:
            if record.promo_code:
                record.sale_order_line_ids.write({
                    'promo_code': False,
                })
                record.promo_code_discount = 0
                coupon_ids = self.env['kits.multi.website.coupon'].search([('promo_code','=',record.promo_code)])
                customer_coupon_line_id = self.env['kits.multi.website.coupon.customer.line'].search([('customer_id','=',record.customer_id.id), ('coupon_id','in',coupon_ids.ids)])
                if customer_coupon_line_id and customer_coupon_line_id.coupon_used_count != 0:
                     customer_coupon_line_id.coupon_used_count -= 1
            record.promo_code = False
        return True


    def action_return_products(self):
        form_view_id = self.env.ref("kits_multi_website.kits_return_request_form_view")
        product_list = []
        for line in self.sale_order_line_ids:
            if line.is_return_available and line.state == 'done' or line.state == 'shipped':
                if not line.is_shipping_product and not line.is_select_for_lenses:
                    line.state= 'requested'
                    product_list.append((0,0,{
                        'product_id': line.product_id.id, 
                        'quantity':line.quantity,
                        'power_type_id':line.power_type_id.id,
                        'glass_type_id':line.glass_type_id.id,
                        'sale_order_line_id':line.id,
                        'amount': (line.discounted_glass_price + line.discounted_unit_price + line.tax_amount) * line.quantity,
                        }))
        if product_list:
            res_id = self.env['kits.multi.website.return.request'].create({
                    'sale_order_id':self.id,
                    'customer_id':self.customer_id.id,
                    'return_request_line_ids': product_list,
                    'website_id': self.website_id.id,
                    'state':'in_progress',
                    'so_sales_person_id' : self.user_id
            })
            return{
                'name': ('Return Request'),
                'res_model': 'kits.multi.website.return.request',
                'type': 'ir.actions.act_window',
                'views': [(form_view_id.id, 'form')],
                'context': {
                    'create':0,
                    },
                'target': 'current',
                'view_mode': 'form',
                'res_id' : res_id.id
            }
        else:
            raise UserError(_("Product can't return for this order."))

    def action_ready_to_ship(self):
        for record in self:
            record.state = 'ready_to_ship'
            record.sale_order_line_ids.write({'state': 'ready_to_ship'})
    
    def action_ship(self):
        for record in self:
            record.state = 'ship'
            record.sale_order_line_ids.write({'state': 'ship'})
    
    def action_ship(self):
        for record in self:
            record.state = 'shipped'
            record.sale_order_line_ids.write({'state': 'shipped'})
            if record.invoice_state == 'paid':
                record.state = 'done'
                record.sale_order_line_ids.write({'state': 'done'})




    def calculate_amount_for_api(self):
        for order in self:
            
            for line in order.sale_order_line_ids:
                line._compute_tax_id()
                line._compute_subtotal()
            return {
                'mrp': order.amount_without_discount,
                'tax': order.amount_tax,
                'shipping_charges': order.shipping_discount,
                'discount':order.amount_discount ,
                'net_price' : order.total
            }
    
    def action_priscription_confirm(self):
        for record in self:
            for line in record.sale_order_line_ids:
                if not line.prescription_id :
                    raise UserError(_('Please add prescription.'))
            record.state = 'waiting_for_prescription'


    def action_add_shipping_cost(self):
        return {
            "name":_("Add Shipping Cost"),
            "type":"ir.actions.act_window",
            "res_model":"kits.multi.website.add.shipping.cost.wizard",
            "view_mode":"form",
            "context":{"default_sale_order_id_kits":self.id,'default_country_id':self.customer_id.country_id.id},
            "target":"new",
        }
    
    def send_placed_order(self):
        self.ensure_one()
        if self:
            mail_template = self.env.ref('kits_multi_website.kits_b2c1_sale_order_placed_email')
            mail_template.sudo().with_context(signature=self.user_id.signature).send_mail(self.id,force_send=True,email_layout_xmlid="mail.mail_notification_light")
            return {"email_sent":True,"error": False}
        else:
            return {"email_sent":False,"error": "Order Not Found."}

    def upload_prescription_notify_cron(self):
        sale_order_ids =  self.env['kits.multi.website.sale.order'].search([('sale_order_line_ids.prescription_id','=',False),('sale_order_line_ids.is_select_for_lenses','=',True)])
        for sale_order in sale_order_ids:
            mail_template = self.env.ref('kits_multi_website.kits_b2c1_sale_order_prescription_email')
            mail_template.with_context(signature=self.user_id.signature).sudo().send_mail(sale_order.id,force_send=True,email_layout_xmlid="mail.mail_notification_light")

    def action_return_request(self):
        self.ensure_one()
        tree_view_id = self.env.ref('kits_multi_website.kits_multi_website_return_request_tree_view')
        form_view_id = self.env.ref('kits_multi_website.kits_multi_website_return_request_form_view')
        return{
            'name': ('Return Request'),
            'res_model': 'kits.multi.website.return.request',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id.id, 'tree'), (form_view_id.id, 'form')],
            'domain': [('sale_order_id','=',self.id)],
            'target': 'current',
        }

    def action_send_mail(self,json):
        reply_to = self.user_id.email+','+self.env.company.catchall_email  if self.user_id and self.env.company.catchall_email else self.env.company.catchall_email  
        attachment_ids = []
        if json.get('attachments'):
            for attachment in json.get('attachments'):
                filename = 'Re-' + attachment.get('filename','') 
                attachment_id = self.env['ir.attachment'].create({
                    'name': filename,
                    'type': 'binary',
                    'datas': attachment.get('file'),
                    'res_model': 'kits.multi.website.sale.order',
                    'res_id': json.get('res_id'),
                    'store_fname': filename,
                    'mimetype': attachment.get('mimetype'),
                })
                attachment_ids.append(attachment_id.id)
        mail_id = self.env['mail.mail'].create({
            'subject' : 'Re:'+self.name,
            'body_html' : json.get('body'),
            'body' : json.get('body'),
            'author_id': 2,
            'model': 'kits.multi.website.sale.order',
            'res_id': json.get('res_id'),
            'record_name': self.name,
            'reply_to' : reply_to,
            'message_type': 'comment',
            'subtype_id': 1,

        })
        mail_id.write({'email_from' : self.customer_id and self.customer_id.email and ((self.customer_id.display_name or'')+' <'+self.customer_id.email+'>' ),'email_to' : self.user_id and self.user_id.email and ((self.user_id.display_name or'')+' <'+self.user_id.email+'>' )})
        if attachment_ids:
            mail_id.sudo().write({
                'attachment_ids': [(4, attachment_id) for attachment_id in attachment_ids]
            }) 
        mail_id.sudo().send()
        return {'id': mail_id.mail_message_id.id,'date': datetime.strftime(mail_id.mail_message_id.create_date,'%d %b %Y'),'body': mail_id.mail_message_id.body,'res_id': mail_id.mail_message_id.res_id,'record_name': mail_id.mail_message_id.record_name,'email_from': mail_id.mail_message_id.email_from,'reply_to':mail_id.mail_message_id.reply_to}
        
