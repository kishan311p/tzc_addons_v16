from odoo import _, api, fields, models, tools

class kits_generate_payment_link_wizard(models.TransientModel):
    _name = "kits.generate.payment.link.wizard"
    _description = "Kits Generate a Payment Link"
    _rec_name = "sale_order_id"

    kits_payment_link = fields.Char('Link')
    sale_order_id = fields.Many2one('sale.order','Order')

    def action_send_payment_link(self):
        return self.sale_order_id.send_payment_link_mail()
