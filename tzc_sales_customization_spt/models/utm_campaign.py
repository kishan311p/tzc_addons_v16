from odoo import api,_,api,fields,models

class utm_campaign(models.Model):
    _inherit = 'utm.campaign'

    def _filter_mailing(self):
        for rec in self:
            if self.env.user.has_group('base.group_system'):
                return [(1,'=',1)]
            else:
                partner_model = self.env.ref('base.model_res_partner')
                partner_obj = self.env['res.partner']
                partner_access_ids = self.env.user.get_filtere_contact()
                mailing_ids = []
                mailing_mail_ids = self.env['mailing.mailing'].search([('campaign_id','=',rec.id),('mailing_model_id','=',partner_model.id)])
                for mail_id in mailing_mail_ids:
                    partner_ids = partner_obj.search(eval(mail_id.mailing_domain))
                    if set(partner_ids.ids) & set(partner_access_ids.ids):
                        mailing_ids.append(mail_id.id)
                return [('id','in',mailing_ids)]
    mailing_mail_ids = fields.One2many(
    'mailing.mailing', 'campaign_id',
    domain=_filter_mailing,
    # domain=[('mailing_type', '=', 'mail')],
    string='Mass Mailings',
    groups="mass_mailing.group_mass_mailing_user")


    def action_view_utm_campaign(self):
        partner_model = self.env.ref('base.model_res_partner')
        campaign_ids=[]
        partner_obj = self.env['res.partner']
        if self.env.user.has_group('base.group_system'):
            # If current user is admin then all records will be shown.
            query = 'select id from utm_campaign'
            self.env.cr.execute(query)
            record_data = self.env.cr.fetchall()
            campaign_ids = list(map(lambda x: x[0], record_data))
        else:
            utm_campaigns = self.env['utm.campaign'].search([])
            # Getting all partner ids whose access have current user.
            partner_access_ids = self.env.user.get_filtere_contact()
            for campaign_id in utm_campaigns:
                mailing_mail_ids = self.env['mailing.mailing'].search([('campaign_id','=',campaign_id.id)])
                if mailing_mail_ids:
                    for mailing_id in mailing_mail_ids.filtered(lambda x : x.mailing_model_id.id==partner_model.id):
                        partner_ids = partner_obj.search(eval(mailing_id.mailing_domain))
                        # Checking if partner is there
                        if set(partner_ids.ids) & set(partner_access_ids.ids):
                            campaign_ids.append(campaign_id.id)
                else:
                    # Adding campaign if responsible is current user and no mailing_mail is there.
                    if campaign_id.user_id == self.env.user:
                        campaign_ids.append(campaign_id.id)
        
        return{
            'name': ('Campaigns'),
            'res_model': 'utm.campaign',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('utm.utm_campaign_view_kanban').id, 'kanban'),
                      (self.env.ref('utm.utm_campaign_view_form').id, 'form'),
                      (self.env.ref('utm.utm_campaign_view_tree').id, 'tree'),
                      ],
            'domain':[('is_auto_campaign', '=', False),('id','in',campaign_ids)],  
            'target': 'current',
        }
