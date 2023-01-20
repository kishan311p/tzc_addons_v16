# @Fenil
from odoo import models,fields,api,_
from lxml import etree

class kits_multi_website_recent_view(models.Model):
    _name = 'kits.multi.website.recent.view'
    _description = 'Multi Website Recent view'
    _order = 'create_date desc,sequence desc'

    website_id = fields.Many2one('kits.b2c.website','Website')
    product_id = fields.Many2one('product.product','Product')
    # product_ids = fields.One2many('kits.multi.website.recent.view.lines','recent_view_id','Products')
    customer_id = fields.Many2one('kits.multi.website.customer','Customer',ondelete="restrict")
    sequence = fields.Integer(index=True)
    image_1_url = fields.Char('Primary Url',related='product_id.primary_image_url',store=True)
    image_2_url = fields.Char('Secondary Url',related='product_id.sec_image_url',store=True)

