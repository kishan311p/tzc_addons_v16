from odoo import api, fields, models, _
from odoo.exceptions import UserError
from lxml import etree

class kits_multi_website_coupon_terms_conditions(models.Model):
    _name = "kits.multi.website.coupon.terms.conditions"
    _description = "Kits Multi Website Coupon Terms Conditions"

    sequence = fields.Integer(index=True)
    name = fields.Char(string='Terms Conditions')
    coupon_id = fields.Many2one(comodel_name='kits.multi.website.coupon', string='Coupon')