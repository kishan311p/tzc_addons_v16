# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class shipping_provider_spt(models.Model):
    _name = 'shipping.provider.spt'
    _description = 'Shipping Provider'
    _order = "sequence,id"

    name = fields.Char('Shipping Provider',required="1")

    provider = fields.Selection(selection="_get_provider",string="Provider",required=True)
    sequence = fields.Integer()
    carrier_id = fields.Many2one('delivery.carrier','Service Type')
    is_tracking_req_flag = fields.Boolean('Tracking No. Required ?')
    active = fields.Boolean('Active',default=True)
    is_published = fields.Boolean('Is Published',default=True)
    

    @api.model
    def _get_provider(self):
        return list(self.env['delivery.carrier']._fields['delivery_type'].selection)

    def action_published(self):
        for record in self:
            record.is_published = True

    def action_unpublished(self):
        for record in self:
            record.is_published = False
