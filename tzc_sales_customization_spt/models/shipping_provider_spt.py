# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class shipping_provider_spt(models.Model):
    _name = 'shipping.provider.spt'
    _description = 'Shipping Provider'
    _order = "sequence,id"

    name = fields.Char('Shipping Provider',required="1")

    provider = fields.Selection(selection="_get_provider",string="Provider",required=True)
    sequence = fields.Integer()
    @api.model
    def _get_provider(self):
        return list(self.env['delivery.carrier']._fields['delivery_type'].selection)
