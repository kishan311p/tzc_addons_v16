from odoo import api, fields, models


class KitsB2BHomeAdvertisement(models.Model):
    _name = 'kits.b2b.home.advertisement'
    _description = 'B2B Home Advertisement'

    name = fields.Html('Description')
    icon_url = fields.Char('Icon URL')
    icon = fields.Char(
        'Icon',
        compute="_compute_icon",
        store=True,
        compute_sudo=True
    )
    page_id = fields.Many2one('kits.b2b.website', 'website')

    @api.depends('icon_url')
    def _compute_icon(self):
        for record in self:
            record.icon = record.icon_url