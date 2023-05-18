from odoo import _, api, fields, models

class product_import_on_barcode_line(models.Model):
    _name = 'product.import.on.barcode.line'
    _description = 'Product Import On Barcode Line'
    
    import_id = fields.Many2one('product.import.on.barcode', string='Import')
    product_id = fields.Many2one('product.product','Product')
    opration = fields.Selection([('create', 'Create'),('update', 'Update')], string='Opration',default="update")
    barcode = fields.Char('Barcode')
    categ_id = fields.Many2one('product.category', string='Category')
    brand_id = fields.Many2one('product.brand.spt', string='Brand')
    model_id = fields.Many2one('product.model.spt', string='Model')
    mcc_id = fields.Many2one('kits.product.color.code', string='Manufacturing Color Code')
    eye_size_id = fields.Many2one('product.size.spt', string='Eye Size')
    bridge_size_id = fields.Many2one('product.bridge.size.spt', string='Bridge Size')
    temple_size_id = fields.Many2one('product.temple.size.spt', string='Temple Size')
    case_product_id = fields.Many2one('product.product', string='Case Product')
    image_url = fields.Char('Image1 URL')
    image_secondary_url = fields.Char('Image2 URL')
    product_color_id =  fields.Many2one('product.color.spt','Product Color ')
    secondary_color_id =  fields.Many2one('product.color.spt','Secondary Color ')
    lense_color_id =  fields.Many2one('product.color.spt','Lense Color ')
    material_id = fields.Many2one('product.material.spt', string='Material')
    shape_id = fields.Many2one('product.shape.spt', string='Shape')
    gender = fields.Selection([('male','Male'),('female','Female'),('m/f','M/F')], string='Gender')
    country_of_origin_id = fields.Many2one('res.country', string='Country Of Origin')
    name = fields.Char('Name')
    internal_reference = fields.Char('Internal Reference')
    seo_keyword = fields.Char('SEO Keyword')
    quantity_available = fields.Integer(' Available Quantity')    
    quantity = fields.Integer('Quantity')    
    add_up_quantity = fields.Boolean('Add Up Quantity')
    rim_type = fields.Many2one('product.rim.type.spt','Rim Type')
    