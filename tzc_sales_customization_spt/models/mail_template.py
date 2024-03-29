from odoo import api,fields,models,_

class mail_template(models.Model):
    _inherit = "mail.template"

    def send_mail(self, res_id, force_send=False, raise_exception=False, email_values=None, email_layout_xmlid=False):
        if email_values is None:
            email_values = {}
        email_list = [self.env.company.catchall_email]
        if self.model =='stock.picking' and not self._context.get('salesperson_notify'):
            picking_id = self.env['stock.picking'].browse(res_id)
            verified = picking_id.sale_id.partner_verification() if picking_id.sale_id.partner_id.user_ids else False
            if not verified:
                res_id = None
                force_send= False
                return False
            else:
                if picking_id:
                    email_list.append(picking_id.sale_id.user_id.email) if picking_id else None
                email_values['reply_to'] = ','.join(email_list)        
                return super(mail_template,self).send_mail(res_id, force_send, raise_exception, email_values, email_layout_xmlid)
        if self._context.get('active_model') and self._context.get('active_id'):
            catalog_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
            if catalog_id and self._context.get('active_model') in ['sale.catalog','sale.order']:
                email_list.append(catalog_id.user_id.email) if catalog_id.user_id.email else None
        if self._context.get('abandoned_server') and self._context.get('record_id'):
            order_id = self._context.get('record_id')
            email_list.append(order_id.user_id.email) if order_id.user_id.email else None
        email_values['reply_to'] = ','.join(email_list)
        user_related_mail_temp_ids = [self.env.ref('portal.mail_template_data_portal_welcome').id,
                                      self.env.ref('auth_signup.reset_password_email').id,
                                      self.env.ref('kits_b2b_website.mail_template_user_signup_confirmation').id,
                                      self.env.ref('tzc_sales_customization_spt.tzc_mail_template_customer_approve_notify_spt').id,
                                      self.env.ref('tzc_sales_customization_spt.tzc_mail_template_customer_approve_spt').id
                                      ]
        if self.id in user_related_mail_temp_ids:
            ctx = self._context.copy()
            ctx.update({'user_template':True})
            self.env.context = ctx
        return super(mail_template,self).send_mail(res_id, force_send, raise_exception, email_values, email_layout_xmlid)

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
