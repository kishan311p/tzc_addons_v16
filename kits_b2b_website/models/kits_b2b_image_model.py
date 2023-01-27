from odoo import fields, models, api, _

class kits_b2b_image_model(models.Model):
    _name = 'kits.b2b.image.model'
    _rec_name = 'url'
    _description = "B2B Images"


    header_description = fields.Text('Header Description')
    description = fields.Text('Description')
    redirect_url = fields.Char('Redirect URL')
    redirect_text = fields.Char('Redirect Text')
    url = fields.Char('Image URL')
    image_icon = fields.Char('Image URL',compute="_compute_image_icon")
    website_id = fields.Many2one('kits.b2b.website','Website')
    main_banner_id = fields.Many2one('kits.b2b.pages','Pages')
    our_core_values_id = fields.Many2one('kits.b2b.pages','Our Core Values')
    parent_id = fields.Many2one('kits.b2b.image.model', string='Parent')

    @api.depends('url')
    def _compute_image_icon(self):
        for record in self:
            record.image_icon = record.url
