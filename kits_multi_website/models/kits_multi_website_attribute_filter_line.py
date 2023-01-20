from odoo import api, fields, models, _

class kits_multi_website_attribute_filter_line(models.Model):
    _name = "kits.multi.website.attribute.filter.line"
    _description = "Kits Multi Website Attribute Filter Line"

    attribute_filter_id = fields.Many2one("kits.multi.website.attribute.filter","Attribute Filter")
    gender_type = fields.Selection([('male','Male'),('female','Female'),('m/f','M/F')])
    brand_id = fields.Many2one("product.brand.spt","Brand")
    shape_id = fields.Many2one("product.shape.spt","Shape")
    rim_type_id = fields.Many2one("product.rim.type.spt","Rim Type")
    category_id = fields.Many2one("product.category","Category")
    image = fields.Char("Image",compute="_compute_image",store=True)
    image_url = fields.Char("Image URL")
    image_name = fields.Char("Image Name")
    redirect_url = fields.Char("Redirect URL",compute="_compute_redirect_url",store=True)

    @api.depends('image_url')
    def _compute_image(self):
        for record in self:
            record.image = record.image_url

    @api.depends('attribute_filter_id.primary_attribute_filter_type','attribute_filter_id.secondary_attribute_filter_type','attribute_filter_id.gender_type','attribute_filter_id.brand_id','attribute_filter_id.shape_id','attribute_filter_id.rim_type_id','attribute_filter_id.category_id','gender_type','brand_id','shape_id','rim_type_id','category_id')
    def _compute_redirect_url(self):
        website_id =  self.env['kits.b2c.website'].search([('website_name','=','b2c1')])

        for record in self:
            record.redirect_url = False
            if record.attribute_filter_id.primary_attribute_filter_type and record.attribute_filter_id.secondary_attribute_filter_type:
                base_url = website_id.url+"/shop"
                if record.attribute_filter_id.primary_attribute_filter_type == 'category':
                    record.redirect_url = "{}?type={}".format(base_url,record.attribute_filter_id.category_id.id)
                elif record.attribute_filter_id.primary_attribute_filter_type == 'brand':
                    record.redirect_url = "{}?brand={}".format(base_url,record.attribute_filter_id.brand_id.id)
                elif record.attribute_filter_id.primary_attribute_filter_type == 'gender':
                    record.redirect_url = "{}?gender={}".format(base_url,record.attribute_filter_id.gender_type)
                elif record.attribute_filter_id.primary_attribute_filter_type == 'shape':
                    record.redirect_url = "{}?shape={}".format(base_url,record.attribute_filter_id.shape_id.id)
                elif record.attribute_filter_id.primary_attribute_filter_type == 'rim_type':
                    record.redirect_url = "{}?rim_type={}".format(base_url,record.attribute_filter_id.rim_type_id.id)

                if record.attribute_filter_id.secondary_attribute_filter_type == 'category':
                    record.redirect_url += "&type={}".format(record.category_id.id)
                elif record.attribute_filter_id.secondary_attribute_filter_type == 'brand':
                    record.redirect_url += "&brand={}".format(record.brand_id.id)
                elif record.attribute_filter_id.secondary_attribute_filter_type == 'gender':
                    record.redirect_url += "&gender={}".format(record.gender_type)
                elif record.attribute_filter_id.secondary_attribute_filter_type == 'shape':
                    record.redirect_url += "&shape={}".format(record.shape_id.id)
                elif record.attribute_filter_id.secondary_attribute_filter_type == 'rim_type':
                    record.redirect_url += "&rim_type={}".format(record.rim_type_id.id)
            
