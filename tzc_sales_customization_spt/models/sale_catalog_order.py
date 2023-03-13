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
    state = fields.Selection(selection=[('draft', 'Draft'),('sent', 'Sent'),('done', 'Done'),('reject', 'reject'),('cancel', 'Cancel'),], string='Status', required=True, readonly=True, copy=False, default='draft')
    customer_id = fields.Many2one('res.partner')
    accept_decline_flag = fields.Boolean('Accept/Decline Flag')
    decline_description = fields.Text('Decline Description ',states={'reject': [('readonly', False)]})
    line_ids = fields.One2many('sale.catalog.order.line', 'catalog_order_id', states={'draft': [('readonly', False)]},copy=True,string='Catalog Order Lines')
    user_id = fields.Many2one('res.users', string='Responsible', related='catalog_id.user_id', readonly=True,store=True)
    sale_order_id = fields.Many2one('sale.order', string='Sale Order')

    def line_ordering_by_product(self):
        product_list = []
        # product_list = self.catalog_id.line_ids.mapped('product_pro_id.name')
        user = self.env.user
        # product_list =  self.catalog_id.line_ids.mapped(lambda line:line.product_pro_id.name if user.country_id not in line.product_pro_id.geo_restriction else '')
        for line in self.catalog_id.line_ids:
            if user.country_id.id not in line.product_pro_id.geo_restriction.ids:
                product_name = line.product_pro_id.name_get()[0][1]
                product_list.append(product_name.strip())
            else:
                product_list.append('')
        #to filter blank values comes where geo ristricted product comes
        product_list = list(filter(None, product_list))
        product_list = list(set(product_list))
        product_list.sort()
        return product_list

    def line_product_dict(self,product_name):
        product_dict = {}
        user = self.env.user
        restricted_products = self.env['product.product'].search([('geo_restriction','in',user.country_id.ids)])
        catalog_id = self.catalog_id.line_ids.filtered(lambda line: line.product_pro_id.name_get()[0][1] == product_name)
        if catalog_id[0].product_pro_id.id not in restricted_products.ids:
            product_dict[product_name] = {'line_ids': [catalog_id[0]]}
            return product_dict
        else:
            product_dict[product_name] = {'line_ids': []}
            return product_dict
