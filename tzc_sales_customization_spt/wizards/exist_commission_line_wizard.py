from odoo import _, api, fields, models, tools


class exist_commission_line_wizard(models.TransientModel):
    _name = 'exist.commission.line.wizard'

    commission_lines_ids = fields.Many2many('kits.commission.lines',readonly=True)
    
