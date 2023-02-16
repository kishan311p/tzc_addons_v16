from odoo import _, api, fields, models

class res_users(models.Model):
    _inherit = 'res.users'

    token_ids = fields.One2many('kits.b2b.user.token', 'user_id', string='Token')

    def kits_b2b_user_verification_sent_email(self):
        mail_template = self.env.ref('user_access.mail_template_user_signup_confirmation')
        mail_template.sudo().send_mail(res_id= self.id,force_send=True)
        return{}

    
    def get_image(self):
        return {'image': self.partner_id.image_128}

    def action_b2b_reset_password_url(self,website):
        try:
            website = self.env['kits.b2b.website'].browse(website)
            tmp_id = self.env.ref('kits_b2b_website.mail_template_b2b_reset_password_email')
            tmp_id = tmp_id.with_context(url='%s/forget-password?code=%s&login=%s'%(website.url or '',self.access_token,self.login),days=website.reset_password_validity_in_hours)
            tmp_id.sudo().send_mail(self.id,force_send=True)
            return {'success':True,'message':'Email send your email account.'}
        except:
            return {'error': 'Email send error.'}