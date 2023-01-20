from odoo import api, fields, models, _
from lxml import etree

class kits_paid_shipping_rule_line(models.Model):
    _name = 'kits.paid.shipping.rule.line'
    _description = "Kits Paid Shipping Rule"

    name = fields.Char("Name")
    days = fields.Float("Shipping Days")
    amount = fields.Float('Amount(USD)')
    shipping_rule_id  = fields.Many2one('kits.free.shipping.rule','Shipping Rule')