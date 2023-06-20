from odoo import api, fields, models, _
from lxml import etree

class kits_multi_website_wallet_transaction(models.Model):
    _name = "kits.multi.website.wallet.transaction"
    _description = "Kits Multi Website Wallet Transaction"
    _rec_name = 'customer_id'

    return_request_id = fields.Many2one("kits.multi.website.return.request","Return Request")
    sale_order_id = fields.Many2one("kits.multi.website.sale.order", "Sale Order")
    amount = fields.Float("Amount ")
    customer_id = fields.Many2one("kits.multi.website.customer","Customer")
    refund_date = fields.Datetime("Refund Date")
    invoice_id = fields.Many2one("kits.multi.website.invoice","Invoice")
    website_id = fields.Many2one("kits.b2c.website","Website")
    description = fields.Text('Description')

    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_wallet_transaction, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res
        
