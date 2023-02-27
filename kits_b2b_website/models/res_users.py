from odoo import _, api, fields, models


class res_users(models.Model):
    _inherit = 'res.users'

    token_ids = fields.One2many(
        'kits.b2b.user.token', 'user_id', string='Token')

    # def kits_b2b_user_verification_sent_email(self):
    #     mail_template = self.env.ref('kits_b2b_website.mail_template_user_signup_confirmation')
    #     mail_template.sudo().send_mail(res_id= self.id,force_send=True,email_layout_xmlid="mail.mail_notification_light")
    #     return{}

    # For API to send Signup mails to salespersons
    def send_signup_mail_to_salespersons(self, country_id):
        user_obj = self.env['res.users'].sudo()
        user_ids_spt = eval(
            self.env['ir.config_parameter'].sudo().get_param('user_ids_spt', '[]'))
        sale_persons = user_obj.search(
            [('is_salesperson', '=', True), ('country_ids', 'in', country_id)])

        salesperson_ids = user_obj.browse(user_ids_spt)
        if sale_persons:
            salesperson_ids |= sale_persons

        partner_ids = salesperson_ids.mapped('partner_id')
        manager_group = self.env.ref(
            'tzc_sales_customization_spt.group_sales_manager_spt')
        if manager_group.sudo().users:
            contact_allowed_users = manager_group.sudo().users.filtered(
                lambda x: country_id in x.contact_allowed_countries.ids and x.partner_id not in partner_ids)
            if contact_allowed_users:
                partner_ids |= contact_allowed_users.mapped('partner_id')
        
        # Find managers
        email_cc = False
        if manager_group:
            manager_ids = manager_group.sudo().mapped("users")
            notify_mails = [manager.email for manager in manager_ids  for sale_peson in sale_persons if sale_peson in manager.allow_user_ids]
            if notify_mails:
                email_cc = ','.join(notify_mails)

        # Notify Salespersons about user signup.
        self.env.ref('tzc_sales_customization_spt.tzc_mail_template_new_user_spt').with_context({'allow_sale_manager': email_cc}).sudo(
        ).send_mail(self.partner_id.id, force_send=True, email_values={'recipient_ids': [(6, 0, partner_ids.ids)]})

        return {}

    def get_image(self):
        return {'image': self.partner_id.image_128}

    def action_b2b_reset_password_url(self, website):
        try:
            website = self.env['kits.b2b.website'].browse(website)
            tmp_id = self.env.ref(
                'kits_b2b_website.mail_template_b2b_reset_password_email')
            tmp_id = tmp_id.with_context(url='%s/forget-password?code=%s&login=%s' % (
                website.url or '', self.access_token, self.login), days=website.reset_password_validity_in_hours)
            tmp_id.sudo().send_mail(self.id, force_send=True)
            return {'success': True, 'message': 'Email send your email account.'}
        except:
            return {'error': 'Email send error.'}
