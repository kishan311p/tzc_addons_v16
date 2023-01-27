from odoo import fields, models, api, _

class kits_b2b_website_slider(models.Model):
    _name = 'kits.b2b.website.slider'
    _description = "B2B Sliders"
    
    name = fields.Text('Name')
    website_id = fields.Many2one('kits.b2b.website','Website')
    slider_type = fields.Selection([('products', 'products'),('eyeglasses', 'Eyeglasses'),('sunglasses', 'Sunglasses'),('new_arrivals', 'New Arrivals'),('sales', 'Sales'),('brands', 'Brands'),('our_story', 'Our Story'),('contact_us', 'Contact Us'),('offers', 'Offers')], string='Type')
    product_ids = fields.Many2many('product.product','kits_b2b_website_slider_with_products_ral','slider_id','product_id','Products')
    page_id = fields.Many2one('kits.b2b.pages','Page')
    image_id = fields.Many2one('kits.b2b.image.model','Image')
    image = fields.Char('Image',related='image_id.url',store=True)
    limit = fields.Integer('Limit')
    parent_id = fields.Many2one('kits.b2b.website.slider','Parent')
