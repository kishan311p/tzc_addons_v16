# -*- coding: utf-8 -*-
# Part of SnepTech See LICENSE file for full copyright and licensing details.##
##############################################################################
from odoo import models, fields, api, _


class business_type_spt(models.Model):
    _name = 'business.type.spt'
    _description = 'Bussiness Type'

    name = fields.Char('Business Type')