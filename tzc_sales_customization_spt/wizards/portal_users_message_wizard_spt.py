from odoo import models, fields, api, _

class portal_users_message_wizard_spt(models.TransientModel):
    _name = 'portal.users.message.wizard.spt'
    _description = 'Portal User Message Wizard'

    name = fields.Html('Message')
    wizard_id = fields.Many2one('portal.wizard','Portal Wizard')
    partner_ids = fields.Many2many('res.partner', 'portal_users_message_wizard_partner_ral','wizard_id','partner_id', string='partner_id')
    user_details = fields.Char('User Details')

    def action_process(self):
        user_changes = []
        for data in eval(self.user_details):
            if len(data) and data[2]:
                if data[2]['partner_id'] not in self.partner_ids.ids:
                    user_changes.append(data)
        if user_changes:
            return {
                    'name': 'Grant portal access',
                    'view_mode': 'form',
                    'target': 'new',
                    'context':{'default_user_ids':user_changes},
                    'res_model': 'portal.wizard',
                    'type': 'ir.actions.act_window',
                }