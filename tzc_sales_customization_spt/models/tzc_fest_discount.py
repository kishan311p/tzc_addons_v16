from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError
from datetime import datetime

class tzc_fest_discount(models.Model):
    _name = 'tzc.fest.discount'
    _rec_name = 'name'

    special_discount_rule_ids = fields.One2many('kits.special.discount','tzc_fest_id','Special Discount')
    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')
    # active = fields.Boolean("Is Active",default=False)
    is_active = fields.Boolean("Is Active",default=False,copy=False)
    name = fields.Char('Name')
    description = fields.Text('Description')

    # field to enable 'dynamic label name' in website
    active_dynamic_label_name = fields.Boolean()
    dynamic_label_icon = fields.Binary()

    # Special discount banner for product category.
    special_discount_active_pro_categ_banner = fields.Boolean(string="Active Special Discount Category Banner")

    special_discount_category_banner_1 = fields.Binary()
    special_discount_category_banner_1_text = fields.Char()
    special_discount_category_banner_1_text_color = fields.Char()
    special_discount_category_banner_1_url = fields.Char()

    special_discount_category_banner_2 = fields.Binary()
    special_discount_category_banner_2_text = fields.Char()
    special_discount_category_banner_2_text_color = fields.Char()
    special_discount_category_banner_2_url = fields.Char()

    special_discount_category_banner_3 = fields.Binary()
    special_discount_category_banner_3_text = fields.Char()
    special_discount_category_banner_3_text_color = fields.Char()
    special_discount_category_banner_3_url = fields.Char()

    special_discount_category_banner_4 = fields.Binary()
    special_discount_category_banner_4_text = fields.Char()
    special_discount_category_banner_4_text_color = fields.Char()
    special_discount_category_banner_4_url = fields.Char()

    # eyeglass banner for product category.
    eyeglass_active_pro_categ_banner = fields.Boolean(string="Active Eyeglass Category Banner")

    eyeglass_category_banner_1 = fields.Binary()
    eyeglass_category_banner_1_text = fields.Char()
    eyeglass_category_banner_1_text_color = fields.Char()
    eyeglass_category_banner_1_url = fields.Char()

    eyeglass_category_banner_2 = fields.Binary()
    eyeglass_category_banner_2_text = fields.Char()
    eyeglass_category_banner_2_text_color = fields.Char()
    eyeglass_category_banner_2_url = fields.Char()

    eyeglass_category_banner_3 = fields.Binary()
    eyeglass_category_banner_3_text = fields.Char()
    eyeglass_category_banner_3_text_color = fields.Char()
    eyeglass_category_banner_3_url = fields.Char()

    eyeglass_category_banner_4 = fields.Binary()
    eyeglass_category_banner_4_text = fields.Char()
    eyeglass_category_banner_4_text_color = fields.Char()
    eyeglass_category_banner_4_url = fields.Char()

    # sunglass banner for product category.
    sunglass_active_pro_categ_banner = fields.Boolean(string="Active Sunglass Category Banner")

    sunglass_category_banner_1 = fields.Binary()
    sunglass_category_banner_1_text = fields.Char()
    sunglass_category_banner_1_text_color = fields.Char()
    sunglass_category_banner_1_url = fields.Char()

    sunglass_category_banner_2 = fields.Binary()
    sunglass_category_banner_2_text = fields.Char()
    sunglass_category_banner_2_text_color = fields.Char()
    sunglass_category_banner_2_url = fields.Char()

    sunglass_category_banner_3 = fields.Binary()
    sunglass_category_banner_3_text = fields.Char()
    sunglass_category_banner_3_text_color = fields.Char()
    sunglass_category_banner_3_url = fields.Char()

    sunglass_category_banner_4 = fields.Binary()
    sunglass_category_banner_4_text = fields.Char()
    sunglass_category_banner_4_text_color = fields.Char()
    sunglass_category_banner_4_url = fields.Char()

    # header message settings in website.
    active_message_header = fields.Boolean()
    message_header_text = fields.Char()
    
    # home page slider banner

    active_home_page_slider = fields.Boolean()

    home_page_slider_header_text = fields.Char()
    home_page_slider_subheader_text = fields.Char()

    home_page_slider_banner_1 = fields.Binary()
    home_page_slider_banner_1_text = fields.Char()
    home_page_slider_banner_1_url = fields.Char()
    
    home_page_slider_banner_2 = fields.Binary()
    home_page_slider_banner_2_text = fields.Char()
    home_page_slider_banner_2_url = fields.Char()
    
    home_page_slider_banner_3 = fields.Binary()
    home_page_slider_banner_3_text = fields.Char()
    home_page_slider_banner_3_url = fields.Char()

    # home page second slider banner

    active_home_page_second_slider = fields.Boolean()

    home_page_second_slider_header_text = fields.Char()
    home_page_second_slider_subheader_text = fields.Char()

    home_page_second_slider_banner_1 = fields.Binary()
    home_page_second_slider_banner_1_text = fields.Char()
    home_page_second_slider_banner_1_url = fields.Char()
    
    home_page_second_slider_banner_2 = fields.Binary()
    home_page_second_slider_banner_2_text = fields.Char()
    home_page_second_slider_banner_2_url = fields.Char()
    
    home_page_second_slider_banner_3 = fields.Binary()
    home_page_second_slider_banner_3_text = fields.Char()
    home_page_second_slider_banner_3_url = fields.Char()


    @api.constrains('is_active')
    def active_rec_validation(self):
        if self.is_active:
            active_rec = self.search([('is_active','=',True)])
            if len(active_rec) > 1:
                raise UserError(f'You can not have 2 discount campaigns at the same time please First Deactivate {active_rec.name}')

    def action_active(self):
        # special_discount_menu_id = self.env.ref('tzc_website.tzc_black_special_friday_sale')
        # main_menu_id = self.env['website.menu'].search([('name','like','Top Menu for Website 2')],limit=1)
        for rec in self:
            rec.is_active = False
            # special_discount_menu_id.parent_id = False
            # self.env.ref('tzc_website.tzc_sale').parent_id = main_menu_id

    def action_deactive(self):
        active_rec = self.search([('is_active','=',True)])
        # special_discount_menu_id = self.env.ref('tzc_website.tzc_black_special_friday_sale')
        # main_menu_id = self.env['website.menu'].search([('name','like','Top Menu for Website 2')],limit=1)
        for rec in self:
            if not active_rec:
                rec.is_active = True
                # if rec.to_date and rec.to_date >= datetime.now().date():
                #     special_discount_menu_id.parent_id = main_menu_id.id if main_menu_id else None
                #     self.env.ref('tzc_website.tzc_sale').parent_id = False
                # else:
                #     if self.env.ref('tzc_website.tzc_sale').parent_id:
                #         self.env.ref('tzc_website.tzc_sale').parent_id = main_menu_id
                #     if special_discount_menu_id.parent_id:
                #         special_discount_menu_id.parent_id = False
            else:
                raise UserError(f'You can not have 2 discount campaigns at the same time please First Deactivate {active_rec.name}')

    # This method is for home page banner xml.
    # def check_validity(self,active_fest_id=None):
    #     if active_fest_id:
    #         applicable = False
    #         if active_fest_id.from_date and active_fest_id.to_date :
    #             if active_fest_id.from_date <= datetime.now().date() and active_fest_id.to_date >= datetime.now().date():
    #                 applicable = True
    #         elif active_fest_id.from_date:
    #             if active_fest_id.from_date <= datetime.now().date():
    #                 applicable = True
    #         elif active_fest_id.to_date:
    #             if active_fest_id.to_date >= datetime.now().date():
    #                 applicable = True
    #         else:
    #             if not active_fest_id.from_date:
    #                 applicable = True
    #             if not active_fest_id.to_date:
    #                 applicable = True
    #     else:
    #         applicable = False
    
    #     return applicable

    def check_special_discount(self):
        active_fest_id = self.search([('is_active','=',True)])
        if active_fest_id:
            for rec in active_fest_id:
                if rec.to_date and rec.to_date < datetime.now().date():
                    rec.is_active = False
                    # self.env.ref('tzc_website.tzc_black_special_friday_sale').parent_id = False
                    # main_menu_id = self.env['website.menu'].search([('name','like','Top Menu for Website 2')],limit=1)
                    # self.env.ref('tzc_website.tzc_sale').parent_id = main_menu_id if main_menu_id else False
                    # for internal_user in self.env.ref('base.group_user').users:
                    #     template_id = self.env.ref('tzc_sales_customization_spt.mail_template_notify_internal_user_sale_end')
                    #     template_id.email_to = internal_user.email
                    #     template_id.with_context(user_name=internal_user.name).send_mail(rec.id,force_send=True,notif_layout="mail.mail_notification_light")
