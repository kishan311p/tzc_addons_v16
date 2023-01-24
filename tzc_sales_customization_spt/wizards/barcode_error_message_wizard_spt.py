# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class barcode_error_message_wizard_spt(models.TransientModel):
    _name = "barcode.error.message.wizard.spt"
    _description = "Barcode Error Message"

    name = fields.Char('Message')
    move_id = fields.Many2one('stock.move','Move')
    picking_id = fields.Many2one('stock.picking','Picking')
    qty = fields.Float('Qty')

    def action_process(self):
        pass