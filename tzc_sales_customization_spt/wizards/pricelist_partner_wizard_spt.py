# -*- coding: utf-8 -*-
# Part of SnepTech See LICENSE file for full copyright and licensing details.##
##############################################################################
from odoo import models, fields, api, _


class pricelist_partner_wizard_spt(models.TransientModel):
    _name = 'pricelist.partner.wizard.spt'
    _description = 'Set Pricelist In Partner'

    property_product_pricelist = fields.Many2one(
        'product.pricelist', ' Pricelist ')
    
    partner_ids = fields.Many2many('res.partner','pricelist_partner_wizard_res_partner_real','wizard_id','partner_id',string='Partner')
    
    def action_process(self):
        for partner in self.partner_ids:
            partner.property_product_pricelist = self.property_product_pricelist.id
