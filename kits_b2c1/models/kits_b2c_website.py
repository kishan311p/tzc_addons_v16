from odoo import api, fields, models, _

class kits_b2c_website(models.Model):
    _inherit = 'kits.b2c.website'

    website_name = fields.Selection(selection_add=[('b2c1', 'B2C1')]) 
    men_image = fields.Char("Men Image",compute="_compute_men_image",store=True)
    women_image = fields.Char("Women Image",compute="_compute_women_image",store=True)
    kids_image = fields.Char("Kids Image",compute="_compute_kids_image",store=True)

    contact = fields.Char("Contact")
    company_email = fields.Char("Company Email")
    facebook_icon = fields.Char("Facebook Icon",compute="_compute_facebook_icon",store=True)
    twitter_icon = fields.Char("Twitter Icon",compute="_compute_twitter_icon",store=True)
    instagram_icon = fields.Char("Instagram Icon",compute="_compute_instagram_icon",store=True)
    youtube_icon = fields.Char("Youtube Icon",compute="_compute_youtube_icon",store=True)
    mail_icon = fields.Char("Mail Icon",compute="_compute_mail_icon",store=True)
    contact_icon = fields.Char("Contact Icon",compute="_compute_contact_icon",store=True)

    men_image_url = fields.Char('Men Image Url')
    women_image_url = fields.Char('Women Image Url')
    kids_image_url = fields.Char('Kids Image Url')

    contact_icon_url = fields.Char("Contact Icon Image Url")
    mail_icon_url = fields.Char("Mail Icon Image Url")
    facebook_icon_url = fields.Char("Facebook Icon Image Url")
    twitter_icon_url = fields.Char("Twitter Icon Image Url")
    instagram_icon_url = fields.Char("Instagram Icon Image Url")
    youtube_icon_url = fields.Char("Youtube Icon Image Url")


    shop_page_keyword = fields.Char('Shop Page Meta Keyword')
    shop_page_title = fields.Char('Shop Page Meta Title')
    shop_page_description = fields.Text('Shop Page Meta Description')
    
    cookies_policy = fields.Html('Cookies Policy')
    cookies_policy_url = fields.Char('Cookies Policy URL')
    canonical_url = fields.Char('Canonical Url')

    @api.depends('men_image_url')
    def _compute_men_image(self):
        for record in self:
            record.men_image = record.men_image_url 

    @api.depends('women_image_url')
    def _compute_women_image(self):
        for record in self:
            record.women_image = record.women_image_url

    @api.depends('kids_image_url')
    def _compute_kids_image(self):
        for record in self:
            record.kids_image = record.kids_image_url

    @api.depends('facebook_icon_url')
    def _compute_facebook_icon(self):
        for record in self:
            record.facebook_icon = record.facebook_icon_url

    @api.depends('twitter_icon_url')
    def _compute_twitter_icon(self):
        for record in self:
            record.twitter_icon = record.twitter_icon_url

    @api.depends('instagram_icon_url')
    def _compute_instagram_icon(self):
        for record in self:
            record.instagram_icon = record.instagram_icon_url

    @api.depends('youtube_icon_url')
    def _compute_youtube_icon(self):
        for record in self:
            record.youtube_icon = record.youtube_icon_url

    @api.depends('mail_icon_url')
    def _compute_mail_icon(self):
        for record in self:
            record.mail_icon = record.mail_icon_url

    @api.depends('contact_icon_url')
    def _compute_contact_icon(self):
        for record in self:
            record.contact_icon = record.contact_icon_url