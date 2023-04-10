from odoo import models,fields,api,_

class stock_change_product_qty(models.TransientModel):
    _inherit = 'stock.change.product.qty'

    @api.onchange('product_id')
    def _onchange_product_id(self):
        self.new_quantity = self.product_id.available_qty_spt

    def change_product_qty(self):
        """ Changes the Product Quantity by creating/editing corresponding quant.
        """
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1
        )
        # Before creating a new quant, the quand `create` method will check if
        # it exists already. If it does, it'll edit its `inventory_quantity`
        # instead of create a new one.
        self.env['stock.quant'].with_context(inventory_mode=True).create({
            'product_id': self.product_id.id,
            'location_id': warehouse.lot_stock_id.id,
            'inventory_quantity': self.new_quantity + self.product_id.reversed_qty_spt if self._context.get('reserve_calculated',False) else self.new_quantity,
        })._apply_inventory()
        to_publish = self.product_id.product_color_name.name != 'Other' and self.product_id.eye_size_compute > 1 and not self.product_id.is_image_missing and self.product_id.available_qty_spt > 1
        if to_publish:
            self.product_id.is_published_spt = True
        if not to_publish and self.product_id.available_qty_spt <= 0:
            self.product_id.is_published_spt = False
        return {'type': 'ir.actions.act_window_close'}

    # def change_product_qty(self):
    #     res = super(stock_change_product_qty,self).change_product_qty()
    #     return res
