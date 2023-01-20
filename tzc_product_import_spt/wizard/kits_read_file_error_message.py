from odoo import _, api, fields, models, tools

class kits_read_file_error_message(models.TransientModel):
    _name = "kits.read.file.error.message"
    _description = 'Product Import Error Message'

    product_import_id = fields.Many2one("product.import.spt")

    def action_process(self):
        if self._context.get('action_process') == 'read_opration_process':
          res =  self.product_import_id.read_opration_process()

        if self._context.get('action_process') == 'action_update_product':
            res = self.product_import_id.action_update_product()
        
        if self._context.get('action_process') == 'all_in_one_spt_update':
            res = self.product_import_id.all_in_one_spt_update()
        
        if self._context.get('action_process') == 'all_in_one_spt_create':
            res = self.product_import_id.all_in_one_spt_create()

        if self._context.get('action_process') == 'action_delete_product_process':
            res = self.product_import_id.action_delete_product_process()
            
        return res 
