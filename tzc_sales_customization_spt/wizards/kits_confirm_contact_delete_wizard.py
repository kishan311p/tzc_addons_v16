from odoo import models,fields,api,_


class kits_confirm_contact_delete_wizard(models.TransientModel):
    _name = 'kits.confirm.contact.delete.wizard'
    _description = 'Confirm Contact Delete Wizard'

    partner_ids = fields.Many2many('res.partner','kits_confirm_delete_wizard_res_partner_rel','kits_confirm_contact_delete_wiz_id','res_partner_id','Partners')
    error_partners = fields.Many2many('res.partner','kits_confirm_delete_wizard_error_partner_rel','kits_confirm_contact_delete_id','res_partner_id','Partners Not Allowed')
    internal_contacts = fields.Many2many('res.partner','kits_confirm_delete_internal_partner_rel','kits_confirm_contact_delete_id','res_partner_id','Internal Partners')
    order_partners = fields.Many2many('res.partner','kits_confirm_delete_order_partner_rel','kits_confirm_contact_delete_wiz_id','res_partner_id','Order Contacts')
    message = fields.Text('Message')
    user_ids = fields.Many2many('res.users','kits_confirm_delete_wizard_res_users_rel','kits_confirm_user_delete_wiz_id','res_user_id','Users')

    # def action_delete(self):
    #     completely_delete = self._context.get('completely_delete')
    #     user_obj = self.env['res.users'].sudo()
    #     partner_obj = self.env['res.partner'].sudo()
    #     mailing_contact_obj = self.env['mailing.contact'].sudo()
    #     if completely_delete:
    #         mailing_contacts = mailing_contact_obj.search(['|',('email','in',self.partner_ids.mapped('email')),('odoo_contact_id','in',self.partner_ids.ids)])
    #         mailing_contacts.unlink() if mailing_contacts else None
    #     if not completely_delete:
    #         mailing_contacts = mailing_contact_obj.search(['|',('email','in',self.partner_ids.mapped('email')),('odoo_contact_id','in',self.partner_ids.ids)])
    #         mailing_contacts.write({'source':'imported'})
    #     self.sudo().partner_ids.with_context(restrict_delete_rules=True).action_delete_partner() if self.partner_ids else None

    def action_confirm_delete(self):
        for rec in self.partner_ids:
            rec.delete_contact()
