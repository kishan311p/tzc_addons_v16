from odoo import api, fields, models, _
from odoo.exceptions import UserError
from lxml import etree

class kits_multi_website_attribute_filter(models.Model):
    _name = "kits.multi.website.attribute.filter"
    _description = "Kits Multi Website Attribute Filter"
    _order = "sequence"

    name = fields.Char("Name")
    primary_attribute_filter_type = fields.Selection([('category','Category'),('shape','Shape'),('brand','Brand'),('gender','Gender'),('rim_type','Rim Type')], string="Primary Filter")
    gender_type = fields.Selection([('male','Male'),('female','Female'),('m/f','M/F')])
    brand_id = fields.Many2one("product.brand.spt","Brand")
    shape_id = fields.Many2one("product.shape.spt","Shape")
    rim_type_id = fields.Many2one("product.rim.type.spt","Rim Type")
    category_id = fields.Many2one("product.category","Category")
    attribute_filter_line_ids = fields.One2many("kits.multi.website.attribute.filter.line","attribute_filter_id","Attribute Filter Line")
    secondary_attribute_filter_type = fields.Selection([('category','Category'),('shape','Shape'),('brand','Brand'),('gender','Gender'),('rim_type','Rim Type')], string="Secondary Filter")
    is_slider = fields.Boolean("Is Slider")
    website_id = fields.Many2one("kits.b2c.website", "Website")
    filter_section_description = fields.Char("Filter Section Description")
    sequence = fields.Integer()
    
    @api.onchange('primary_attribute_filter_type')
    def check_primary_attribute_filter_type(self):
        for record in self:
            if record.primary_attribute_filter_type and record.primary_attribute_filter_type == record.secondary_attribute_filter_type:
                raise UserError("Primary Filter Type and Secondary Filter Type cannot be same!")

    @api.onchange('secondary_attribute_filter_type')
    def check_secondary_attribute_filter_type(self):
        for record in self:
            if record.secondary_attribute_filter_type and record.secondary_attribute_filter_type == record.primary_attribute_filter_type:
                raise UserError("Secondary Filter Type and Primary Filter Type cannot be same!")


    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_attribute_filter, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res


