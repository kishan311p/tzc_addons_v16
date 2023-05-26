from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class delivery_package_line(models.Model):
    _name = 'delivery.package.line'

    name = fields.Char('Package Name')
    height = fields.Integer('Height (in cm)')
    width = fields.Integer('Width (in cm)')
    length = fields.Integer('Length (in cm)')
    weight = fields.Float('Weight (in kg)')
    picking_id = fields.Many2one('stock.picking')
    deliver_box_domain_ids = fields.Many2many('delivery.box.line','delivery_package_domain_deliverybox_rel','package_domain_id','box_domain_id','Box')
    delivery_box_ids = fields.Many2many('delivery.box.line','packageline_deliverybox_rel','deliverypackage_line_id','delverybox_id','Box')
    # deliver_box_ids = fields.One2many('delivery.box.line','delivery_package_line_id','Box')
    tracking_number = fields.Char('Tracking Number')
    package_label = fields.Binary('Shipping Label')
    file_name = fields.Char()
    def _filter_commodity_categories(self):
        categories_ids = self.env['product.category'].search([('name','in',['S','E','Case'])])
        return categories_ids.ids
    categ_ids = fields.Many2many('product.category','delivery_packagelinedomain_product_categ_rel','delivery_package_linedomain_id','product_categ_id','Commodities',default=_filter_commodity_categories)
    commodity_ids = fields.Many2many('product.category','delivery_packageline_product_categ_rel','delivery_package_line_id','product_categ_id','Commodities')
    qty = fields.Float('Quantity')

    # @api.onchange('delivery_box_ids')
    # def _compute_categ_ids(self):
    #    for rec in self:
    #         category_ids=False
    #         if rec.delivery_box_ids:
    #             category_ids = rec.picking_id.move_ids_without_package.mapped('product_id').mapped('categ_id').ids
    #             # if rec.delivery_box_ids.filtered(lambda x : x.extra_case_qty):
    #             #     case_id = self.env.ref('tzc_sales_customization_spt.case_product_category').id
    #             #     category_ids.append(case_id)
                
    #         rec.categ_ids = self.env['product.category'].search([('id','in',category_ids)])
    
    @api.onchange('delivery_box_ids')
    def _compute_package_qty(self):
        # updating qty and weight according to boxes
        for rec in self:
            qty = 0
            weight = 0
            if rec.delivery_box_ids:
                qty = sum(rec.delivery_box_ids.mapped("qty"))
                weight = sum(rec.delivery_box_ids.mapped("weight"))
            rec.qty = qty
            rec.weight = weight

    @api.onchange('delivery_box_ids','picking_id')
    def _compute_box_domain(self):
        # Use for filtering delivery box ids.
        for rec in self:
            ignore_ids = rec.picking_id.delivery_package_line_ids.mapped('delivery_box_ids').ids
            rec.deliver_box_domain_ids = rec.picking_id._origin.delivery_box_line_ids.filtered(lambda x: x.id not in ignore_ids)._origin
    
    @api.constrains('width','height','length')
    def check_package_dimension(self):
        for rec in self:
            if rec.width <= 0 or rec.height <= 0 or rec.length <= 0:
                raise UserError('Package dimension must be greater than 0.')