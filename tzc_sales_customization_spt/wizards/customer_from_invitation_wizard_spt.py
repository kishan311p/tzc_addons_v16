# -*- coding: utf-8 -*-
# Part of SnepTech See LICENSE file for full copyright and licensing details.##
##############################################################################
from odoo import models, fields, api, _


class customer_from_invitation_wizard_spt(models.TransientModel):
    _name = 'customer.from.invitation.wizard.spt'
    _description = 'Customer Invitation'

    # invitation = fields.Boolean('Invitation Accepted')
    user_id = fields.Many2one('res.users',string='User',default=lambda self: self.env.user)
    invitation = fields.Selection([('both','Both (Accepted/Not Confirmed)'),('accepted','Accepted'),('reject','Not Confirmed')],default='both')
    
    def action_process(self):
        list_view = self.env.ref('base.view_partner_tree')
        form_view = self.env.ref('base.view_partner_form')
        partner_obj = self.env['res.partner']
        user_obj = self.env['res.users']
        for record in self:
            domain= [('share','=',True)]
            if record.invitation == 'reject':
                domain.append(('state','=','new'))
            elif record.invitation == 'accepted':
                domain.append(('state','=','active'))
            elif record.invitation == 'both':
                domain.append(('state','in',['new','active']))
            user_partner_ids = user_obj.search(domain).mapped('partner_id')
            # user_partner_ids = user_obj.search([('share','=',True),('state','=','new' if not record.invitation else 'active')]).mapped('partner_id')
            partner_ids = partner_obj.search([('id','in',user_partner_ids.ids),('user_id','=',record.user_id.id)])
            return {
                'name': 'Signup Customers',
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'res.partner',
                'view_id': False,
                'views': [(list_view.id, 'tree'),(form_view.id, 'form')],
                'type': 'ir.actions.act_window',
                'target':'current',
                'domain':[('id','in',partner_ids.ids)],
            }
