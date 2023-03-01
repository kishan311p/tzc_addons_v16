from odoo import models,fields,api,_
from datetime import datetime

class mailing_trace(models.Model):
    _inherit = 'mailing.trace'

    trace_status = fields.Selection(selection_add=[('received', 'Received'),('failed_mailgun','Mailgun Failed')])
    received = fields.Datetime('Received')
    failed_mailgun = fields.Datetime("Failed By Mailgun")

    @api.depends('sent', 'opened', 'clicked', 'replied', 'bounced', 'exception', 'ignored','failed_mailgun')
    def _compute_state(self):
        self.update({'state_update': fields.Datetime.now()})
        for stat in self:
            if stat.ignored:
                stat.state = 'ignored'
            elif stat.exception:
                stat.state = 'exception'
            elif stat.replied:
                stat.state = 'replied'
            elif stat.opened or stat.clicked:
                stat.state = 'opened'
            elif stat.bounced:
                stat.state = 'bounced'
            elif stat.sent:
                stat.state = 'sent'
            elif stat.failed_mailgun:
                stat.state = 'failed_mailgun'
            else:
                stat.state = 'outgoing'

    @api.model_create_multi
    def create(self,vals_list):
        res = super(mailing_trace,self).create(vals_list)
        campaing_contact_list=[]
        for trace in res:
            mailing_contact = self.env['mailing.contact'].search([('email','=',trace.email)],limit=1)
            
            campaing_contact_list.append({
                'trace_id':trace.id,
                'email':trace.email or '',
                'mass_mailing_id':trace.mass_mailing_id.id,
                'mailing_contact_id':mailing_contact.id,
                'activity_id':trace.marketing_trace_id.activity_id.id,
                'campaign_id':trace.marketing_trace_id.activity_id.campaign_id.id,
                'state':'draft',
            })
        self.env['campaign.report.contacts'].create(campaing_contact_list)
        return res

    # def set_clicked(self):
    #     res = super(mailing_trace,self).set_clicked()
    #     for rec in res:
    #         email_log_id = self.env['mailgun.email.logs'].search([('message_id','=',rec.message_id)],limit=1)
    #         if email_log_id:
    #             email_log_id.write({'clicked':datetime.now()})
    #     return res

    # def set_opened(self):
    #     res = super(mailing_trace,self).set_opened()
    #     for rec in res:
    #         email_log_id = self.env['mailgun.email.logs'].search([('message_id','=',rec.message_id)],limit=1)
    #         if email_log_id:
    #             email_log_id.write({'opened':datetime.now()})
    #     return res
