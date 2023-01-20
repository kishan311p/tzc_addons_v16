from odoo import _, api, fields, models, tools

class ir_model(models.Model):
    _inherit = "ir.model"

    def _updated_data_validation(self,fields,data,model):
        updated_fields = []
        update = False
        for value in data.keys():
            if value in fields:
                if model == 'sale.order' and not self._context.get('cron') and not self._context.get('on_consign_wizard') or self._context.get('active_model') == 'sale.barcode.order.spt':
                    updated_fields.append(value)
                if model == 'stock.picking' and not self._context.get('custom'):
                    updated_fields.append(value)
                if model == 'account.move' or model == 'res.partner':
                    updated_fields.append(value)
            elif self._context.get('params') and self._context.get('params').get('model') == 'sale.order' and self._context.get('active_model') == 'sale.barcode.order.spt':
                updated_fields.append(value)

        if updated_fields:
            update = True
        
        return update
