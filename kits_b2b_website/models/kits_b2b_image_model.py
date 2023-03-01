from odoo import fields, models, api, _


class kits_b2b_image_model(models.Model):
    _name = 'kits.b2b.image.model'
    _rec_name = 'url'
    _description = "B2B Images"

    sequence = fields.Integer('Sequence')
    header_description = fields.Text('Title')
    description = fields.Text('Description')
    redirect_url = fields.Char('Redirect URL')
    redirect_text = fields.Char('Button Text')
    url = fields.Char('Image URL')
    image_icon = fields.Char('Image', related="url")
    website_id = fields.Many2one('kits.b2b.website', 'Website')
    main_banner_id = fields.Many2one('kits.b2b.pages', 'Pages')
    our_core_values_id = fields.Many2one('kits.b2b.pages', 'Our Core Values')
    parent_id = fields.Many2one('kits.b2b.image.model', string='Parent')
    how_to_shop_page_id = fields.Many2one(
        'kits.b2b.pages',
        'How To shop Page'
    )
