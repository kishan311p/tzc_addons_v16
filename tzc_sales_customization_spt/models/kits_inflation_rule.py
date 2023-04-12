from odoo.exceptions import UserError
from odoo import fields,models,api

class kits_inflation_rule(models.Model):
    _name = 'kits.inflation.rule'

    country_id = fields.Many2many('res.country','inflation_country_rel','discount_id','brand_id',string='Country',index = True)
    brand_ids = fields.Many2many('product.brand.spt','inflation_brand_rel','model_id','brand_id','Brands',index = True)
    # inflation_rate = fields.Float('inflation (%)')
    inflation_rate = fields.Integer('inflation (%)')
    inflation_id = fields.Many2one('kits.inflation')
    

    @api.onchange('inflation_rate')
    def onchange_discount(self):
        for rec in self:
            if rec.inflation_rate < 0:
                raise UserError ('Discount should be positive.')

    @api.constrains('country_id','brand_ids')
    def _check_duplicate_value(self):
        countries_name = []
        brnads_name = []
        for rec in self:
            active_inflation_id = self.env['kits.inflation'].search([('id','=',rec.inflation_id.id)],limit=1)
            for country in rec.country_id:
                if active_inflation_id:
                    line_ids = active_inflation_id.inflation_rule_ids.search([('country_id','in',country.id),('inflation_id','=',active_inflation_id.id),('id','!=',rec.id)])
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

    @api.constrains('country_id','brand_ids')
    def _check_duplicate_value(self):
        # active_fest_id = self.env['kits.inflation'].search([('is_active','=',True)],limit=1)
        countries_name = []
        brnads_name = []   
        for rec in self: 
            line_ids = rec.inflation_id.inflation_rule_ids - rec
            for line in line_ids:
                for country in rec.country_id.ids:
                    if country in line.country_id.ids:
                        countries_name.append(rec)
                for brand in rec.brand_ids.ids:
                    if brand in line.brand_ids.ids:
                        brnads_name.append(rec)
            for cntry in countries_name:
                for brnd in brnads_name:
                    if cntry.id == brnd.id:
                # if rec.country_id.ids in i.country_id.ids and rec.brand_ids.ids in i.brand_ids.ids:
                        raise UserError ('duplicated')
        for rec in self:
            line_ids = rec.inflation_id.inflation_rule_ids - rec
            for line in line_ids:
                for country in rec.country_id:
                    if country.id in line_ids.mapped('country_id').ids:
                        if country.name not in countries_name:
                            countries_name.append(country.name)
                for brand in rec.brand_ids:
                    if brand.id in line_ids.mapped('brand_ids').ids:
                        if brand.name not in brnads_name:
                            brnads_name.append(brand.name)
        
        if countries_name and brnads_name != []:
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
