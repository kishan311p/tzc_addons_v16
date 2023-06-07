from odoo import _, api, fields, models, tools

class change_order_currency(models.TransientModel):
    _name = 'change.order.currency'
    _description = 'Change Order Currency'

    currency_id = fields.Many2one('res.currency','Currency')

    def btn_process(self):
        order_id = self.env['sale.order'].browse(self._context.get('order_id'))
        for rec in order_id:
            currency_id = self.currency_id
            for line in rec.order_line.filtered(lambda x : x.is_included_case==False):
                # For service type product.
                if line.product_id.is_global_discount or line.product_id.is_shipping_product or line.product_id.is_admin:
                    # Get converted price based on selected currency.
                    service_pro_price = rec.service_pro_price(line.price_unit,line.unit_discount_price,line.discount,currency_id)
                    if service_pro_price:
                        price_unit = service_pro_price.get('price_unit')
                        fix_discount_price = service_pro_price.get('fix_discount_price')
                        unit_discount_price = service_pro_price.get('unit_discount_price')
                    else:
                        price_unit = line.price_unit
                        fix_discount_price = line.fix_discount_price
                        unit_discount_price = line.unit_discount_price
                # For delivered type product.
                else:
                    usd_pricelist_id = self.env.ref('tzc_sales_customization_spt.usd_public_pricelist_spt')
                    extra_pricing = line.product_id.inflation_special_discount(self.env.user.country_id.ids,bypass_flag=rec.pricelist_id.is_pricelist_excluded)
                    if line.product_id.is_case_product:
                        unit_price = line.product_id.lst_price
                    else:
                        unit_price = self.env['product.pricelist.item'].search([('product_id','=',line.product_id.id),('pricelist_id','=',usd_pricelist_id.id)],limit=1).fixed_price
                    if currency_id.name.lower() != 'usd':
                        currency_rate = self.env['kits.b2b.multi.currency.mapping'].search([('currency_id','=',currency_id.id)],limit =1).currency_rate
                        price_unit = unit_price * currency_rate
                        fix_discount_price = round((price_unit * line.discount)/100,2)
                        unit_discount_price = price_unit - fix_discount_price
                    else:
                        if currency_id.name.lower() == 'usd':
                            price_unit = unit_price
                            fix_discount_price = round((price_unit * line.discount)/100,2)
                            unit_discount_price = price_unit - fix_discount_price

                    if extra_pricing.get('is_inflation'):
                        price_unit = round(price_unit+(price_unit*extra_pricing.get('inflation_rate') /100),2)
                        unit_discount_price = round(unit_discount_price+(unit_discount_price*extra_pricing.get('inflation_rate') /100),2)

                    if extra_pricing.get('is_special_discount'):
                        unit_discount_price = round((unit_discount_price - unit_discount_price * extra_pricing.get('special_disc_rate') / 100),2)
                        line.is_special_discount = extra_pricing.get('is_special_discount')

                line.write({
                    'price_unit':price_unit,
                    'unit_discount_price':unit_discount_price,
                    'fix_discount_price':fix_discount_price
                })

                line.with_context(currency_change=True)._compute_amount()
            rec.b2b_currency_id = self.currency_id.id
            rec._amount_all()
