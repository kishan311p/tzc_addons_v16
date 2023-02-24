from odoo import models, fields, api, _

class sale_catalog_order_line(models.Model):
    _name = 'sale.catalog.order.line'
    _description = 'Catalog Order Line'
    _order = "product_pro_id"

    catalog_order_id = fields.Many2one('sale.catalog.order', ondelete='cascade', string='Catalog', copy=False)
    product_pro_id = fields.Many2one('product.product', ondelete='cascade', string='Product', required=True)
    product_qty = fields.Float('Qty', digits='Product Unit of Measure', default=1)
    
class sale_catalog_order(models.Model):
    _name = 'sale.catalog.order'
    _description = 'Catalog Order'

    catalog_id = fields.Many2one('sale.catalog', string='catalog')
    state = fields.Selection(selection=[('draft', 'Draft'),('sent', 'Sent'),('pending', 'Pending'),('done', 'Done'),('reject', 'reject'),('cancel', 'Cancel'),], string='Status', required=True, readonly=True, copy=False, default='draft')
    customer_id = fields.Many2one('res.partner')
    accept_decline_flag = fields.Boolean('Accept/Decline Flag')
    decline_description = fields.Text('Decline Description ',states={'reject': [('readonly', False)]})
    line_ids = fields.One2many('sale.catalog.order.line', 'catalog_order_id', states={'draft': [('readonly', False)]},copy=True,string='Catalog Order Lines')
    user_id = fields.Many2one('res.users', string='Responsible', related='catalog_id.user_id', readonly=True,store=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')
