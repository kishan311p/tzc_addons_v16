from odoo import models,fields

class kits_multi_website_prescription_line(models.Model):
    _name = 'kits.multi.website.prescription.line'
    _description = 'Prescription Eye Data'
    _rec_name = 'eye_name_id'

    eye_name_id = fields.Many2one('kits.eye.data.name','Eye')
    left_eye = fields.Char('Left Eye')
    right_eye = fields.Char('Right Eye')
    prescription_id = fields.Many2one('kits.multi.website.prescription','Prescription')


class kits_eye_data_name(models.Model):
    _name = 'kits.eye.data.name'
    _description = "Eye Name"

    name = fields.Char('Name')