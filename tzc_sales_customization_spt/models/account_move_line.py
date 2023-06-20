# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import ast
from collections import defaultdict
from contextlib import contextmanager
from datetime import date, timedelta
from functools import lru_cache
from odoo.tools import frozendict, formatLang, format_date, float_compare, Query

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _order = "product_id"

    is_global_discount = fields.Boolean("Is Additional Discount",related="product_id.is_global_discount", store=True)
    sale_type = fields.Selection([('clearance','Clearance'),('on_sale','On Sale')],'Sale Type',compute='_compute_boolean_fields')
    is_admin = fields.Boolean("Is Admin Fee",related="product_id.is_admin", store=True)
    is_shipping_product = fields.Boolean("Is Shipping Product",related="product_id.is_shipping_product", store=True)
    unit_discount_price = fields.Float('Discount',compute='_compute_discount_price')
    product_categ_id = fields.Many2one('product.category',related="product_id.categ_id", string='  Category ', readonly=True)
    discount_unit_price = fields.Float('Our Price',compute='_compute_discount_price')
    # is_fs = fields.Boolean("Is FS?",compute='_compute_boolean_fields')
    # is_fs = fields.Boolean("Is FS?")
    # is_promotion_applied = fields.Boolean("Is promotion applied?",compute='_compute_boolean_fields')
    primary_image_url = fields.Char("Primary Image URL",related='product_id.primary_image_url')
    is_included_case = fields.Boolean('Case Included?',help='Use to differentiate case is included or not.')

    _sql_constraints = [
        (
            "check_amount_currency_balance_sign",
            """CHECK(1=1)""",
            ""
        ),
    ]
    # def write(self, vals):
    #     if 'pos_model' in self._context.keys():
    #         create_context = {}
    #         for context in self._context:
    #             create_context[context] = self._context[context]
    #         create_context['check_move_validity'] = False
    #         self.env.context = create_context     
    #     for record in self:
    #         if record.debit:
    #             if not record.balance:
    #                 vals['balance']= record.debit
    #         if record.credit:
    #             if not record.balance:
    #                 vals['balance']= record.credit

    #     return super(AccountMoveLine, self).write(vals)



    # @api.depends(
    #     'move_id.invoice_line_ids',
    #     'move_id.invoice_line_ids.quantity',
    #     'move_id.invoice_line_ids.discount',
    #     'move_id.invoice_line_ids.price_unit',
    #     'quantity','discount','price_unit'
    #    )

    @api.depends('tax_ids', 'currency_id', 'partner_id', 'analytic_distribution', 'balance', 'partner_id', 'move_id.partner_id', 'price_unit')
    def _compute_all_tax(self):
        for line in self:
            sign = line.move_id.direction_sign
            if line.display_type == 'tax':
                line.compute_all_tax = {}
                line.compute_all_tax_dirty = False
                continue
            if line.display_type == 'product' and line.move_id.is_invoice(True):
                # amount_currency = sign * line.discount_unit_price * (1 - line.discount / 100)
                amount_currency = sign * line.discount_unit_price
                handle_price_include = True
                quantity = line.quantity
            else:
                amount_currency = line.amount_currency
                handle_price_include = False
                quantity = 1
            line.tax_ids
            compute_all_currency = line.tax_ids.compute_all(
                amount_currency,
                currency=line.currency_id,
                quantity=quantity,
                product=line.product_id,
                partner=line.move_id.partner_id or line.partner_id,
                is_refund=line.is_refund,
                handle_price_include=handle_price_include,
                include_caba_tags=line.move_id.always_tax_exigible,
                fixed_multiplicator=sign,
            )
            rate = line.amount_currency / line.balance if line.balance else 1
            line.compute_all_tax_dirty = True
            line.compute_all_tax = {
                frozendict({
                    'tax_repartition_line_id': tax['tax_repartition_line_id'],
                    'group_tax_id': tax['group'] and tax['group'].id or False,
                    'account_id': tax['account_id'] or line.account_id.id,
                    'currency_id': line.currency_id.id,
                    'analytic_distribution': (tax['analytic'] or not tax['use_in_tax_closing']) and line.analytic_distribution,
                    'tax_ids': [(6, 0, tax['tax_ids'])],
                    'tax_tag_ids': [(6, 0, tax['tag_ids'])],
                    'partner_id': line.move_id.partner_id.id or line.partner_id.id,
                    'move_id': line.move_id.id,
                }): {
                    'name': tax['name'],
                    'balance': tax['amount'] / rate,
                    'amount_currency': tax['amount'],
                    'tax_base_amount': tax['base'] / rate * (-1 if line.tax_tag_invert else 1),
                }
                for tax in compute_all_currency['taxes']
                if tax['amount']
            }
            if not line.tax_repartition_line_id:
                line.compute_all_tax[frozendict({'id': line.id})] = {
                    'tax_tag_ids': [(6, 0, compute_all_currency['base_tags'])],
                }

    # @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    # def _compute_totals(self):
    #     for line in self:
    #         line.price_subtotal =  line.sale_line_ids.price_subtotal
    #         line.price_total =  line.sale_line_ids.price_total
    #         if line.display_type != 'product':
    #             line.price_total = line.price_subtotal = False
    #         # Compute 'price_subtotal'.
    #         line_discount_price_unit = line.discount_unit_price 
    #         subtotal = line.quantity * line_discount_price_unit

    #         # Compute 'price_total'.
    #         if line.tax_ids:
    #             taxes_res = line.tax_ids.compute_all(
    #                 line_discount_price_unit,
    #                 quantity=line.quantity,
    #                 currency=line.currency_id,
    #                 product=line.product_id,
    #                 partner=line.partner_id,
    #                 is_refund=line.is_refund,
    #             )
    #             line.price_subtotal = taxes_res['total_excluded']
    #             line.price_total = taxes_res['total_included']
    #         else:
    #             line.price_total = line.price_subtotal = subtotal

    def _compute_discount_price(self):
        for record in self:
            # discounted_price = record.price_unit
            # unit_discount_price = 0.0
            # if record.discount:
            #     unit_discount_price = round( (record.price_unit*record.discount)/100,2)
                # discounted_price = round(record.price_unit - unit_discount_price,2)
            record.unit_discount_price = round(record.sale_line_ids.fix_discount_price,2)
            record.discount_unit_price = round(record.sale_line_ids.unit_discount_price,2) #Our Price
            total = {}
            if record.sale_line_ids:
                if record.product_id.detailed_type == 'product':
                    total = record._get_price_total_and_subtotal_model(record.sale_line_ids[0].price_unit,record.sale_line_ids[0].picked_qty,record.sale_line_ids[0].discount,record.sale_line_ids[0].currency_id,record.sale_line_ids[0].product_id,record.partner_id,record.sale_line_ids[0].tax_id,record.move_type)
                else:
                    total = record._get_price_total_and_subtotal_model(record.sale_line_ids[0].price_unit,record.sale_line_ids[0].product_uom_qty,record.sale_line_ids[0].discount,record.sale_line_ids[0].currency_id,record.sale_line_ids[0].product_id,record.partner_id,record.sale_line_ids[0].tax_id,record.move_type)
                
            record.price_total = total.get('price_total') if total.get('price_total') else 0.0
            record.price_subtotal = record.sale_line_ids.picked_qty_subtotal # Subtotal

    @api.onchange('product_id')
    def _onchange_product_id_spt(self):
        for record in self:
            record.quantity = record.quantity
            if record.product_id and record.product_id.is_global_discount:
                record.quantity = -record.quantity

    @api.onchange('quantity','price_unit','unit_discount_price','discount_unit_price')
    def _onchange_compute_price_subtotal_spt(self):
        for record in self:
            if record.discount_unit_price:
                record.price_subtotal =  round(record.discount_unit_price * record.quantity,2)

    @api.depends('sale_line_ids')
    def _compute_boolean_fields(self):
        for record in self:
            # record.is_fs = False
            record.sale_type = False
            # record.is_promotion_applied = False
            if record.sale_line_ids:
                # record.is_fs = record.sale_line_ids[0].is_fs
                record.sale_type = record.sale_line_ids[0].sale_type
                # record.is_promotion_applied = record.sale_line_ids[0].is_promotion_applied

    # Method Depriciated in 16.
    @api.model
    def _get_price_total_and_subtotal_model(self, price_unit, quantity, discount, currency, product, partner, taxes, move_type):
        ''' This method is used to compute 'price_total' & 'price_subtotal'.

        :param price_unit:  The current price unit.
        :param quantity:    The current quantity.
        :param discount:    The current discount.
        :param currency:    The line's currency.
        :param product:     The line's product.
        :param partner:     The line's partner.
        :param taxes:       The applied taxes.
        :param move_type:   The type of the move.
        :return:            A dictionary containing 'price_subtotal' & 'price_total'.
        '''
        res = {}

        # Compute 'price_subtotal'.
        # price_unit_wo_discount = price_unit * (1 - (discount / 100.0))
        #compute unit_discount_price

        unit_discount_price = (discount *0.01) * price_unit
        # unit_discount_price = format(unit_discount_price,'.2f')
        # try:
        #     price_unit_wo_discount = price_unit - float(str(unit_discount_price).split('.')[0]+'.'+str(unit_discount_price).split('.')[1][0:2])
        # except:
        price_unit_wo_discount = price_unit - round(unit_discount_price,2)

        try:
            subtotal = quantity * float(str(price_unit_wo_discount).split('.')[0]+'.'+str(price_unit_wo_discount).split('.')[1][0:2])
        except:
            subtotal = quantity * round(price_unit_wo_discount,2)

        # price_unit_wo_discount = float(price_unit_wo_discount)
        # unit_discount_price = float(unit_discount_price)

        # price_unit_wo_discount = round(price_unit - ((discount *0.01) * price_unit),2)
        

        # Compute 'price_total'.
        if taxes:
            taxes_res = taxes._origin.compute_all(price_unit_wo_discount,
                quantity=quantity, currency=currency, product=product, partner=partner, is_refund=move_type in ('out_refund', 'in_refund'))
            res['price_subtotal'] = taxes_res['total_excluded']
            res['price_total'] = taxes_res['total_included']
        else:
            res['price_total'] = res['price_subtotal'] = subtotal
        #In case of multi currency, round before it's use for computing debit credit
        if currency:
            res = {k: currency.round(v) for k, v in res.items()}
        return res

    def _sale_determine_order(self):
        """ Get the mapping of move.line with the sale.order record on which its analytic entries should be reinvoiced
            :return a dict where key is the move line id, and value is sale.order record (or None).
        """
        analytic_accounts = self.mapped('analytic_account_id')

        # link the analytic account with its open SO by creating a map: {AA.id: sale.order}, if we find some analytic accounts
        mapping = {}
        if analytic_accounts:  # first, search for the open sales order
            sale_orders = self.env['sale.order'].search([('analytic_account_id', 'in', analytic_accounts.ids), ('state', 'in', ['sale', 'done','in_scanning','scanned','scan','shipped','draft_inv','open_inv'])], order='create_date DESC')
            for sale_order in sale_orders:
                mapping[sale_order.analytic_account_id.id] = sale_order

            analytic_accounts_without_open_order = analytic_accounts.filtered(lambda account: not mapping.get(account.id))
            if analytic_accounts_without_open_order:  # then, fill the blank with not open sales orders
                sale_orders = self.env['sale.order'].search([('analytic_account_id', 'in', analytic_accounts_without_open_order.ids)], order='create_date DESC')
            for sale_order in sale_orders:
                mapping[sale_order.analytic_account_id.id] = sale_order

        # map of AAL index with the SO on which it needs to be reinvoiced. Maybe be None if no SO found
        return {move_line.id: mapping.get(move_line.analytic_account_id.id) for move_line in self}

    def _sale_create_reinvoice_sale_line(self):
        
        sale_order_map = self._sale_determine_order()

        sale_line_values_to_create = []  # the list of creation values of sale line to create.
        existing_sale_line_cache = {}  # in the sales_price-delivery case, we can reuse the same sale line. This cache will avoid doing a search each time the case happen
        # `map_move_sale_line` is map where
        #   - key is the move line identifier
        #   - value is either a sale.order.line record (existing case), or an integer representing the index of the sale line to create in
        #     the `sale_line_values_to_create` (not existing case, which will happen more often than the first one).
        map_move_sale_line = {}

        for move_line in self:
            sale_order = sale_order_map.get(move_line.id)

            # no reinvoice as no sales order was found
            if not sale_order:
                continue

            # raise if the sale order is not currenlty open
            if sale_order.state not in  ['sale', 'done','in_scanning','scanned','scan','shipped','draft_inv','open_inv']:
                message_unconfirmed = _('The Sales Order %s linked to the Analytic Account %s must be validated before registering expenses.')
                messages = {
                    'draft': message_unconfirmed,
                    'sent': message_unconfirmed,
                    'done': _('The Sales Order %s linked to the Analytic Account %s is currently locked. You cannot register an expense on a locked Sales Order. Please create a new SO linked to this Analytic Account.'),
                    'cancel': _('The Sales Order %s linked to the Analytic Account %s is cancelled. You cannot register an expense on a cancelled Sales Order.'),
                }
                raise UserError(messages[sale_order.state] % (sale_order.name, sale_order.analytic_account_id.name))

            price = move_line._sale_get_invoice_price(sale_order)

            # find the existing sale.line or keep its creation values to process this in batch
            sale_line = None
            if move_line.product_id.expense_policy == 'sales_price' and move_line.product_id.invoice_policy == 'delivery':  # for those case only, we can try to reuse one
                map_entry_key = (sale_order.id, move_line.product_id.id, price)  # cache entry to limit the call to search
                sale_line = existing_sale_line_cache.get(map_entry_key)
                if sale_line:  # already search, so reuse it. sale_line can be sale.order.line record or index of a "to create values" in `sale_line_values_to_create`
                    map_move_sale_line[move_line.id] = sale_line
                    existing_sale_line_cache[map_entry_key] = sale_line
                else:  # search for existing sale line
                    sale_line = self.env['sale.order.line'].search([
                        ('order_id', '=', sale_order.id),
                        ('price_unit', '=', price),
                        ('product_id', '=', move_line.product_id.id),
                        ('is_expense', '=', True),
                    ], limit=1)
                    if sale_line:  # found existing one, so keep the browse record
                        map_move_sale_line[move_line.id] = existing_sale_line_cache[map_entry_key] = sale_line
                    else:  # should be create, so use the index of creation values instead of browse record
                        # save value to create it
                        sale_line_values_to_create.append(move_line._sale_prepare_sale_line_values(sale_order, price))
                        # store it in the cache of existing ones
                        existing_sale_line_cache[map_entry_key] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line
                        # store it in the map_move_sale_line map
                        map_move_sale_line[move_line.id] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line

            else:  # save its value to create it anyway
                sale_line_values_to_create.append(move_line._sale_prepare_sale_line_values(sale_order, price))
                map_move_sale_line[move_line.id] = len(sale_line_values_to_create) - 1  # save the index of the value to create sale line

        # create the sale lines in batch
        new_sale_lines = self.env['sale.order.line'].create(sale_line_values_to_create)
        
        # build result map by replacing index with newly created record of sale.order.line
        result = {}
        for move_line_id, unknown_sale_line in map_move_sale_line.items():
            if isinstance(unknown_sale_line, int):  # index of newly created sale line
                result[move_line_id] = new_sale_lines[unknown_sale_line]
            elif isinstance(unknown_sale_line, models.BaseModel):  # already record of sale.order.line
                result[move_line_id] = unknown_sale_line
        return result

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the generic taxes computation method
        defined on account.tax.
        :return: A python dictionary.
        """
        self.ensure_one()
        is_invoice = self.move_id.is_invoice(include_receipts=True)
        sign = -1 if self.move_id.is_inbound(include_receipts=True) else 1

        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.partner_id,
            currency=self.currency_id,
            product=self.product_id,
            taxes=self.tax_ids,
            price_unit=self.discount_unit_price,
            quantity=self.quantity,
            discount=self.discount ,
            account=self.account_id,
            analytic_distribution=self.analytic_distribution,
            price_subtotal=sign * self.amount_currency,
            is_refund=self.is_refund,
            rate=(abs(self.amount_currency) / abs(self.balance)) if self.balance else 1.0
        )

    @api.depends('quantity', 'discount', 'price_unit', 'tax_ids', 'currency_id')
    def _compute_totals(self):
        for record in self:
            record.price_subtotal =  record.sale_line_ids.price_subtotal
            record.price_total =  record.sale_line_ids.price_total
        return super(AccountMoveLine, self)._compute_totals()

    @api.model_create_multi
    def create(self,vals_list):
        for vals in vals_list:
            product_id = self.env['product.product'].browse(vals.get('product_id'))
            if vals.get('display_type') == 'product' and product_id.is_global_discount:
                vals.update({'price_unit':-vals.get('price_unit')})
        res = super(AccountMoveLine,self).create(vals_list)
        for rec in res:
            if rec.display_type == 'payment_term':
                rec.balance = res.amount_currency
            if rec.display_type == 'product' and rec.move_id.move_type == 'out_invoice':
                if not rec.product_id.is_global_discount:
                    rec.balance = rec.price_subtotal
                    rec.credit = rec.price_subtotal
                else:
                    rec.debit = rec.discount_unit_price
                    rec.amount_currency = rec.discount_unit_price
            if rec.sale_line_ids:
                rec.discount_unit_price = rec.sale_line_ids[0].unit_discount_price
        return res
