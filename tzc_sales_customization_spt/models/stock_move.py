from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
import requests
import json

class stock_move(models.Model):
    _inherit = 'stock.move'

    package_id = fields.Many2one('kits.package.product',compute="_compute_package_id",store=True,compute_sudo=True)
    qty_available = fields.Float('Total Qty',related='product_id.qty_available')

    @api.depends('sale_line_id','sale_line_id.package_id')
    def _compute_package_id(self):
        for record in self:
            if record.sale_line_id and record.sale_line_id.is_pack_order_line:
                record.package_id = record.sale_line_id.package_id.id

    def stock_quant_update_spt(self):
        context={}
        for move in self:
            if move.product_id.type == "product":
                for line in move.move_line_ids:
                    if line.picking_id.state in ['done','cancel']:
                        line.qty_done = 0
                        qty = line.product_uom_id._compute_quantity(line.qty_done, line.product_id.uom_id)
                        self.env['stock.quant']._update_available_quantity(line.product_id, line.location_id, qty)
                        self.env['stock.quant']._update_available_quantity(line.product_id, line.location_dest_id, qty * -1)
            context.update(self._context)
            context.update({'stock_quant_update_spt':True})
            move.with_context(context)._action_cancel()
        return True
