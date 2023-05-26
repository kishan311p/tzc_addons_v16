# -*- coding: utf-8 -*-
# Part of SnepTech See LICENSE file for full copyright and licensing details.##
##############################################################################
from odoo import models, fields, api, _


class eto_partner_wizard_spt(models.TransientModel):
    _name = 'eto.partner.wizard.spt'
    _description = 'Set eto In Partner'

    property_product_eto = fields.Selection([('b2c','Pending'),('b2b_regular','Verified')],default="b2c",tracking=True,string='ETO')
    
    partner_ids = fields.Many2many('res.partner','eto_partner_wizard_res_partner_real','wizard_id','partner_id',string='Partner')
    
    def action_process(self):
        for partner in self.partner_ids:
            partner.customer_type = self.property_product_eto