from odoo import fields,models,_
class stock_quant(models.Model):
    _inherit = 'stock.quant'
    
    def _apply_inventory(self):
        res = super(stock_quant, self)._apply_inventory()
        for record in self:
            if self._context.get('kits_update_product_date',False):
                record.product_id.write({
                    'last_qty_update': fields.Datetime.now()
                })
        return res