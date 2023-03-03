from odoo import fields, models, api, _

FILTER_MENU_TYPE = [
    ('filter', 'Filter'),
    ('redirect', 'Redirect')
]


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
    homepage_main_banner_id = fields.Many2one('kits.b2b.pages', 'Pages')
    our_core_values_id = fields.Many2one('kits.b2b.pages', 'Our Core Values')
    parent_id = fields.Many2one('kits.b2b.image.model', string='Parent')
    how_to_shop_page_id = fields.Many2one(
        'kits.b2b.pages',
        'How To shop Page'
    )
    login_id = fields.Many2one('kits.b2b.website', 'Login')
    filter_menu_id = fields.Many2one('kits.b2b.menus', 'Filter Menu')
    filter_menu_type = fields.Selection(
        selection=FILTER_MENU_TYPE,
        string='Type',
        default=FILTER_MENU_TYPE[0][0]
    )
    show_filter_menu_sliders = fields.Boolean(
        'Show Filter Menu Sliders',
        related='filter_menu_id.show_sliders'
    )
    offer_id = fields.Many2one('kits.b2b.pages', 'Offres')
    team_member_page_id = fields.Many2one('kits.b2b.pages', 'Team Member Page')
