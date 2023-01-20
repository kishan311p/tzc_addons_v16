from odoo import api, fields, models, _

class kits_b2c1_website_menu(models.Model):
    _name = "kits.b2c1.website.menu"
    _order = "sequence"

    name = fields.Char("Name")
    is_mega_menu = fields.Boolean("Is Mega Menu")
    product_filter = fields.Selection([('category','Product Category'), ('sale_type','Sale Type'), ('new_arrivals','New Arrival')])
    menu_url = fields.Char("Menu URL") 
    sequence = fields.Integer()
    website_id = fields.Many2one("kits.b2c.website","Website")
    menu_icon = fields.Char("Menu Icon",compute="_compute_menu_icon",store=True)
    menu_icon_url = fields.Char("Menu Icon URL")

    product_category_ids = fields.Many2many("product.category","website_menu_product_category_rel","website_menu_id","product_category_id","Product Categories") 
    sale_type = fields.Selection([('on_sale','On Sale'), ('clearance','Clearence')])
    sale_type_on_sale = fields.Boolean("On Sale")
    sale_type_clearence = fields.Boolean("Clearence")
    new_arrivals = fields.Boolean("New Arrival")


    metadata_keyword = fields.Char('Metadata Keyword')
    metadata_title = fields.Char('Metadata Title')
    metadata_description = fields.Text('Metadata Description')
    
    @api.model
    def default_get(self, fields):
        res = super(kits_b2c1_website_menu, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res

    @api.depends('menu_icon_url')
    def _compute_menu_icon(self):
        for record in self:
            record.menu_icon = record.menu_icon_url
