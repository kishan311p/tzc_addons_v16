from odoo import models,fields,api,_


class res_country_group(models.Model):
    _inherit = "res.country.group"

    country_ids = fields.One2many('res.country','territory_id',string="countries")

class res_country(models.Model):
    _inherit = "res.country"

    territory_id = fields.Many2one('res.country.group','Territory')
