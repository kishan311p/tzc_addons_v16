from odoo import _, api, fields, models, tools, Command
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools.safe_eval import safe_eval

import ast

def _reopen(self, res_id, model, context=None):
        context = dict(context or {}, default_model=model)
        return {'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_id': res_id,
                'res_model': self._name,
                'target': 'new',
                'context': context,
                }

class mail_compose_message_wizard(models.TransientModel):
    _inherit = "mail.compose.message"

    campaign_name = fields.Char("Campaign Name")

    _sql_constraints = [
        ('name_campaign_uniq', 'check(1=1)', 'Campaign name must be unique !'),
    ]

    @api.constrains('campaign_name')
    def _camp_name_const(self):
        res_partner_model_id = self.env.ref('base.model_res_partner').sudo().model
        res_users_model_id = self.env.ref('base.model_res_users').sudo().model
        for rec in self:
            if rec.model and (rec.model == res_partner_model_id or rec.model == res_users_model_id):
                campaign_names  = self.env['marketing.campaign'].search([]).mapped('name')
                if rec.campaign_name in campaign_names:
                    raise UserError ('Campaign name must be unique !')

    @api.onchange('template_id','subject')
    def _get_campaign_name(self):
        for rec in self:
            if rec.subject:
                rec.campaign_name = rec.subject
            else:
                rec.campaign_name = ''

    def action_send_mail(self):
        if self._context.get('quotation_send'):
            ctx = self._context.copy()
            ctx.update({'mail_notify_author': True})
            self.env.context = ctx
        if self._context.get('signature_user'):
            ctx = self._context.copy()
            signature = self.env['res.users'].browse(ctx.get('signature_user')).signature
            ctx.update({'signature': signature}) 
            self.env.context = ctx
        if self._context.get('active_model') and self._context.get('active_model') == 'kits.generate.payment.link.wizard':
            ctx = self._context.copy()
            ctx.update({'order_id':self.res_id})
            self.env.context = ctx
        if self._context.get('cart_recovery') and self._context.get('next_execution_date'):
            order_id = self.env[self._context.get('default_model')].search([('id','=',self._context.get('default_res_id'))])
            order_id.write({'next_execution_date':self._context.get('next_execution_date')})
        self._action_send_mail()
        if self._context.get('active_model') == 'mail.template':
            mail_context=self._context.copy()
            partner_ids = self.partner_ids.filtered(lambda x: x.mailgun_verification_status == 'approved' and x.email).ids
            none_mails_partner_ids = self.partner_ids.filtered(lambda x: not x.email).ids
            message = 'Out of %s customer %s customer is eligible for mail.'%(len(self.partner_ids),len(partner_ids))
            mail_context.update({
                    'none_mails_partner_ids':none_mails_partner_ids,
                    'email_partner_ids':self.partner_ids.ids,
                    'wiz_message':message, 
                    'verify_partner_ids':partner_ids,
            })
            mail_context.update({ 
                    'default_partner_ids':partner_ids,
                    'default_none_mails_partner_ids':none_mails_partner_ids,
                    'default_email_partner_ids':self.partner_ids.ids,
                    'default_message':message,
                    'raise_campaign':True,
                    'campaign' : True,
                })
            return {
                        'name': _('Mailgun Verification'),   
                        'type': 'ir.actions.act_window',
                        'res_model': "mass.mailing.message.wizard",
                        'view_type': 'form',
                        'view_mode': 'form',
                        'target': 'new',
                        'context':mail_context,
                    }
        if self._context.get('active_model') == 'mass.mailing.message.wizard':
            mail_context=self._context.copy()
            mail_context.update({
                        'default_partner_ids':self._context.get('verify_partner_ids'),
                        'default_none_mails_partner_ids':self._context.get('none_mails_partner_ids'),
                        'default_email_partner_ids':self._context.get('email_partner_ids'),
                        'default_message': self._context.get('wiz_message'),
                        'raise_campaign':True,
                        'campaign' : True,
                    })
            return {
                    'name': _('Mailgun Verification'),   
                    'type': 'ir.actions.act_window',
                    'res_model': "mass.mailing.message.wizard",
                    'view_type': 'form',
                    'view_mode': 'form',
                    'target': 'new',
                    'context':mail_context,
                }
        if self._context.get('raise_campaign'):
            form_view = self.env.ref('tzc_sales_customization_spt.marketing_campaing_form_view')
            campaign_id = self._context.get('campaign_id') if self._context.get('campaign_id') else self.env['marketing.campaign']
            return{
                'name': ('Campaign'),
                'res_model': 'marketing.campaign',
                'type': 'ir.actions.act_window',
                'views': [(form_view.id, 'form')],
                'res_id': campaign_id,
                'target': 'current',
            }
        else:
            return {'type': 'ir.actions.act_window_close', 'infos': 'mail_sent'}

    def _action_send_mail(self,auto_commit=False):
        if not self._context.get('campaign'):
            ctx = self.env.context.copy()
            if self.env.context.get('user_bulk_mail'):
                if self._context.get('raise_campaign'):
                    ctx.update({'active_model':'res.partner','active_ids':self.env['res.partner'].browse(self.env.context.get('active_ids')).mapped('id')})
                else:
                    ctx.update({'active_model':'res.partner','active_ids':self.env['res.users'].browse(self.env.context.get('active_ids')).mapped('partner_id').ids})
                self.env.context = ctx
            notif_layout = self._context.get('default_email_layout_xmlid')
            model_description = self._context.get('model_description')
            result_mails_su, result_messages = self.env['mail.mail'].sudo(), self.env['mail.message']
            for wizard in self:
                if wizard.attachment_ids and wizard.composition_mode != 'mass_mail' and wizard.template_id:
                    new_attachment_ids = []
                    for attachment in wizard.attachment_ids:
                        if attachment in wizard.template_id.attachment_ids:
                            new_attachment_ids.append(attachment.copy({'res_model': 'mail.compose.message', 'res_id': wizard.id}).id)
                        else:
                            new_attachment_ids.append(attachment.id)
                    new_attachment_ids.reverse()
                    wizard.write({'attachment_ids': [Command.set(new_attachment_ids)]})

                mass_mode = wizard.composition_mode in ('mass_mail', 'mass_post')

                # Mail = self.env['mail.mail']
                ActiveModel = self.env[wizard.model] if wizard.model and hasattr(self.env[wizard.model], 'message_post') else self.env['mail.thread']
                if wizard.composition_mode == 'mass_post':
                    ActiveModel = ActiveModel.with_context(mail_notify_force_send=False, mail_create_nosubscribe=True)
                if mass_mode and wizard.use_active_domain and wizard.model:
                    res_ids = self.env[wizard.model].search(ast.literal_eval(wizard.active_domain)).ids
                elif mass_mode and wizard.model and self._context.get('active_ids'):
                    res_ids = self._context['active_ids']
                else:
                    res_ids = [wizard.res_id]

                batch_size = int(self.env['ir.config_parameter'].sudo().get_param('mail.batch_size')) or self._batch_size
                sliced_res_ids = [res_ids[i:i + batch_size] for i in range(0, len(res_ids), batch_size)]

                if wizard.composition_mode == 'mass_mail' or wizard.is_log or (wizard.composition_mode == 'mass_post' and not wizard.notify):  # log a note: subtype is False
                    subtype_id = False
                elif wizard.subtype_id:
                    subtype_id = wizard.subtype_id.id
                else:
                    subtype_id = self.env['ir.model.data']._xmlid_to_res_id('mail.mt_comment')

                for res_ids in sliced_res_ids:
                    batch_mails_sudo = self.env['mail.mail'].sudo()
                    all_mail_values = wizard.get_mail_values(res_ids)
                    if self.composition_mode == 'mass_mail' and all_mail_values:
                        for values in all_mail_values:
                            email_list = [self.env.company.catchall_email]
                            if all_mail_values[values] and all_mail_values[values].get('email_from'):
                                if '<' in all_mail_values[values].get('email_from') or '>' in all_mail_values[values].get('email_from'):
                                    email_from_val = all_mail_values[values].get('email_from').split('<')[1].replace('>','')
                                    email_list.append(email_from_val)
                            all_mail_values[values]['reply_to'] = ','.join(email_list)
                    for res_id, mail_values in all_mail_values.items():
                        if type(all_mail_values[int(res_id)].get('body_html')) == bytes:
                            if all_mail_values[int(res_id)].get('body_html') and "{kits_recipient_name}" in all_mail_values[int(res_id)]['body_html'].decode('utf-8'):
                                partner_id = self.env['res.partner'].search([('email','=',mail_values.get('email_to'))])
                                body_html = all_mail_values[int(res_id)]['body_html'].decode('utf-8').replace("{kits_recipient_name}",partner_id.name if partner_id else '')
                                all_mail_values[int(res_id)]['body_html'] = bytes(body_html,'utf-8')
                        elif type(all_mail_values[int(res_id)].get('body_html')) == str:
                            if all_mail_values[int(res_id)].get('body_html') and "{kits_recipient_name}" in all_mail_values[int(res_id)]['body_html'].encode('utf-8').decode('utf-8'):
                                partner_id = self.env['res.partner'].search([('email','=',mail_values.get('email_to'))])
                                body_html = all_mail_values[int(res_id)]['body_html'].encode('utf-8').decode('utf-8').replace("{kits_recipient_name}",partner_id.name if partner_id else '')
                                all_mail_values[int(res_id)]['body_html'] = bytes(body_html,'utf-8')

                        if self._context.get('raise_campaign') and self.model in ['res.partner','res.users'] and mail_values.get('email_from'):
                            mail_values['reply_to'] = mail_values.get('email_from')

                        if wizard.composition_mode == 'mass_mail':
                            batch_mails_sudo |= batch_mails_sudo.create(mail_values)
                        else:
                            post_params = dict(
                                subtype_id=subtype_id,
                                email_layout_xmlid=notif_layout or wizard.email_layout_xmlid,
                                email_add_signature=not bool(wizard.template_id) and wizard.email_add_signature,
                                mail_auto_delete=wizard.template_id.auto_delete if wizard.template_id else self._context.get('mail_auto_delete', True),
                                model_description=model_description)
                            post_params.update(mail_values)
                            if ActiveModel._name == 'mail.thread':
                                if wizard.model:
                                    post_params['model'] = wizard.model
                                    post_params['res_id'] = res_id
                                if not ActiveModel.message_notify(**post_params):
                                    # if message_notify returns an empty record set, no recipients where found.
                                    raise UserError(_("No recipient found."))
                            else:
                                email_list = [self.env.company.catchall_email]
                                if self.template_id.reply_to and (self._context.get('active_id') or self._context.get('default_res_id')) and (self._context.get('active_model') or self._context.get('default_model')):
                                    order_id = self.env[self._context.get('active_model') or self._context.get('default_model')].browse(self._context.get('active_id') or self._context.get('default_res_id'))
                                    if order_id and (self._context.get('active_model') or self._context.get('default_model')) == 'account.move':
                                        email_list.append(order_id.invoice_user_id.email)
                                    if order_id and (self._context.get('active_model') or self._context.get('default_model')) == 'sale.order':
                                        email_list.append(order_id.user_id.email)
                                post_params['reply_to'] = ','.join(email_list)
                                # ActiveModel.browse(res_id).with_context(res_id=res_id).message_post(**post_params)
                                result_messages += ActiveModel.browse(res_id).with_context(res_id=res_id).message_post(**post_params)
                    
                    result_mails_su += batch_mails_sudo
                    if wizard.composition_mode == 'mass_mail':
                        # if self._context.get('create_log'):
                        #     mail_server_id = eval(self.env['ir.config_parameter'].sudo().get_param('mass_mailing.mail_server_id'))
                        #     server_id = self.env['ir.mail_server'].search([('id','=',mail_server_id)]) if mail_server_id else False
                        #     try:
                        #         smtp_session = self.env['ir.mail_server'].connect(mail_server_id=server_id)
                        #     except:
                        #         for mail in batch_mails:
                        #             rec_vals = {
                        #                 'date':mail.date,
                        #                 'email_to':mail.email_to,
                        #                 'email_from':mail.email_from,
                        #                 'message_id':mail.message_id,
                        #                 'subject':mail.subject,
                        #                 'body':mail.body_html,
                        #                 'reply_to':mail.reply_to,
                        #                 'failed':datetime.now(),
                        #                 'state':'fail',
                        #                 }
                        #             log_id = self.env['mailgun.email.logs'].create(rec_vals)
                        batch_mails_sudo.send(auto_commit=auto_commit)
            return result_mails_su, result_messages
        else:
            campaign_obj = self.env['marketing.campaign']
            mailing_obj = self.env['mailing.mailing']
            utm_campaign_obj = self.env['utm.campaign']
            activity_obj = self.env['marketing.activity']
            stage_id = self.env.ref('utm.default_utm_stage').id
            mail_server_id = self.env['ir.mail_server'].search([])
            partner_ids = self.partner_ids.ids if self.composition_mode == 'comment' and self.partner_ids else False

            if self._context.get('default_partner_to'):
                partner_ids = [int(i) for i in self._context.get('default_partner_to').split(',') if self._context.get('default_partner_to')]
            if self._context.get('active_model') == 'mail.template':
                partner_ids = self.partner_ids.filtered(lambda x: x.mailgun_verification_status == 'approved' and x.email).ids
            if partner_ids:
                for partner in partner_ids:
                    partner_id = self.env['res.partner'].search([('id','=',partner)])
                    mailing_contact_id = self.env['mailing.contact'].search([('email','=',partner_id.email)])
                    if not mailing_contact_id:
                        self.env['mailing.contact'].with_context(partner_id=partner_id).action_sync_contacts()



            model_id = self.env.ref('base.model_res_partner').id
            name = self.campaign_name
            # if self._context.get('active_model') and self._context.get('active_model') == 'res.partner':
            #     name = self.subject
            # elif self._context.get('active_model') and self._context.get('active_model') == 'res.users':
            #     name = self.subject

            utm_campaign_id = utm_campaign_obj.create({
                'name': 'UTM Campaign.',
                'stage_id': stage_id,
                'user_id': self.env.uid ,
            })

            campaign_id = campaign_obj.create({
                'model_id':model_id,
                'stage_id':stage_id,
                'utm_campaign_id':utm_campaign_id.id,
                'user_id':self.env.uid ,
                'domain': [('id','in',partner_ids)],
                'name': name,
                'is_custome_rec':True,
                })
            
            mailing_id = mailing_obj.create({
                # 'email_from':self.env['mail.message']._get_default_from(),
                'email_from':self.email_from,
                'mailing_type':'mail',
                'reply_to_mode':'new',
                'state':'done',
                'reply_to':self.email_from,
                # 'reply_to':self.env['mail.message']._get_default_from(),
                'subject':self.subject,
                'keep_archives':False,
                'campaign_id':utm_campaign_id.id,
                'mailing_model_id':model_id,
                'use_in_marketing_automation':False,
                'body_html':self.body,
                'mail_server_id':mail_server_id[0].id if mail_server_id else False,
                'attachment_ids':[(6,0,self.attachment_ids.ids)]
            })

            activity_id = activity_obj.create({
                'name':self.subject,
                'activity_type':'email',
                'campaign_id':campaign_id.id,
                'interval_type':'hours',
                'interval_number':0,
                'trigger_type':'begin',
                'validity_duration':False,
                'mass_mailing_id':mailing_id.id,
            })
 
            if self._context.get('campaign'):
                ctx = self._context.copy()
                ctx.update({'campaign_id':campaign_id.id})
                # ctx.update({'not_create_log':True})
                del ctx['campaign']
                if self._context.get('resend'):
                    del ctx['default_res_id']
                self.env.context = ctx

            campaign_id.action_start_campaign()
            campaign_id.sync_participants()
            campaign_id.execute_activities()
            campaign_id.execution_datetime = datetime.now()
            campaign_id.count_sent = len(partner_ids) if partner_ids else 0
            campaign_id.action_stop_campaign()

    def save_as_template(self):
        """ hit save as template button: current form value will be a new
            template attached to the current document. """
        for record in self:
            model = self.env['ir.model']._get(record.model or 'mail.message')
            model_name = model.name or ''
            template_name = "%s: %s" % (model_name, tools.ustr(record.subject))
            values = {
                'name': template_name,
                'subject': record.subject or False,
                'body_html': record.body or False,
                'model_id': model.id or False,
                'attachment_ids': [(6, 0, [att.id for att in record.attachment_ids])],
                'partner_to':'${object.id}',
            }
            template = self.env['mail.template'].create(values)
            # generate the saved template
            record.write({'template_id': template.id})
            record.onchange_template_id_wrapper()
            return _reopen(self, record.id, record.model, context=self._context)

    @api.model
    def get_record_data(self, values):
        """ Returns a defaults-like dict with initial values for the composition
        wizard when sending an email related a previous email (parent_id) or
        a document (model, res_id). This is based on previously computed default
        values. """
        result, subject = {}, False
        if values.get('parent_id'):
            parent = self.env['mail.message'].browse(values.get('parent_id'))
            result['record_name'] = parent.record_name,
            subject = tools.ustr(parent.subject or parent.record_name or '')
            if not values.get('model'):
                result['model'] = parent.model
            if not values.get('res_id'):
                result['res_id'] = parent.res_id
            partner_ids = values.get('partner_ids', list()) + parent.partner_ids.ids
            result['partner_ids'] = partner_ids
        elif values.get('model') and values.get('res_id'):
            doc_name_get = self.env[values.get('model')].browse(values.get('res_id')).name_get()
            result['record_name'] = doc_name_get and doc_name_get[0][1] or ''
            subject = tools.ustr(result['record_name'])

        re_prefix = _('Re:')
        if subject and not (subject.startswith('Re:') or subject.startswith(re_prefix)):
            subject = "%s %s" % (re_prefix, subject)
        
        if self._context.get('resend') or self._context.get('raise_campaign') or self._context.get('campaign'):
            subject = self._context.get('subject')
        result['subject'] = subject

        return result
