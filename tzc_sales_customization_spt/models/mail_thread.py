from odoo import models,fields,api,_

class mail_thread(models.AbstractModel):
    _inherit = "mail.thread"

    def _message_track(self, tracked_fields, initial_values):
        user_obj = self.env['res.users'].sudo()
        if self._name == 'res.partner' and self.env.user.has_group('tzc_sales_customization_spt.group_sales_manager_spt'):
            setting_admins = user_obj.browse(eval(self.env['ir.config_parameter'].sudo().get_param('user_ids_spt','[]')))
            recipients = setting_admins.mapped('partner_id')
            for record in self:
                data = record._mail_track(self.fields_get(tracked_fields), initial_values[record.id])
                if 'email' in data[0] and recipients:
                    for recipient in recipients:
                        self.with_context(recipient=recipient.name).env.ref('tzc_sales_customization_spt.partner_email_change_notify_admin_mail_template').sudo().send_mail(record.id,force_send=True,email_values={'recipient_ids':[(6,0,recipient.ids)]},email_layout_xmlid="mail.mail_notification_light")
        if self._name == 'res.users':
            for rec in self:
                if 'contact_allowed_countries' in initial_values[rec.id] or 'country_ids' in initial_values[self.id]:
                    rec._mail_track(self.fields_get(tracked_fields), initial_values[rec.id])
        res = super(mail_thread,self)._message_track(tracked_fields,initial_values)
        return res
    
