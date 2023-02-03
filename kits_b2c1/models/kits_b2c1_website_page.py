from odoo import api, fields, models, _

class kits_b2c1_website_page(models.Model):
    _name = "kits.b2c1.website.page"
    
    kits_web_url = "https://eto.keypress.in"    
    website_id = fields.Many2one("kits.b2c.website","Website")

    @api.model
    def default_get(self, fields):
        res = super(kits_b2c1_website_page, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res
    
    name = fields.Char("Name")
    page_type = fields.Selection([('homepage','Homepage'), ('header','Header'), ('footer','Footer'), ('about_us','About Us')], string="Page Type")

    homepage_banner_main_image_ids = fields.One2many("kits.multi.website.shoppage.banner","website_page_id","Homepage Banner Main Images")
    
    eyeglass_banner_image_1 = fields.Char("Eyeglass Banner Image 1",compute="_compute_eyeglass_banner_image_1",store=True)
    eyeglass_banner_image_1_url = fields.Char("Eyeglass Banner Image 1 Redirect URL")
    eyeglass_banner_image_2 = fields.Char("Eyeglass Banner Image 2",compute="_compute_eyeglass_banner_image_2",store=True)
    eyeglass_banner_image_2_url = fields.Char("Eyeglass Banner Image 2 Redirect URL")
    eyeglass_banner_image_category = fields.Many2one("kits.b2c1.menu.category","Eyeglass Banner Image Category")
    eyeglass_banner_image_gender_1 = fields.Selection([('male','Male'),('female','Female'),('m/f','Unisex')],string="Eyeglass Banner Image Gender")
    eyeglass_banner_image_gender_2 = fields.Selection([('male','Male'),('female','Female'),('m/f','Unisex')],string="Eyeglass Banner Image Gender")


    image_1 = fields.Char("Image 1",compute="_compute_image_1",store=True)
    image_1_url = fields.Char("Image 1 Redirect URL")
    image_2 = fields.Char("Image 2",compute="_compute_image_2",store=True)
    image_2_url = fields.Char("Image 2 Redirect URL")
    
    sunglass_banner_image_1 = fields.Char("Sunglass Banner Image 1",compute="_compute_sunglass_banner_image_1",store=True)
    sunglass_banner_image_1_url = fields.Char("Sunglass Banner Image 1 Redirect URL")
    sunglass_banner_image_2 = fields.Char("Sunglass Banner Image 2",compute="_compute_sunglass_banner_image_2",store=True)
    sunglass_banner_image_2_url = fields.Char("Sunglass Banner Image 2 Redirect URL")
    sunglass_banner_image_category = fields.Many2one("kits.b2c1.menu.category","Sunglass Banner Image Category")
    sunglass_banner_image_gender_1 = fields.Selection([('male','Male'),('female','Female'),('m/f','Unisex')],string="Sunglass Banner Image Gender")
    sunglass_banner_image_gender_2 = fields.Selection([('male','Male'),('female','Female'),('m/f','Unisex')],string="Sunglass Banner Image Gender")


    guide_image_1 = fields.Char("Guide Image 1",compute="_compute_guide_image_1",store=True)
    guide_image_1_url = fields.Char("Guide Image 1 Redirect URL")
    guide_image_2 = fields.Char("Guide Image 2",compute="_compute_guide_image_2",store=True)
    guide_image_2_url = fields.Char("Guide Image 2 Redirect URL")
    guide_image_3 = fields.Char("Guide Image 3",compute="_compute_guide_image_3",store=True)
    guide_image_3_url = fields.Char("Guide Image 3 Redirect URL")

    guide_image_1_name = fields.Char("Guide Image 1 Name")
    guide_image_2_name = fields.Char("Guide Image 2 Name")
    guide_image_3_name = fields.Char("Guide Image 3 Name")

    guide_section_name = fields.Char("Guide Section Name") 
    guide_section_description = fields.Char("Guide Section Description") 

    ad_image_1 = fields.Char("Ad Image 1",compute="_compute_ad_image_1",store=True)
    ad_image_1_url = fields.Char("Ad Image 1 Redirect URL")
    ad_image_2 = fields.Char("Ad Image 2",compute="_compute_ad_image_2",store=True)
    ad_image_2_url = fields.Char("Ad Image 2 Redirect URL")

    offer_main_image = fields.Char("Offer Main Image",compute="_compute_offer_main_image",store=True)
    offer_main_image_url = fields.Char("Offer Main Image Redirect URL")
    offer_image_1 = fields.Char("Offer Image 1",compute="_compute_offer_image_1",store=True)
    offer_image_1_url = fields.Char("Offer Image 1 Redirect URL")
    offer_image_2 = fields.Char("Offer Image 2",compute="_compute_offer_image_2",store=True)
    offer_image_2_url = fields.Char("Offer Image 2 Redirect URL")
    offer_image_3 = fields.Char("Offer Image 3",compute="_compute_offer_image_3",store=True)
    offer_image_3_url = fields.Char("Offer Image 3 Redirect URL")

    lens_feature_image_1 = fields.Char("Lens Feature Image 1",compute="_compute_lens_feature_image_1",store=True)
    lens_feature_image_1_url = fields.Char("Lens Feature Image 1 Redirect URL")
    lens_feature_image_2 = fields.Char("Lens Feature Image 2",compute="_compute_lens_feature_image_2",store=True)
    lens_feature_image_2_url = fields.Char("Lens Feature Image 2 Redirect URL")
    lens_feature_image_3 = fields.Char("Lens Feature Image 3",compute="_compute_lens_feature_image_3",store=True)
    lens_feature_image_3_url = fields.Char("Lens Feature Image 3 Redirect URL")
    lens_feature_image_4 = fields.Char("Lens Feature Image 4",compute="_compute_lens_feature_image_4",store=True)
    lens_feature_image_4_url = fields.Char("Lens Feature Image 4 Redirect URL")
    lens_feature_image_5 = fields.Char("Lens Feature Image 5",compute="_compute_lens_feature_image_5",store=True)
    lens_feature_image_5_url = fields.Char("Lens Feature Image 5 Redirect URL")
    lens_feature_image_6 = fields.Char("Lens Feature Image 6",compute="_compute_lens_feature_image_6",store=True)
    lens_feature_image_6_url = fields.Char("Lens Feature Image 6 Redirect URL")
    lens_feature_image_7 = fields.Char("Lens Feature Image 7",compute="_compute_lens_feature_image_7",store=True)
    lens_feature_image_7_url = fields.Char("Lens Feature Image 7 Redirect URL")
    lens_feature_image_8 = fields.Char("Lens Feature Image 8",compute="_compute_lens_feature_image_8",store=True)
    lens_feature_image_8_url = fields.Char("Lens Feature Image 8 Redirect URL")

    lens_feature_image_1_name = fields.Char("Lens Feature Image 1 Name")
    lens_feature_image_2_name = fields.Char("Lens Feature Image 2 Name")
    lens_feature_image_3_name = fields.Char("Lens Feature Image 3 Name")
    lens_feature_image_4_name = fields.Char("Lens Feature Image 4 Name")
    lens_feature_image_5_name = fields.Char("Lens Feature Image 5 Name")
    lens_feature_image_6_name = fields.Char("Lens Feature Image 6 Name")
    lens_feature_image_7_name = fields.Char("Lens Feature Image 7 Name")
    lens_feature_image_8_name = fields.Char("Lens Feature Image 8 Name")

    lens_feature_section_name = fields.Char("Lens Feature Section Name") 
    lens_feature_section_description = fields.Char("Lens Feature Section Description") 

    aspect_image_1 = fields.Char("Aspect Image 1",compute="_compute_aspect_image_1",store=True)
    aspect_image_1_url = fields.Char("Aspect Image 1 Redirect URL")
    aspect_image_2 = fields.Char("Aspect Image 2",compute="_compute_aspect_image_2",store=True)
    aspect_image_2_url = fields.Char("Aspect Image 2 Redirect URL")
    aspect_image_3 = fields.Char("Aspect Image 3",compute="_compute_aspect_image_3",store=True)
    aspect_image_3_url = fields.Char("Aspect Image 3 Redirect URL")
    aspect_image_4 = fields.Char("Aspect Image 4",compute="_compute_aspect_image_4",store=True)
    aspect_image_4_url = fields.Char("Aspect Image 4 Redirect URL")
    aspect_image_5 = fields.Char("Aspect Image 5",compute="_compute_aspect_image_5",store=True)
    aspect_image_5_url = fields.Char("Aspect Image 5 Redirect URL")

    aspect_image_1_name = fields.Char("Aspect Image 1 Name")
    aspect_image_2_name = fields.Char("Aspect Image 2 Name")
    aspect_image_3_name = fields.Char("Aspect Image 3 Name")
    aspect_image_4_name = fields.Char("Aspect Image 4 Name")
    aspect_image_5_name = fields.Char("Aspect Image 5 Name")

# public URL fields
    eyeglass_banner_image_1_public_url = fields.Char("Eyeglass Banner Image 1 Public URL")
    eyeglass_banner_image_2_public_url = fields.Char("Eyeglass Banner Image 2 Public URL")
    
    image_1_public_url = fields.Char("Image 1 Public URL")
    image_2_public_url = fields.Char("Image 2 Public URL")
    
    sunglass_banner_image_1_public_url = fields.Char("Sunglass Banner Image 1 Public URL")
    sunglass_banner_image_2_public_url = fields.Char("Sunglass Banner Image 2 Public URL")

    guide_image_1_public_url = fields.Char("Guide Image 1 Public URL")
    guide_image_2_public_url = fields.Char("Guide Image 2 Public URL")
    guide_image_3_public_url = fields.Char("Guide Image 3 Public URL")
    
    ad_image_1_public_url = fields.Char("Ad Image 1 Public URL")
    ad_image_2_public_url = fields.Char("Ad Image 2 Public URL")

    offer_main_image_public_url = fields.Char("Offer Main Image Public URL")
    offer_image_1_public_url = fields.Char("Offer Image 1 Public URL")
    offer_image_2_public_url = fields.Char("Offer Image 2 Public URL")
    offer_image_3_public_url = fields.Char("Offer Image 3 Public URL")

    lens_feature_image_1_public_url = fields.Char("Lens Feature Image 1 Public URL")
    lens_feature_image_2_public_url = fields.Char("Lens Feature Image 2 Public URL")
    lens_feature_image_3_public_url = fields.Char("Lens Feature Image 3 Public URL")
    lens_feature_image_4_public_url = fields.Char("Lens Feature Image 4 Public URL")
    lens_feature_image_5_public_url = fields.Char("Lens Feature Image 5 Public URL")
    lens_feature_image_6_public_url = fields.Char("Lens Feature Image 6 Public URL")
    lens_feature_image_7_public_url = fields.Char("Lens Feature Image 7 Public URL")
    lens_feature_image_8_public_url = fields.Char("Lens Feature Image 8 Public URL")

    aspect_image_1_public_url = fields.Char("Aspect Image 1 Public URL")
    aspect_image_2_public_url = fields.Char("Aspect Image 2 Public URL")
    aspect_image_3_public_url = fields.Char("Aspect Image 3 Public URL")
    aspect_image_4_public_url = fields.Char("Aspect Image 4 Public URL")
    aspect_image_5_public_url = fields.Char("Aspect Image 5 Public URL")

    homepage_keyword = fields.Char('Homepage Meta Keyword')
    homepage_title = fields.Char('Homepage Meta Title')
    homepage_description = fields.Text('Homepage Meta Description')

    # for eyeglasses 
    @api.onchange('eyeglass_banner_image_category','eyeglass_banner_image_gender_1')
    def _onchange_eyeglass_category_and_gender_1(self):
        for record in self:
            if record.eyeglass_banner_image_category and record.eyeglass_banner_image_gender_1:
                record.eyeglass_banner_image_1_url = "{}/shop?gender={}&type={}".format(self.kits_web_url,record.eyeglass_banner_image_gender_1,record.eyeglass_banner_image_category.id)
    
    @api.onchange('eyeglass_banner_image_category','eyeglass_banner_image_gender_2')
    def _onchange_eyeglass_category_and_gender_2(self):
        for record in self:
            if record.eyeglass_banner_image_category and record.eyeglass_banner_image_gender_2:
                record.eyeglass_banner_image_2_url = "{}/shop?gender={}&type={}".format(self.kits_web_url,record.eyeglass_banner_image_gender_2,record.eyeglass_banner_image_category.id)

    # for sunglasses
    @api.onchange('sunglass_banner_image_category','sunglass_banner_image_gender_1')
    def _onchange_sunglass_category_and_gender_1(self):
        for record in self:
            if record.sunglass_banner_image_category and record.sunglass_banner_image_gender_1:
                record.sunglass_banner_image_1_url = "{}/shop?gender={}&type={}".format(self.kits_web_url,record.sunglass_banner_image_gender_1,record.sunglass_banner_image_category.id)
    
    @api.onchange('sunglass_banner_image_category','sunglass_banner_image_gender_2')
    def _onchange_sunglass_category_and_gender_2(self):
        for record in self:
            if record.sunglass_banner_image_category and record.sunglass_banner_image_gender_2:
                record.sunglass_banner_image_2_url = "{}/shop?gender={}&type={}".format(self.kits_web_url,record.sunglass_banner_image_gender_2,record.sunglass_banner_image_category.id)

# compute methods
    # for eyeglass banner images
    @api.depends('eyeglass_banner_image_1_public_url')
    def _compute_eyeglass_banner_image_1(self):
        for record in self:
            record.eyeglass_banner_image_1 = record.eyeglass_banner_image_1_public_url
            
    @api.depends('eyeglass_banner_image_2_public_url')
    def _compute_eyeglass_banner_image_2(self):
        for record in self:
            record.eyeglass_banner_image_2 = record.eyeglass_banner_image_2_public_url
            
    # for images
    @api.depends('image_1_public_url')
    def _compute_image_1(self):
        for record in self:
            record.image_1 = record.image_1_public_url

    @api.depends('image_2_public_url')
    def _compute_image_2(self):
        for record in self:
            record.image_2 = record.image_2_public_url
  
    # for sunglass banner images
    @api.depends('sunglass_banner_image_1_public_url')
    def _compute_sunglass_banner_image_1(self):
        for record in self:
            record.sunglass_banner_image_1 = record.sunglass_banner_image_1_public_url
    
    @api.depends('sunglass_banner_image_2_public_url')
    def _compute_sunglass_banner_image_2(self):
        for record in self:
            record.sunglass_banner_image_2 = record.sunglass_banner_image_2_public_url
            
    # for guide images
    @api.depends('guide_image_1_public_url')
    def _compute_guide_image_1(self):
        for record in self:
            record.guide_image_1 = record.guide_image_1_public_url
            
    @api.depends('guide_image_2_public_url')
    def _compute_guide_image_2(self):
        for record in self:
            record.guide_image_2 = record.guide_image_2_public_url
            
    @api.depends('guide_image_3_public_url')
    def _compute_guide_image_3(self):
        for record in self:
            record.guide_image_3 = record.guide_image_3_public_url
            
    # for ad images
    @api.depends('ad_image_1_public_url')
    def _compute_ad_image_1(self):
        for record in self:
            record.ad_image_1 = record.ad_image_1_public_url
            
    @api.depends('ad_image_2_public_url')
    def _compute_ad_image_2(self):
        for record in self:
            record.ad_image_2 = record.ad_image_2_public_url
            
    # for offer images
    @api.depends('offer_main_image_public_url')
    def _compute_offer_main_image(self):
        for record in self:
            record.offer_main_image = record.offer_main_image_public_url
            
    @api.depends('offer_image_1_public_url')
    def _compute_offer_image_1(self):
        for record in self:
            record.offer_image_1 = record.offer_image_1_public_url
            
    @api.depends('offer_image_2_public_url')
    def _compute_offer_image_2(self):
        for record in self:
            record.offer_image_2 = record.offer_image_2_public_url
            
    @api.depends('offer_image_3_public_url')
    def _compute_offer_image_3(self):
        for record in self:
            record.offer_image_3 = record.offer_image_3_public_url
            
    # for lens feature images
    @api.depends('lens_feature_image_1_public_url')
    def _compute_lens_feature_image_1(self):
        for record in self:
            record.lens_feature_image_1 = record.lens_feature_image_1_public_url
            
    @api.depends('lens_feature_image_2_public_url')
    def _compute_lens_feature_image_2(self):
        for record in self:
            record.lens_feature_image_2 = record.lens_feature_image_2_public_url
        
    @api.depends('lens_feature_image_3_public_url')
    def _compute_lens_feature_image_3(self):
        for record in self:
            record.lens_feature_image_3 = record.lens_feature_image_3_public_url
        
    @api.depends('lens_feature_image_4_public_url')
    def _compute_lens_feature_image_4(self):
        for record in self:
            record.lens_feature_image_4 = record.lens_feature_image_4_public_url
        
    @api.depends('lens_feature_image_5_public_url')
    def _compute_lens_feature_image_5(self):
        for record in self:
            record.lens_feature_image_5 = record.lens_feature_image_5_public_url
        
    @api.depends('lens_feature_image_6_public_url')
    def _compute_lens_feature_image_6(self):
        for record in self:
            record.lens_feature_image_6 = record.lens_feature_image_6_public_url
        
    @api.depends('lens_feature_image_7_public_url')
    def _compute_lens_feature_image_7(self):
        for record in self:
            record.lens_feature_image_7 = record.lens_feature_image_7_public_url
        
    @api.depends('lens_feature_image_8_public_url')
    def _compute_lens_feature_image_8(self):
        for record in self:
            record.lens_feature_image_8 = record.lens_feature_image_8_public_url
            
    # for aspect images
    @api.depends('aspect_image_1_public_url')
    def _compute_aspect_image_1(self):
        for record in self:
            record.aspect_image_1 = record.aspect_image_1_public_url
            
    @api.depends('aspect_image_2_public_url')
    def _compute_aspect_image_2(self):
        for record in self:
            record.aspect_image_2 = record.aspect_image_2_public_url
            
    @api.depends('aspect_image_3_public_url')
    def _compute_aspect_image_3(self):
        for record in self:
            record.aspect_image_3 = record.aspect_image_3_public_url
            
    @api.depends('aspect_image_4_public_url')
    def _compute_aspect_image_4(self):
        for record in self:
            record.aspect_image_4 = record.aspect_image_4_public_url
            
    @api.depends('aspect_image_5_public_url')
    def _compute_aspect_image_5(self):
        for record in self:
            record.aspect_image_5 = record.aspect_image_5_public_url
