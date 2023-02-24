from odoo import _, api, fields, models, tools
# from datetime import datetime
from dateutil.relativedelta import relativedelta
import requests

# datetime.fromtimestamp(y.get('items')[0]['timestamp'])

class mailgun_email_logs(models.Model):
    _name = 'mailgun.email.logs'
    _rec_name = "subject"

    state = fields.Selection([('sent','Sent'),('received','Received'),('fail','Failed')])
    date = fields.Datetime("Date")
    # status = fields.Char("Status")
    # message = fields.Char("Description")
    email_to = fields.Char('Email To')
    email_from = fields.Char('Email From')
    subject = fields.Char('Subject')
    message_id = fields.Char('Message Id')
    active = fields.Boolean(default=True)
    body = fields.Html()
    reply_to = fields.Char()
    create_user_id = fields.Many2one('res.users','Email Sender')
    # trace_id = fields.Many2one('mailing.trace','Mailing Trace ',required=True,ondelete='cascade')

    sent = fields.Datetime('Sent ')
    opened = fields.Datetime('Opened ')
    clicked = fields.Datetime('Clicked ')
    failed = fields.Datetime('Odoo Failed ')
    failed_mailgun = fields.Datetime('Mailgun Failed ')
    received = fields.Datetime('Received ')

    # def action_fetch_mailgun_mail_logs(self):
    #     api_key = self.env['ir.config_parameter'].sudo().get_param('mailgun.webhook.signin.key',False)
    #     response = requests.get("https://api.mailgun.net/v3/mg.teameto.com/events",auth=("api", api_key),params={"event": "failed"})
    #     new_log = []
    #     for log in response.json().get('items'):
    #         message_id = '<'+log.get('message').get('headers').get('message-id')+'>' if log.get('message').get('headers').get('message-id') else False
    #         exist_rec_id = self.search([('message_id','=',message_id)])
    #         if not exist_rec_id:
    #             rec_vals = {
    #                 'date':datetime.fromtimestamp(log.get('timestamp')),
    #                 'status':log.get('event'),
    #                 'message':log.get('delivery-status').get('message') or log.get('delivery-status').get('description'),
    #                 'email_to':log.get('message').get('headers').get('to'),
    #                 'email_from':log.get('message').get('headers').get('from'),
    #                 'message_id':message_id,
    #                 'subject':log.get('message').get('headers').get('subject'),
    #                 }

    #             log_id = self.create(rec_vals)
    #             new_log.append(log_id)
        
    #     if new_log and self.search([],limit=1).id:
    #         template_id = self.env.ref('tzc_sales_customization_spt.mail_template_notify_failed_email_logs')
    #         template_id.send_mail(self.search([],limit=1).id,force_send=True,notif_layout="mail.mail_notification_light")

    def action_manage_email_logs(self):
        days = int(self.env['ir.config_parameter'].sudo().get_param('mail_marketing_customization_spt.email_log_duration',0))
        actual_date = max(self.search([]).mapped('date')) - relativedelta(days=days)
        old_logs = self.search([]).filtered(lambda x:x.date.date() < actual_date.date())
        for log in old_logs:
            log.sudo().unlink()
