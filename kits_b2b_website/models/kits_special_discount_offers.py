from odoo import fields, models, api, _
from odoo.exceptions import UserError

class kits_special_discount_offers(models.Model):
    _inherit = 'kits.special.discount.offers'
    
    website_id = fields.Many2one('kits.b2b.website','Website')
    page_url = fields.Char(compute='_compute_page_url', string='Page URL',store=True)

    @api.constrains('seo_keyword')
    def _constrains_seo_keyword(self):
        for record in self:
            if record.page_url:
                rec = self.search([('page_url','=',record.page_url),('id','!=',record.id)])
                if rec:
                    raise UserError(_('A page URL must be unique.'))
    
    @api.depends('url_keyword')
    def _compute_page_url(self):
        for record in self:
            page_url = ''
            if record.website_id and record.url_keyword:
                page_url = record.website_id.url +'/offer?offer='+ record.url_keyword
            record.page_url =  page_url
