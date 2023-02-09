# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError,UserError

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    _order = "product_id"

    is_global_discount = fields.Boolean("Is Additional Discount",related="product_id.is_global_discount", store=True)
    sale_type = fields.Selection([('clearance','Clearance'),('on_sale','On Sale')],'Sale Type',compute='_compute_boolean_fields')
    is_admin = fields.Boolean("Is Admin Fee",related="product_id.is_admin", store=True)
    is_shipping_product = fields.Boolean("Is Shipping Product",related="product_id.is_shipping_product", store=True)
    unit_discount_price = fields.Float('Discount',compute='_compute_discount_price')
    product_categ_id = fields.Many2one('product.category',related="product_id.categ_id", string='Category', readonly=True)
    discount_unit_price = fields.Float('Our Price',compute='_compute_discount_price')
    is_fs = fields.Boolean("Is FS?",compute='_compute_boolean_fields')
    is_promotion_applied = fields.Boolean("Is promotion applied?",compute='_compute_boolean_fields')
    
    def write(self, vals):
        if 'pos_model' in self._context.keys():
            create_context = {}
            for context in self._context:
                create_context[context] = self._context[context]
            create_context['check_move_validity'] = False
            self.env.context = create_context     
        for record in self:
            if record.debit:
                if not record.balance:
                    vals['balance']= record.debit
            if record.credit:
                if not record.balance:
                    vals['balance']= record.credit

        return super(AccountMoveLine, self).write(vals)



    # @api.depends(
    #     'move_id.invoice_line_ids',
    #     'move_id.invoice_line_ids.quantity',
    #     'move_id.invoice_line_ids.discount',
    #     'move_id.invoice_line_ids.price_unit',
    #     'quantity','discount','price_unit'
    #    )
    def _compute_discount_price(self):
        for record in self:
            discounted_price = record.price_unit
            unit_discount_price = 0.0
            if record.discount:
                unit_discount_price = round( (record.price_unit*record.discount)/100,2)
                discounted_price = round(record.price_unit - unit_discount_price,2)
            record.unit_discount_price = round(unit_discount_price,2)
            record.discount_unit_price = round(discounted_price,2)


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
            record.is_fs = False
            record.sale_type = False
            record.is_promotion_applied = False
            if record.sale_line_ids:
                record.is_fs = record.sale_line_ids[0].is_fs
                record.sale_type = record.sale_line_ids[0].sale_type
                record.is_promotion_applied = record.sale_line_ids[0].is_promotion_applied

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

        unit_discount_price = round((discount *0.01) * price_unit,2)
        price_unit_wo_discount = round(price_unit - unit_discount_price,2)
        subtotal = round(quantity * price_unit_wo_discount,2)
        
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
