from odoo import _, api, fields, models, tools
import logging
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class delivery_carrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_product_id = fields.Many2one('product.product','Delivery Product ')
    is_default = fields.Boolean()
    is_published = fields.Boolean()
    is_freight = fields.Boolean()

    def write(self,vals):
        res = super(delivery_carrier,self).write(vals)
        if vals.get('integration_level'):
            vals['integration_level'] = 'rate'
        return res

    @api.model
    def create(self,vals):
        res = super(delivery_carrier,self).create(vals)
        if vals.get('integration_level'):
            vals['integration_level'] = 'rate'
        return res