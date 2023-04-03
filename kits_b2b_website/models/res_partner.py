from odoo import fields, models, api, _

language_code = [('en','English'),('af','Afrikaans'),('sq','Albanian'),('ar','Arabic'),('hy','Armenian'),('az','Azerbaijani'),('eu','Basque'),('be','Belarusian'),('bn','Bengali'),('bg','Bulgarian'),('ca','Catalan'),('zh-CN','Chinese (Simplified)'),('zh-TW','Chinese (Traditional)'),('hr','Croatian'),('cs','Czech'),('da','Danish'),('nl','Dutch'),('eo','Esperanto'),('et','Estonian'),('tl','Filipino'),('fi','Finnish'),('fr','French'),('gl','Galician'),('ka','Georgian'),('de','German'),('el','Greek'),('gu','Gujarati'),('ht','Haitian Creole'),('iw','Hebrew'),('hi','Hindi'),('hu','Hungarian'),('is','Icelandic'),('id','Indonesian'),('ga','Irish'),('it','Italian'),('ja','Japanese'),('kn','Kannada'),('ko','Korean'),('la','Latin'),('lv','Latvian'),('lt','Lithuanian'),('mk','Macedonian'),('ms','Malay'),('mt','Maltese'),('no','Norwegian'),('fa','Persian'),('pl','Polish'),('pt','Portuguese'),('ro','Romanian'),('ru','Russian'),('sr','Serbian'),('sk','Slovak'),('sl','Slovenian'),('es','Spanish'),('sw','Swahili'),('sv','Swedish'),('ta','Tamil'),('te','Telugu'),('th','Thai'),('tr','Turkish'),('uk','Ukrainian'),('ur','Urdu'),('vi','Vietnamese'),('cy','Welsh'),('yi','Yiddish')]

class res_partner(models.Model):
    _inherit = 'res.partner'

    b2b_pricelist_id = fields.Many2one(comodel_name='product.pricelist',string="Pricelist")
    preferred_currency= fields.Many2one(comodel_name='res.currency',string="Preferred Currency")
    b2b_wishlist_count = fields.Integer('Wishlist Count',compute='_compute_b2b_wishlist_count')
    b2b_recent_view_count = fields.Integer('Recent View Count',compute='_compute_b2b_wishlist_count')
    b2b_lang = fields.Selection(language_code, string='B2B Website Language',default="en")
    
    
    def _compute_b2b_wishlist_count(self):
        for record in self:
            record.b2b_wishlist_count = len(self.env['kits.b2b.product.wishlist'].search([('partner_id','=',record.id)]))
            record.b2b_recent_view_count = len(self.env['kits.b2b.recent.view'].search([('partner_id','=',record.id)]))

    @api.model
    def create(self, vals):
        res = super(res_partner, self).create(vals)
        for record in res:    
            record.b2b_pricelist_id = record.property_product_pricelist.id
        return res


    def write(self, vals):
        res = super().write(vals)
        for record in self:
            vals['b2b_pricelist_id'] = record.property_product_pricelist.id
        return res
    
    def get_image(self):
        image_128 = self.user_id.partner_id.image_128
        return {'image': image_128}

    def action_open_wishlist(self):
        self.ensure_one()
        return {
            'name': _('Wishlist'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'kits.b2b.product.wishlist',
            'view_id': self.env.ref('kits_b2b_website.kits_b2b_product_wishlist_view_tree').id,
            'domain' : [('id','in',self.env['kits.b2b.product.wishlist'].search([('partner_id','=',self.id)]).ids)]
        }

    def action_open_recent_view(self):
        self.ensure_one()
        return {
            'name': _('Recent View'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'kits.b2b.recent.view',
            'view_id': self.env.ref('kits_b2b_website.kits_b2b_recent_view_tree').id,
            'domain' : [('id','in',self.env['kits.b2b.recent.view'].search([('partner_id','=',self.id)]).ids)]
        }
