# -*- coding: utf-8 -*-
# Part of SnepTech See LICENSE file for full copyright and licensing details.##
##############################################################################
from odoo import models, fields, api, _
from odoo.exceptions import AccessDenied, AccessError, UserError, ValidationError
from odoo.exceptions import UserError
class portal_wizard(models.TransientModel):
    _inherit = 'portal.wizard'


    def _default_user_ids(self):
        # for each partner, determine corresponding portal.wizard.user records
        partner_ids = self.env.context.get('active_ids', [])
        contact_ids = set()
        user_changes = []
        portal_users = ''
        for partner in self.env['res.partner'].sudo().browse(partner_ids):
            contact_partners = partner.child_ids.filtered(lambda p: p.type in ('contact', 'other')) | partner
            for contact in contact_partners:
                # make sure that each contact appears at most once in the list
                if contact.id not in contact_ids:
                    contact_ids.add(contact.id)
                    is_portal = False
                    if contact.user_ids:
                        is_portal = self.env.ref('base.group_portal') in contact.user_ids[0].groups_id
                    user_changes.append((0, 0, {
                        'partner_id': contact.id,
                        'email': contact.email,
                        'is_portal': is_portal,
                    }))
                    if contact.user_ids:
                        portal_users = portal_users + contact.name +'\n'
        if portal_users:
            raise UserError(_("These contacts are alredy user: \n %s")%(portal_users))

        return user_changes
    
    user_ids = fields.One2many('portal.wizard.user', 'wizard_id', string='Users ',default=_default_user_ids)
    set_all_portal = fields.Boolean('Select all')
    

    @api.onchange('set_all_portal')
    def set_all_user_portal(self):
        for record in self:
            for user in record.user_ids:
                user.user_selected = False
                if record.set_all_portal:
                    user.user_selected = True

    def action_apply(self):
        for rec in self:
            ctx = self._context.copy()
            ctx['set_user_spt'] = True
            ctx['from_grant_portal'] = True
            self.env.context = ctx
            for user_id in rec.user_ids.filtered(lambda x: x.user_selected==True):
                user_id.action_grant_access()
                user_id.partner_id.action_verify_email()
                 
        # self._check_one_user_type()
        # ctx = self._context.copy()
        # ctx['set_user_spt'] = True
        # ctx['from_grant_portal'] = True
        # self.env.context = ctx
        # self.ensure_one()
        # self.user_ids.action_apply()
        # self.user_ids.partner_id.action_verify_email()
        # return {'type': 'ir.actions.act_window_close'}
        # res = super(portal_wizard,self).action_apply()
        # return res

    def _check_one_user_type(self):
        """We check that no users are both portal and users (same with public).
           This could typically happen because of implied groups.
        """
        users = ''
        for user in self.user_ids:
            if user.partner_id.user_ids:
                users = users + user.partner_id.name +'\n'
        if users:
            raise ValidationError(_('These contacts are alredy user: \n %s' % (users)))

