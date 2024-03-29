from odoo import fields, models, api, _
from odoo.exceptions import UserError

MENU_TYPE = [
    ('filter', 'Filter'),
    ('redirect', 'Redirect')
]


class kits_b2b_menus(models.Model):
    _name = 'kits.b2b.menus'
    _description = "B2B Menus"

    name = fields.Char('Name')
    website_id = fields.Many2one('kits.b2b.website', 'Website')
    page_id = fields.Many2one('kits.b2b.pages', 'Page')
    is_published = fields.Boolean('Is Published')
    sequence = fields.Integer(index=True,)
    my_dashboard_model_id = fields.Many2one('kits.b2b.website', 'My Dashboard')
    redirect_url = fields.Char('Redirect URL')
    query_params = fields.Char('Query Params')
    fileter_params = fields.Char('Fileter Params')
    menu_type = fields.Selection(
        selection=MENU_TYPE,
        default=MENU_TYPE[0][0],
        string='Type',
        help="""
        dashboard - Menu will be shown in user dashboard
        filter - Menu will be show in header and work as filter
        redirect - Menu will be show in header and redirect to url
        """
    )
    in_more = fields.Boolean('In More?')
    show_sliders = fields.Boolean('Show Sliders ?')
    slider_ids = fields.One2many(
        'kits.b2b.image.model',
        'filter_menu_id',
        string='Sliders'
    )

    meta_keyword = fields.Char('Meta Keyword')
    meta_title = fields.Char('Meta Title')
    meta_description = fields.Text('Meta Description')

    def product_is_publish(self):
        self.write({'is_published':True})
    
    def product_is_unpublish(self):
        self.write({'is_published':False})
        
    @api.constrains('slider_ids')
    def _constrains_slider_ids(self):
        for record in self:
            if len(record.slider_ids) > 6:
                raise UserError(_('Only 6 records are allowed.'))