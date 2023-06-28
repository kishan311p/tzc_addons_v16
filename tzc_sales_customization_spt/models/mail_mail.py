from odoo import _,api,models,fields
from odoo.addons.base.models.ir_mail_server import MailDeliveryException
from odoo import tools
import ast
import base64
import logging
import psycopg2
import smtplib
import re

import logging
_logger = logging.getLogger(__name__)
class mail_mail(models.Model):
    _inherit = 'mail.mail'


    @api.model_create_multi
    def create(self, values_list):
        partner_obj = self.env['res.partner']
        for val in values_list:
            if val.get('email_to'):
                email_to = val.get('email_to')
                partners = email_to.split(',')
                for partner_email in partners:
                    partner = partner_obj.search([('email','=',partner_email)],limit=1)
                    if not self._context.get('user_template'):
                        if partner.customer_type != 'b2b_regular':
                            values_list.pop(values_list.index(val))
            if val.get('recipient_ids'):
                try:
                    partner = partner_obj.browse(val.get('recipient_ids')[0][1])
                    if not self._context.get('user_template'):
                        if partner.customer_type != 'b2b_regular':
                            values_list.pop(values_list.index(val))
                except:
                    pass
                    # update_emails.append(partner.email)
            # email_to = (',').join(list(update_emails))
        # self._cr.execute("SELECT email FROM mail_blacklist WHERE active=true")
        # blacklist = {x[0] for x in self._cr.fetchall()}
        # for rec in res:
        #     rec.recipient_ids = rec.partner_ids.filtered(lambda x : x.email not in blacklist)
        # return res 
        return super(mail_mail,self).create(values_list)
