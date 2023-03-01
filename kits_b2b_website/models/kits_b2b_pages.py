from odoo import fields, models, api, _

class kits_b2b_pages(models.Model):
    _name = 'kits.b2b.pages'
    _description = "B2B Pages"

    name = fields.Char('Name')
    website_id = fields.Many2one('kits.b2b.website', 'Website')
    page_type = fields.Selection([('home', 'Home Page'), ('eyeglasses', 'Eyeglasses'), ('sunglasses', 'Sunglasses'), ('new_arrivals', 'New Arrivals'), ('sales', 'Sales'), (
        'brands', 'Brands'), ('our_story', 'Our Story'), ('contact_us', 'Contact Us'), ('faqs', 'FAQs'), ('our_core_values', 'Our Core Values')], string='Type')
    main_banner_ids = fields.One2many(
        'kits.b2b.image.model', 'main_banner_id', 'Main Banner')
    our_core_values_ids = fields.One2many(
        'kits.b2b.image.model', 'our_core_values_id', 'Our Core Values')
    header_text_1 = fields.Char('Header Text')
    text_1 = fields.Char('Text')
    image_url_text_1 = fields.Char('Image URL')
    image_url_text_1_copy = fields.Char('Image', related="image_url_text_1")
    text_1_redirect_url = fields.Text('Redirect URL')
    text_1_redirect_url_text = fields.Char('Redirect URL Text')
    banner_1_id = fields.Many2one('kits.b2b.image.model', 'Banner URL')
    banner_1_image = fields.Char(
        'Banner Image', related='banner_1_id.url', store=True)
    slider_ids = fields.One2many(
        'kits.b2b.website.slider', 'page_id', 'Sliders')
    key_value_model_ids = fields.One2many(
        'kits.b2b.key.value.model', 'page_id', 'Key Value')
    header_text_2 = fields.Char('Header Text')
    text_2 = fields.Char('Text')
    image_url_text_2 = fields.Char('Image URL')
    image_url_text_2_copy = fields.Char('Image', related="image_url_text_2")
    text_field = fields.Html('Text Field')
    banner_2_id = fields.Many2one('kits.b2b.image.model', 'Banner 2')
    banner_2_image = fields.Char(
        'Banner 2 Image', related='banner_2_id.url', store=True)
    is_our_core_values = fields.Boolean('Use For Our Core Values')

    # Contact Us Sliders
    contact_us_slider_ids = fields.One2many(
        'kits.b2b.website.slider', 'cu_page_id', 'Sliders'
    )
    char_field = fields.Char('Char Field')
    
