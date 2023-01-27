from odoo import fields, models, api, _

class kits_b2b_multi_currency_mapping(models.Model):
    _name = 'kits.b2b.multi.currency.mapping'
    _description = "Kits Currency Mapping"
    _rec_name = 'currency_id'

    currency_id = fields.Many2one("res.currency", "Currency")
    currency_rate = fields.Float("Currency Rate")
    website_id = fields.Many2one('kits.b2b.website','Website')

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
                    currency_mapping_id = self.env['kits.b2b.multi.currency.mapping'].search([('currency_id','=',record.env.company.currency_id.id)])
                    if currency_mapping_id:
                        return record.get_rate(currency_mapping_id, price)
            else:
                currency_mapping_id = self.env['kits.b2b.multi.currency.mapping'].search([('currency_id','=',record.env.company.currency_id.id)])
                if currency_mapping_id:
                    return record.get_rate(currency_mapping_id, price)
        
    def get_rate(self, currency_mapping_id, price):
        rate = currency_mapping_id.currency_rate
        new_price = price * rate
        return new_price

