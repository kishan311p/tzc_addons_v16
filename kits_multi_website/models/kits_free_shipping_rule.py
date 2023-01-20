from odoo import api, fields, models, _
from lxml import etree
from odoo.exceptions import UserError

class kits_free_shipping_rule(models.Model):
    _name = 'kits.free.shipping.rule'
    _description = "Kits Free Shipping Rule"

    name = fields.Char("Name")
    country_ids = fields.Many2many("res.country","shipping_rule_res_country_rel","shipping_rule_id","country_id","Countries")
    website_id = fields.Many2one("kits.b2c.website", "Website")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    shipping_rule_ids = fields.One2many('kits.free.shipping.rule.line','shipping_rule_id','Free Shipping Rule')
    free_shipping_days = fields.Float('Free Shipping Days')
    paid_shipping_rule_ids = fields.One2many('kits.paid.shipping.rule.line','shipping_rule_id','Paid Shipping Rule')

    _sql_constraints = [
        (
            'unique_coupon_name', 'UNIQUE(name)',
            'Coupon name must be unique')
    ] 

    def add_website_id(self):
        return {
                'name': 'Add Website',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'kits.add.remove.website.wizard',
                'views': [(self.env.ref('kits_multi_website.kits_add_remove_website_wizard_form_view').id, 'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'context':{'default_is_add': True,'default_res_model': self._name,'default_res_id' : self.ids}
            }   
    
    def remove_website_id(self):
            return {
                'name': 'Remove Website',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'kits.add.remove.website.wizard',
                'views': [(self.env.ref('kits_multi_website.kits_add_remove_website_wizard_form_view').id, 'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'context':{'default_is_add': False,'default_res_model': self._name,'default_res_id' : self.ids}
            }   
    

    @api.model
    def default_get(self, fields):
        res = super(kits_free_shipping_rule, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res

    @api.constrains('country_ids')
    def _constrains_country_ids(self):
        for rec in self:
            country_ids = self.search([('id','!=', rec.id),('website_id','=',rec.website_id.id)]).mapped('country_ids').ids
            country_list = [country_id.name for country_id in rec.country_ids if country_id.id in country_ids]
            if country_list:
                raise UserError('%s is already assigned, so you cannot create other record.'%(','.join(set(country_list))))
