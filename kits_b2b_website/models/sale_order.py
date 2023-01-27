from odoo import _, api, fields, models

class sale_order(models.Model):
    _inherit = 'sale.order'
    
    b2b_currency_id = fields.Many2one('res.currency', string=' Currency')

    def compute_all(self):
        for record in self:
            record._amount_all()
        return True
    
    def action_confirm(self):
        res = super(sale_order, self).action_confirm()
        for so in self:
            currency_rate = self.env['kits.b2b.multi.currency.mapping'].search([('currency_id','=',so.b2b_currency_id.id)],limit =1).currency_rate
            if currency_rate:
                for sol in so.line_ids:
                    sol.b2b_currency_rate = currency_rate
        return res