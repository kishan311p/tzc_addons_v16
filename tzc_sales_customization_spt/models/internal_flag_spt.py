from odoo import models, fields, api, _


class internal_flag_spt(models.Model):
    _name = 'internal.flag.spt'
    _description = 'Internal Flag'

    name = fields.Char('Internal Flag')