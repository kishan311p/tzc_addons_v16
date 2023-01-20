from odoo import api, fields, models, _

class kits_multi_website_lense_details(models.Model):
    _name = "kits.multi.website.lense.details"
    _description = "Kits Multi Website lense"
    _rec_name = 'lense_id'

    lense_id = fields.Many2one('kits.multi.website.lense','Lense')
    is_boolean = fields.Boolean('Is Boolean')
    field_type = fields.Selection([('boolean','Boolean'),('char','Character')],'Type Of Data',related='lense_id.field_type')
    value = fields.Char('Value')
    glass_type_id = fields.Many2one('kits.multi.website.glass.type', string='Glass Type')
    image_icon_url = fields.Char('Image Icon Url',related='lense_id.image_icon_url')

    website_id = fields.Many2one('kits.b2c.website','Website')

    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_lense_details, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res
