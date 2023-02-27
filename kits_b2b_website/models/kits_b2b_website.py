from odoo import fields, models, api, _

class kits_b2b_website(models.Model):
    _name = 'kits.b2b.website'
    _description = "B2B Website"

    name = fields.Char('Name')
    website_name = fields.Selection([('b2b1', 'B2B1')], string='Type')
    url = fields.Char('Website URL')
    is_allow_for_geo_restriction = fields.Boolean('Apply Geo Restriction')
    company_id = fields.Many2one('res.company', string='Company')
    login_validity_in_days = fields.Integer('Login Validity In Days')
    reset_password_validity_in_hours = fields.Integer('Reset Password Validity In Hours')
    pricelist_id = fields.Many2one('product.pricelist', string='Default Pricelist')
    portal_user_id = fields.Many2one('res.group', string='Default Portal User')
    my_dashboard_ids = fields.One2many('kits.b2b.menus','my_dashboard_model_id','My Dashboard')
    logo = fields.Char('Logo',related="image_logo")
    image_logo = fields.Char('Logo')
    stock_location_id = fields.Many2one('stock.location', string='Stock Location')
    virtual_location_id = fields.Many2one('stock.location', string='Virtual Location')
    recommended_products_ids = fields.Many2many('product.product', string='Recommended Products')
    shipping = fields.Html('Shipping')
    privacy_policy = fields.Html('Privacy Policy')
    terms_and_conditions = fields.Html('Terms and Conditions')
    show_product_image = fields.Selection([('front_face','Front Face'),('side_face','Side Face')],string="Shop Product Image Face",default='front_face')
