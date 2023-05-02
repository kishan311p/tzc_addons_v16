from odoo import _, api, fields, models
from odoo.exceptions import UserError
import json

class kits_scan_return_items_wizard_line(models.TransientModel):
    _name = 'kits.scan.return.items.wizard.line'
    _description = 'Scan Return Items Line'
    
    product_id = fields.Many2one('product.product', string='Product')
    return_items_id = fields.Many2one('kits.scan.return.items.wizard', string='Return Items')
    product_qty = fields.Float('Quantity')
    sequence = fields.Integer(index=True,)
    barcode_spt = fields.Char('Barcode')

    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            if record.product_id:
                if not record.return_items_id.return_order_id.return_line_ids.filtered(lambda line : line.product_id.id == record.product_id.id  and not line.id!= record.id):
                    self._cr.execute(('SELECT id FROM sale_order_line WHERE product_id = %s AND order_id IN %s ORDER BY order_id'%(record.product_id.id,tuple(record.return_items_id.return_order_id.order_ids.ids))).replace(',)', ')'))
                    line_ids = self._cr.fetchall()
                    line_ids = [sol_id[0] for sol_id in line_ids ]
                    if not line_ids:
                        raise UserError(_('Product not found in selected order.'))
                else:
                    raise UserError(_('Duplicate product found.'))

    @api.onchange('product_qty')
    def _onchange_product_qty(self):
        for record in self:
            if record.product_id:
                self._cr.execute(('SELECT id FROM sale_order_line WHERE product_id = %s AND order_id IN %s ORDER BY order_id'%(record.product_id.id,tuple(record.return_items_id.return_order_id.order_ids.ids))).replace(',)', ')'))
                line_ids = self._cr.fetchall()
                line_ids = [sol_id[0] for sol_id in line_ids ]
                line_ids = self.env['sale.order.line'].browse(line_ids)
                if sum(line_ids.mapped('product_qty')) < record.product_qty:
                    raise UserError(_('Product quantity more than delivered quantity.'))
                
class kits_scan_return_items_wizard(models.TransientModel):
    _name = 'kits.scan.return.items.wizard'
    _description = 'Scan Return Items'
    _inherit = ["barcodes.barcode_events_mixin"]
    
    return_order_id = fields.Many2one('kits.return.ordered.items', string='Return Order')
    return_items_ids = fields.One2many('kits.scan.return.items.wizard.line', 'return_items_id', string='Return Items Line')
    return_type = fields.Selection([
        ('return', 'Return'),('scrap', 'Scrap')
    ], string='Type',default="return")

    def on_barcode_scanned(self, barcode):
        self._add_product(barcode)

    def _add_product(self,barcode):
        wizard_line_obj = self.env['kits.scan.return.items.wizard.line']
        search_product = self.env["product.product"].search([("barcode","=",barcode)], limit = 1)
        self._cr.execute('SELECT id FROM sale_order_line WHERE product_id = %s AND order_id IN %s ORDER BY order_id'%(search_product.id,str(tuple(self.return_order_id.order_ids.ids)).replace(',)', ')')))
        line_ids = self._cr.fetchall()
        line_ids = [sol_id[0] for sol_id in line_ids ]
        if not line_ids:
            raise UserError(_('Product not found in selected order.'))
        line_ids = self.env['sale.order.line'].browse(line_ids)
        self._cr.execute('SELECT COALESCE(sum(product_qty),0) FROM kits_return_ordered_items_line WHERE product_id = %s and (scrap_order_id = %s or return_order_id = %s )'%(search_product.id,self.return_order_id.id,self.return_order_id.id))
        line_qty=self._cr.fetchall()
        line_qty=[oid[0] for oid in line_qty ][-1]
        line_qty =line_qty+ sum(self.return_items_ids.mapped(lambda line : line.product_qty if line.product_id.id == search_product.id else 0))
        if sum(line_ids.mapped('product_qty')) < line_qty+1:
            raise UserError(_('Scanned item is more than delivered quantity.'))
        scaned = True
        line = line_ids[-1]
        wizard_line = self.return_items_ids.filtered(lambda line: line.product_id.id == search_product.id)
        if line:
            if wizard_line:
                # self.return_items_ids.write({'sequence': 1})
                wizard_line[0].sequence = 0
                wizard_line[0].product_qty =  wizard_line[0].product_qty +1
            else:
                # self.return_items_ids.write({'sequence': 1})
                new_line_id = wizard_line_obj.new({
                    'product_id' : line.product_id.id,
                    'product_qty' : 1,
                    'sequence' : 0,
                    'return_items_id' : self.id,
                })

    def action_process(self):
        return_obj = self.env['kits.return.ordered.items.line']
        for line in self.return_items_ids:
            if self.return_type == 'return':
                return_obj.create({
                    'product_id' : line.product_id.id,
                    'return_order_id' : self.return_order_id.id,
                    'product_qty' : line.product_qty,
                    'return_type' : self.return_type,
                })
            else:
                return_obj.create({
                    'product_id' : line.product_id.id,
                    'scrap_order_id' : self.return_order_id.id,
                    'product_qty' : line.product_qty,
                    'return_type' : self.return_type,
                })