from odoo import _, api, fields, models

class crm_lead(models.Model):
    _inherit = 'crm.lead'
    
    
    def notify_to_manager_crm_lead(self):
        user_ids = eval(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.to_notify_user_ids', default='[]'))
        users = self.env['res.users'].browse(user_ids)
        partner_ids = users.mapped('partner_id')
        for record in self:
            self.env.ref('tzc_sales_customization_spt.tzc_order_lead_generation_notification_to_salesperson').sudo().with_context(lang= 'en_US').send_mail(res_id=record.id,force_send=True,email_values={'recipient_ids':[(6,0,partner_ids.ids)]})
        return {}