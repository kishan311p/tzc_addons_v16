from odoo import models,fields,api,_

class crm_lead(models.Model):
    _inherit = 'crm.lead'

    @api.model_create_multi
    def create(self,vals_list):
        res = super(crm_lead,self).create(vals_list)
        user_ids = eval(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.to_notify_user_ids', default='[]'))
        users = self.env['res.users'].browse(user_ids)
        partner_ids = users.mapped('partner_id')
        if partner_ids:
            self.env.ref('tzc_sales_customization_spt.tzc_order_lead_generation_notification_to_salesperson').sudo().send_mail(res_id=res.id,force_send=True,email_values={'recipient_ids':[(6,0,partner_ids.ids)]})
        return res
