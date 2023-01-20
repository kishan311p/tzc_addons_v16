from lxml import etree
from odoo import api, fields, models, _

class kits_multi_website_glass_type(models.Model):
    _name = "kits.multi.website.glass.type"
    _description = "Kits Multi Website Glass Type"

    name = fields.Char("Name")
    price = fields.Float("Price")
    discounted_price = fields.Float("Discounted Price")
    power_type_id = fields.Many2one('kits.multi.website.power.type',string="Power Type",domain="[('website_id','=',website_id)]")
    website_id = fields.Many2one('kits.b2c.website','Website')
    lense_details_ids = fields.field_name_ids = fields.One2many('kits.multi.website.lense.details', 'glass_type_id', string='Lense Details')


    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_glass_type, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res
        
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

