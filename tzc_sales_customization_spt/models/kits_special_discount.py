from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class kits_special_discount(models.Model):
    _name = 'kits.special.discount'

    country_id = fields.Many2many('res.country','special_discount_country_rel','discount_id','brand_id',string='Country',index = True)
    brand_ids = fields.Many2many('product.brand.spt','special_discount_brand_rel','model_id','brand_id','Brands',index = True)
    discount = fields.Float('Additional Discout %')
    tzc_fest_id = fields.Many2one('tzc.fest.discount')

    @api.onchange('discount')
    def onchange_discount(self):
        for rec in self:
            if rec.discount < 0:
                raise UserError ('Discount should be positive.')

    @api.constrains('country_id','brand_ids')
    def _check_duplicate_value(self):
        countries_name = []
        brnads_name = []
        for rec in self:
            active_fest_id = self.env['tzc.fest.discount'].search([('id','=',rec.tzc_fest_id.id)],limit=1)
            for country in rec.country_id:
                if active_fest_id:
                    line_ids = active_fest_id.special_discount_rule_ids.search([('country_id','in',country.id),('tzc_fest_id','=',active_fest_id.id),('id','!=',rec.id)])
                    if line_ids:
                        for brand in rec.brand_ids:
                            if brand in line_ids.mapped('brand_ids'):
                                if country.name not in countries_name:
                                    countries_name.append(country.name)
                                if brand.name not in brnads_name:
                                    brnads_name.append(brand.name)

        if countries_name or brnads_name:
            message = ''
            if countries_name and brnads_name:
                if len(countries_name) > 1:
                    message += 'Countries '
                else:
                    message += 'Country '
                
                message += ', '.join(countries_name) + ' and brand ' + ', '.join(brnads_name) + ' is duplicated.'
            elif countries_name:
                if len(countries_name) > 1:
                    message += 'Countries '
                else:
                    message += 'Country '
                
                message += ', '.join(countries_name) + ' is duplicated.'
            elif brnads_name:
                if len(brnads_name) > 1:
                    message += 'Brnads '
                else:
                    message += 'Brand '
                
                message += ', '.join(brnads_name) + ' is duplicated.'
            
            raise UserError (_(message))
