from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class kits_landing_view(models.Model):
    _name = 'kits.landing.view'
    _description = 'Kits Landing View'

    name = fields.Char('Name')
    on_link = fields.Char('Redirect URL')
    mobile_banner = fields.Char('Mobile Banner ',related='mobile_banner_url')
    dekstop_banner = fields.Char('Dekstop Banner',related='dekstop_banner_url')
    website_id = fields.Many2one('kits.b2b.website','Website')
    mobile_banner_url = fields.Char('Mobile Banner')
    dekstop_banner_url = fields.Char('Dekstop Banner ')
    video_url_ids = fields.One2many('kits.landing.url', 'landing_view_id', string='Video URL')
    seo_keyword = fields.Char('URL Keyword')
    page_url = fields.Char(compute='_compute_page_url', string='Page URL',store=True)
    
    @api.constrains('seo_keyword')
    def _constrains_seo_keyword(self):
        for record in self:
            if record.page_url:
                rec = self.search([('page_url','=',record.page_url),('id','!=',record.id)])
                if rec:
                    raise UserError(_('A page URL must be unique.'))
    
    @api.depends('seo_keyword')
    def _compute_page_url(self):
        for record in self:
            url = ''
            if record.website_id and record.seo_keyword:
                url = record.website_id.url +'/video/'+ record.seo_keyword
            record.page_url =  url

class kits_landing_url(models.Model):
    _name = 'kits.landing.url'

    sequence = fields.Integer(string="Sequence")
    url = fields.Char('URL')
    landing_view_id = fields.Many2one('kits.landing.view', string='Landing View')
