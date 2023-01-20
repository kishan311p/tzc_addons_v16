from odoo import api, fields, models, _

class stock_move(models.Model):
    _inherit = "stock.move"

    sale_order_id = fields.Many2one("kits.multi.website.sale.order", "Sale Order")
    sale_order_line_id = fields.Many2one("kits.multi.website.sale.order.line", "Sale Order")
    website_id = fields.Many2one("kits.b2c.website","Website")

    @api.model
    def default_get(self, fields):
        res = super(stock_move, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res
