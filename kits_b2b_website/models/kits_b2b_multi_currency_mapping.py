from odoo import fields, models, api, _
from odoo.exceptions import UserError

class kits_b2b_multi_currency_mapping(models.Model):
    _name = 'kits.b2b.multi.currency.mapping'
    _description = "Kits Currency Mapping"
    _rec_name = 'currency_id'

    currency_id = fields.Many2one("res.currency", "Currency")
    currency_rate = fields.Float("Currency Rate")
    website_id = fields.Many2one('kits.b2b.website','Website')
    partner_country_ids = fields.Many2many("res.country",string="Countries")

    _sql_constraints = [
        (
            'unique_currency_id', 'UNIQUE(currency_id)',
            'Record for this currency already exists!')
    ]

    def _convert_rates(self, price, to_currency):
        for record in self:
            from_currency = record.env.company.currency_id
            if from_currency != to_currency:
                currency_mapping_id = self.env['kits.b2b.multi.currency.mapping'].search([('currency_id','=',to_currency.id)])
                if currency_mapping_id:
                    return record.get_rate(currency_mapping_id, price)
                else:
                    currency_mapping_id = self.env['kits.b2b.multi.currency.mapping'].search([('currency_id','=',from_currency.id)])
                    if currency_mapping_id:
                        return record.get_rate(currency_mapping_id, price)
            else:
                currency_mapping_id = self.env['kits.b2b.multi.currency.mapping'].search([('currency_id','=',from_currency.id)])
                if currency_mapping_id:
                    return record.get_rate(currency_mapping_id, price)
        
    def get_rate(self, currency_mapping_id, price):
        rate = currency_mapping_id.currency_rate
        new_price = price * rate
        return new_price

    def write(self,vals):
        res = super(kits_b2b_multi_currency_mapping,self).write(vals)
        if 'partner_county_ids' in vals:
            country_list = []
            country_ids = False
            try:
                country_ids = vals.get('partner_county_ids')[0][2]
            except:
                country_ids = False
            if country_ids:
                rec_id = self.search([('partner_county_ids','in',vals.get('partner_county_ids')[0][2]),('id','!=',self.id)])
                for country in self.partner_county_ids:
                    if country.id in rec_id.partner_county_ids.ids:
                        country_list.append(country.name)
                if rec_id:
                    raise UserError('Country %s is alredy set in %s currency.'%(','.join(country_list),', '.join(rec_id.mapped('currency_id.name'))))

        return res

    # Data passing formate
    # PartnerId --> Integer & ProductIds --> List of Integer

    def get_product_price(self,partner_id,product_ids,order_id=None):
        if isinstance(partner_id, int) and isinstance(product_ids,list)  :
            partner_id = self.env['res.partner'].browse(partner_id)
            multi_currency_obj = self.env['kits.b2b.multi.currency.mapping']
            partner_currency_rate = 0.0
            products_prices = {}
            for product in product_ids:
                sale_type_price = 0.0
                is_currency_match = True if partner_id.property_product_pricelist.currency_id.id == partner_id.preferred_currency.id else False

                product = self.env['product.product'].browse(product)
                pricelist_price = self.env['product.pricelist.item'].search([('product_id','in',product.ids),('pricelist_id','=',partner_id.property_product_pricelist.id)],limit=1).fixed_price
                
                if self._context.get('from_order_line') and order_id and not is_currency_match:
                    partner_currency_rate = multi_currency_obj.search([('currency_id','=',order_id.b2b_currency_id.id)],limit=1).currency_rate
                elif partner_id.preferred_currency and not is_currency_match:
                    partner_currency_rate = multi_currency_obj.search([('currency_id','=',partner_id.preferred_currency.id)],limit=1).currency_rate
                elif not is_currency_match:
                    partner_currency_rate = multi_currency_obj.search([('partner_country_ids','in',partner_id.country_id.id)],limit=1).currency_rate

                if partner_currency_rate:
                    product_price = pricelist_price * partner_currency_rate
                    product_msrp_price = product.price_msrp * partner_currency_rate
                    product_wholsale_price = product.price_wholesale * partner_currency_rate
                
                    if product.sale_type == 'on_sale':
                        sale_type_price = product.on_sale_usd * partner_currency_rate
                    elif product.sale_type == 'clearance':
                        sale_type_price = product.clearance_usd * partner_currency_rate
                    else:
                        sale_type_price = product_price
                else:
                    product_price = pricelist_price
                    product_msrp_price = product.price_msrp
                    product_wholsale_price = product.price_wholesale

                    if product.sale_type == 'on_sale':
                        sale_type_price = product.on_sale_usd
                    elif product.sale_type == 'clearance':
                        sale_type_price = product.clearance_usd
                    else:
                        sale_type_price = product_price
                
                if product_price and product_price != sale_type_price:
                    discounted_unit_price = product_price - sale_type_price
                    discount = (1-(sale_type_price/product_price))*100
                else:
                    discounted_unit_price = product_price
                    discount = 0.0

                products_prices[product.id] = {
                                                'price':product_price,
                                                'msrp_price':product_msrp_price,
                                                'product_wholsale_price':product_wholsale_price,
                                                'sale_type':product.sale_type,
                                                'sale_type_price':sale_type_price,
                                                'discount' : discount,
                                                'discounted_unit_price' : discounted_unit_price
                                            }

            return  products_prices

        else:
            error = 'Make sure your'
            flag = False
            if not isinstance(partner_id, int):
                error += ' partner data in integer partner id'
                flag= True
            if not isinstance(product_ids, list):
                if flag:
                    error += ' AND '
                error += ' product data in list of product ids '
            raise UserError(error)
