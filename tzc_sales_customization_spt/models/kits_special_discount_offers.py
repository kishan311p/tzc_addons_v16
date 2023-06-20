from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class kits_special_discount_offers_line(models.Model):
    _name = 'kits.special.discount.offers.line'

    sdo_id = fields.Many2one('kits.special.discount.offers', string='Special Discount Offers')
    brand_ids = fields.Many2many('product.brand.spt','special_discount_offer_with_line_real','line_id','brand_id', string='Brand')
    amount = fields.Float('Discount(%)')


class kits_special_discount_offers_product_line(models.Model):
    _name = 'kits.special.discount.offers.product.line'

    pp_sdo_id = fields.Many2one('kits.special.discount.offers', string='Special Discount Offers')
    product_ids = fields.Many2many('product.product','sdo_with_pp_real','line_id','product_id', string='Product')
    amount = fields.Float('Discount(%)')


class kits_special_discount_offers(models.Model):
    _name = 'kits.special.discount.offers'

    name = fields.Char('Name')
    start_date = fields.Datetime('Start Date')
    end_date = fields.Datetime('End Date')
    url_keyword = fields.Char('URL Keyword')
    desktop_main_banners_url = fields.Char('Desktop Main Banners URL')
    mobile_main_banners_url = fields.Char('Mobile Main Banners URL')
    offer_expired_desktop_banners_url = fields.Char('Offer Expired Desktop Banners URL')
    offer_expired_mobile_banners_url = fields.Char('Offer Expired Mobile Banners URL')
    desktop_main_banners = fields.Char('Desktop Main Banners',related='desktop_main_banners_url')
    mobile_main_banners = fields.Char('Mobile Main Banners',related='mobile_main_banners_url')
    offer_expired_desktop_banners = fields.Char('Offer Expired Desktop Banners',related='offer_expired_desktop_banners_url')
    offer_expired_mobile_banners = fields.Char('Offer Expired Mobile Banners',related='offer_expired_mobile_banners_url')
    brands_ids = fields.One2many('kits.special.discount.offers.line', 'sdo_id', string='Brands')
    active = fields.Boolean('Active',default=True)
    offer_icon_url = fields.Char('Offer Icon URL')
    offer_icon = fields.Char('Offer Icon',related='offer_icon_url')
    product_ids = fields.One2many('kits.special.discount.offers.product.line', 'pp_sdo_id', string='Brands')
    
