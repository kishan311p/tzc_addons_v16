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