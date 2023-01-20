from odoo import api, fields, models, _
from lxml import etree

class kits_multi_website_lense(models.Model):
    _name = "kits.multi.website.lense"
    _description = "Kits Multi Website lense"

    name = fields.Char('Name')
    field_type = fields.Selection([('boolean','Boolean'),('char','Character')],'Type Of Data')
    website_id = fields.Many2one('kits.b2c.website','Website')
    image_icon_url = fields.Char('Image Icon Url')
    image_icon_url_icon = fields.Char(compute='_compute_image_icon_url_icon', string='Image Icon Url Icon')
    
    @api.depends('image_icon_url')
    def _compute_image_icon_url_icon(self):
        for record in self:
            record.image_icon_url_icon = record.image_icon_url


    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_lense, self).default_get(fields)
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
                'name': 'Remove website',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'kits.add.remove.website.wizard',
                'views': [(self.env.ref('kits_multi_website.kits_add_remove_website_wizard_form_view').id, 'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'context':{'default_is_add': False,'default_res_model': self._name,'default_res_id' : self.ids}
            }   
