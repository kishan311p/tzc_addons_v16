from odoo import models, fields, api, _

class res_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    
    import_url = fields.Char('Import Url',config_parameter="tzc_product_import_spt.import_url",default="")
    