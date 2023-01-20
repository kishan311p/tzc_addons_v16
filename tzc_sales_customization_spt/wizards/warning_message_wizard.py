from odoo import _, api, fields, models, tools

class warning_message_wizard(models.TransientModel):
    _name = 'kits.warning.message.wizard'
    _description = 'Warning Message Wizard'

    message = fields.Char()
    partner_ids = fields.Many2many('res.partner','wraning_wizard_res_partner_rel','partner_id','wizard_id','Contacts')
    selected_id = fields.Many2one('res.partner','Contact')

    def action_archive_contact(self):
        # deleted_data = False
        allow_contact_for_delete = []
        if self.partner_ids:
            return {
                    'name':_("Contact Delete"),
                    'view_mode': 'form',
                    'view_type': 'form',
                    'res_model': 'kits.assign.salesperson.wizard',
                    'type': 'ir.actions.act_window',
                    'target': 'new',
                    'context' : {
                        'default_partner_id' : self.selected_id.id,
                        'default_partner_ids' : [(6,0,self.partner_ids.ids)],
                        'default_hide_button':True,
                        'total_count':len(self),
                        'default_message':'The selected contact is assigned in contact as a salesperson, Please change below contacts salesperson.'
                    }
                }
        else:
            allow_contact_for_delete.append(self.selected_id.id)
            # deleted_data = self.selected_id.delete_contact()
    
        if allow_contact_for_delete:
            message = (f'Out of {self.env.context.get("total_count")} contacts {len(allow_contact_for_delete)} will be deleted.')
            # message = (f'Out of {self.env.context.get("total_count")} contacts {deleted_data[2]} is deleted and following {deleted_data[1]} is archived')
            return {
                    'name':_('Delete Contact'),
                    'type':'ir.actions.act_window',
                    'res_model':'kits.confirm.contact.delete.wizard',
                    'view_mode':'form',
                    'context':{'default_partner_ids':[(6,0,allow_contact_for_delete)],'default_message':message},
                    'target':'new',
                }
