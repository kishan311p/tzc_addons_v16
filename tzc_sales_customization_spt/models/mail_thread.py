from odoo import models, fields, api, _
from bs4 import BeautifulSoup


class mail_thread(models.AbstractModel):
    _inherit = "mail.thread"

    def _message_track(self, tracked_fields, initial_values):
        user_obj = self.env['res.users'].sudo()
        if self._name == 'res.partner' and self.env.user.has_group('tzc_sales_customization_spt.group_sales_manager_spt'):
            setting_admins = user_obj.browse(
                eval(self.env['ir.config_parameter'].sudo().get_param('user_ids_spt', '[]')))
            recipients = setting_admins.mapped('partner_id')
            for record in self:
                data = record._mail_track(self.fields_get(
                    tracked_fields), initial_values[record.id])
                if 'email' in data[0] and recipients:
                    for recipient in recipients:
                        self.with_context(recipient=recipient.name).env.ref('tzc_sales_customization_spt.partner_email_change_notify_admin_mail_template').sudo().send_mail(
                            record.id, force_send=True, email_values={'recipient_ids': [(6, 0, recipient.ids)]}, email_layout_xmlid="mail.mail_notification_light")
        if self._name == 'res.users':
            for rec in self:
                if 'contact_allowed_countries' in initial_values[rec.id] or 'country_ids' in initial_values[self.id]:
                    rec._mail_track(self.fields_get(
                        tracked_fields), initial_values[rec.id])
        if self._name == 'sale.order':
            ctx = self._context.copy()
            ctx.update({'order_id':self})
            self.env.context = ctx
        res = super(mail_thread, self)._message_track(
            tracked_fields, initial_values)
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if not any(k not in ['lang', 'tz', 'uid', 'mail_post_autofollow'] for k in self._context.keys()):
            kwargs.update({'email_layout_xmlid': 'mail.mail_notification_light'})
        return super(mail_thread, self).message_post(**kwargs)

    # def create(self,vals):
    #     ctx = self.env.context.copy()
    #     ctx.update({'mail_create_nosubscribe':True})
    #     self.env.context = ctx

    def _notify_get_recipients(self, message, msg_vals, **kwargs):
        """ Compute recipients to notify based on subtype and followers. This
        method returns data structured as expected for ``_notify_recipients``.

        TDE/XDO TODO: flag rdata directly, with for example r['notif'] = 'ocn_client' and r['needaction']=False
        and correctly override _notify_get_recipients

        Kwargs allow to pass various parameters that are used by sub notification
        methods. See those methods for more details about supported parameters.
        Specific kwargs used in this method:

          * ``skip_existing``: check existing notifications and skip them in order
            to avoid having several notifications / partner as it would make
            constraints crash. This is disabled by default to optimize speed;

        :return list recipients_data: this is a list of recipients information (see
          ``MailFollowers._get_recipient_data()`` for more details) formatted like
          [{'active': partner.active;
            'id': id of the res.partner;
            'groups': res.group IDs if linked to a user;
            'notif': 'inbox', 'email', 'sms' (SMS App);
            'share': partner.partner_share;
            'type': 'customer', 'portal', 'user;'
           }, {...}]
        """
        msg_sudo = message.sudo()
        # get values from msg_vals or from message if msg_vals doen't exists
        pids = msg_vals.get('partner_ids', []) if msg_vals else msg_sudo.partner_ids.ids
        message_type = msg_vals.get('message_type') if msg_vals else msg_sudo.message_type
        subtype_id = msg_vals.get('subtype_id') if msg_vals else msg_sudo.subtype_id.id
        # is it possible to have record but no subtype_id ?
        soup = BeautifulSoup(msg_vals.get('body').encode("utf-8"), "html.parser")
        sub_partner_id = False
        try:
            sub_partner_id = int(soup.a.attrs.get('data-oe-id'))
        except:
            pass
        recipients_data = []

        res = self.env['mail.followers']._get_recipient_data(self, message_type, subtype_id, pids)[self.id if self else 0]
        if not res:
            return recipients_data

        author_id = msg_vals.get('author_id') or message.author_id.id
        for pid, pdata in res.items():
            if pid and pid == author_id and not self.env.context.get('mail_notify_author'):  # do not notify the author of its own messages
                continue
            if pdata['active'] is False:
                continue
            if pdata.get('id') in msg_sudo.partner_ids.ids:
                if not pdata.get('is_follower'):
                    if pdata.get('id') not in msg_sudo.partner_ids.ids:
                        recipients_data.append(pdata)
                else:
                    if pdata.get('id') in msg_sudo.partner_ids.ids:
                        recipients_data.append(pdata)
            if sub_partner_id and pdata.get('id') == sub_partner_id and pdata not in recipients_data:
                recipients_data.append(pdata)

        # avoid double notification (on demand due to additional queries)
        if kwargs.pop('skip_existing', False):
            pids = [r['id'] for r in recipients_data]
            if pids:
                existing_notifications = self.env['mail.notification'].sudo().search([
                    ('res_partner_id', 'in', pids),
                    ('mail_message_id', 'in', message.ids)
                ])
                recipients_data = [
                    r for r in recipients_data
                    if r['id'] not in existing_notifications.res_partner_id.ids
                ]

        return recipients_data
