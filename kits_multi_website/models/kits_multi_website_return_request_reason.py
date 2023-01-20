from odoo import fields,models,api

class kits_multi_website_return_request_reason(models.Model):
    _name = 'kits.multi.website.return.request.reason'
    _description = 'Return Request Reason'

    def get_website_id(self):
        website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
        return website_id
    

    name = fields.Char('Name')
    website_id = fields.Many2one('kits.b2c.website','Website',default=get_website_id)

    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_return_request_reason, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res

