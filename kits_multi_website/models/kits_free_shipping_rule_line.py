from odoo import api, fields, models, _
from odoo.exceptions import UserError
class kits_free_shipping_rule_line(models.Model):
    _name = 'kits.free.shipping.rule.line'
    _description = "Kits Free Shipping Rule"

    name = fields.Char("Name",default="Free Shipping")
    amount_from = fields.Float('From Porduct USD Price')
    amount_to = fields.Float('To Porduct USD Price')
    amount = fields.Float('Amount(USD)')
    shipping_rule_id  = fields.Many2one('kits.free.shipping.rule','Shipping Rule')

    @api.onchange('amount_to','shipping_rule_id','amount_from')
    def _onchange_amount(self):
        for record in self:
            if record.shipping_rule_id:
                shipping_rule_ids = self.search([('shipping_rule_id','=',record.shipping_rule_id.id.origin),('id','!=',record.id.origin)])
                min_amount =  min(shipping_rule_ids.mapped('amount_from')) if shipping_rule_ids else 0
                max_amount = max(shipping_rule_ids.mapped('amount_to')) if shipping_rule_ids else 0
                if record.amount_from and record.amount_to and record.amount_from >= record.amount_to:
                    raise UserError(_("Start amount bigger then ending amount."))
                if (record.amount_from and min_amount<= record.amount_from <= max_amount) or (record.amount_to and min_amount <= record.amount_to <= max_amount):
                    raise UserError(_("This amount already applied"))
