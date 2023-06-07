from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class delivery_box(models.Model):
    _name='delivery.box'
    _description = 'Delivery Box'

    name = fields.Char('Name')
    height = fields.Float('Height (in cm)')
    width = fields.Float('Width (in cm)')
    length = fields.Float('Length (in cm)')
