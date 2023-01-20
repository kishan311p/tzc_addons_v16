from odoo import api, fields, models, _

class kits_file_download_wizard(models.TransientModel):
    _name = "kits.file.download.wizard"
    _description = "Kits File Download Wizard"

    file = fields.Binary('file')