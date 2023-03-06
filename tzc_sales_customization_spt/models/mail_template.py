from odoo import api,fields,models,_

class mail_template(models.Model):
    _inherit = "mail.template"

    def action_send_mail(self):
        ctx = {
            'default_model': 'mail.template',
            'default_res_id': self.id,
            'default_use_template': bool(self.id),
            'default_template_id': self.id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True,
            'default_email_layout_xmlid': "mail.mail_notification_light",
            # 'custom_layout': "mail.mail_notification_light",
            'force_email': True,
            'campaign':True,
            'resend':True,
            'raise_campaign':True,
            'subject':self.name,
        }
        return {
                'name': _('Send Mail'),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.compose.message',
                'binding_model':"marketing.campaign",
                'view_mode' : 'form',
                'target': 'new',
                'context':ctx
            }
