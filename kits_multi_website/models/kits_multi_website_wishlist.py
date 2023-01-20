from odoo import _, api, fields, models, tools
from lxml import etree

class kits_multi_website_wishlist(models.Model):
    _name = 'kits.multi.website.wishlist'
    _description = 'Kits Multi Website Wishlist'
    _rec_name = 'customer_id'
    _order = 'create_date desc,sequence desc'

    customer_id = fields.Many2one('kits.multi.website.customer','Customer')
    website_id = fields.Many2one('kits.b2c.website','Website')
    # product_line_ids = fields.Many2many('product.product','kmwwl_pp_real','wishlist_id','pp_id','Products')
    product_id = fields.Many2one('product.product','Product')
    sequence = fields.Integer(index=True)
    image_1_url = fields.Char('Primary Url',related='product_id.primary_image_url',store=True)
    image_2_url = fields.Char('Secondary Url',related='product_id.sec_image_url',store=True)


    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_wishlist, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res
