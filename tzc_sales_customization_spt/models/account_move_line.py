# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

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