from odoo import api, fields, models, _

class kits_multi_website_sign_up_otp(models.Model):
    _name = "kits.multi.website.sign.up.otp"

    email = fields.Char("Email")
    otp = fields.Char("OTP")
    otp_validity = fields.Datetime("OTP Validity")

    @api.model
    def send_otp_email(self,customer_email):
        sign_up_otp_id = self.env['kits.multi.website.sign.up.otp'].search([('email','=',customer_email)],limit=1)
        if sign_up_otp_id:
            mail_template = self.env.ref('kits_multi_website.multi_website_otp_email_template')
            mail_template.sudo().send_mail(sign_up_otp_id.id,force_send=True,email_layout_xmlid="mail.mail_notification_light")
            return {"email_sent":True,"error": False}
        else:
            return {"email_sent":False,"error": "Record Not Found"}


    @api.model
    def guest_send_email(self,customer_email):
        record = self.search([('email','=',customer_email.strip())],limit=1)
        if customer_email:
            mail_template = self.env.ref('kits_multi_website.multi_website_guest_otp_email_template')
            mail_template.sudo().send_mail(res_id= record.id,force_send=True,email_layout_xmlid="mail.mail_notification_light")
            return {"email_sent":True,"error": False}
        else:
            return {"email_sent":False,"error": "Email Not Found"}


    
    def reset_password_email(self,customer_email):
        customer_id = self.sudo().search([('email','=',customer_email)])
        if customer_email:
            mail_template = self.env.ref('kits_multi_website.kits_multi_website_reset_password_email')
            mail_template.sudo().send_mail(res_id= customer_id.id,force_send=True,email_layout_xmlid="mail.mail_notification_light")
            return {"email_sent":True,"error": False}
        else:
            return {"email_sent":False,"error": "Customer Not Found"}
