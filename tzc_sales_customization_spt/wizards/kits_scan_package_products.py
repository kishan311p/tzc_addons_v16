from odoo import models,fields,api,_
from odoo.exceptions import UserError

class kits_scan_package_product_lines(models.TransientModel):
    _name = 'kits.scan.package.product.lines'
    _description = 'Scan Package Product Lines'

    wiz_id = fields.Many2one('kits.scan.package.products','Wiard')
    product_id = fields.Many2one('product.product','Product')
    package_id = fields.Many2one('kits.package.product','Package')
    barcode_spt = fields.Char('Barcode')
    product_qty = fields.Integer('Qty')

class kits_scan_package_products(models.TransientModel):
    _name = 'kits.scan.package.products'
    _inherit = ["barcodes.barcode_events_mixin"]
    _description = 'Scan Package Products'

    def _get_available_packages(self):
        picking_id = self.env['stock.picking'].browse(self.env.context.get('default_picking_id'))
        packages = picking_id.move_ids_without_package.filtered(lambda x: x.product_uom_qty > x.quantity_done and x.package_id).mapped('package_id')
        return [('id','in',packages.ids)]

    line_ids = fields.One2many('kits.scan.package.product.lines','wiz_id','Lines')
    picking_id = fields.Many2one('stock.picking','Picking',required=True)
    total_qty = fields.Integer('Total QTY',compute="_compute_total_qty")
    package_id = fields.Many2one('kits.package.product','Package',domain=_get_available_packages)

    @api.depends('line_ids','line_ids.product_qty')
    def _compute_total_qty(self):
        total = 0
        for line in self.line_ids:
            total += line.product_qty
        self.total_qty = total

    def on_barcode_scanned(self, barcode):
        self._add_product(barcode)

    def _add_product(self,barcode):
        search_product = self.env["product.product"].search([("barcode","=",barcode)], limit = 1)
        if self.package_id:
            if search_product:
                search_lines = self.line_ids.filtered(lambda ol: ol.product_id.barcode == barcode and ol.package_id == self.package_id)
                stock_moves  = self.env['stock.move'].sudo().search([('picking_id','=',self.picking_id.id),('product_id','=',search_product.id)])
                if stock_moves:
                    package_lines = stock_moves.filtered(lambda x: x.package_id == self.package_id)
                    if package_lines:
                        product_moves = package_lines.filtered(lambda ol: (ol.product_uom_qty-ol.quantity_done) > search_lines.product_qty)
                        package = product_moves.package_id if len(product_moves) == 1 else product_moves[0].package_id if product_moves else False
                        
                        # changes
                        qty_needed = sum(product_moves.mapped('product_uom_qty'))-sum(product_moves.mapped('quantity_done')) - search_lines.product_qty
                        if qty_needed > 0 :
                            if search_product.available_qty_spt - search_lines.product_qty <= 0:
                                raise UserError(_("You scanned more quantity than package have for product %s."%(search_product.variant_name)))
                            else:
                                if search_lines:
                                    search_lines.barcode_spt = barcode
                                    search_lines.product_qty += 1
                                else:
                                    vals = {
                                        'product_id': search_product.id,
                                        'product_qty': 1,
                                        'barcode_spt': barcode,
                                        'package_id':package.id if package else False
                                    }
                                    new_line_ids = self.line_ids.new(vals)                                          
                                    self.line_ids += new_line_ids
                        else:
                            raise UserError(_('All quantity scanned for product %s.\nProcess to set done quantitiy.'%(search_product.variant_name)))
                    else:
                        raise UserError(_("Scanned product of package %s not found in order."%(self.package_id.name)))
                else:
                    raise UserError(_('Scanned product not found in order.'))
            else:                   
                raise UserError(_("Scanned Barcode does not exist. Try manual entry.")) 
        else:
            raise UserError(_("Please select package first."))

    def action_process(self):
        for line in self.line_ids:
            self.picking_id.write({'state': 'in_scanning'})
            self.picking_id.sate_id.write({'state': 'in_scanning'})
            move = self.picking_id.move_ids_without_package.filtered(lambda x: x.product_id == line.product_id and x.package_id == line.package_id)
            if move:
                if move.product_uom_qty >= line.product_qty:
                    move.write({'quantity_done':move.quantity_done+line.product_qty})
                elif move.product_uom_qty < line.product_qty:
                    raise UserError(_('For product %s scanned quantity is more than demanded.'%(line.product_id.variant_name)))
                else:
                    pass
            else:
                pass
            

    def action_remove_package(self):
        sale_order = self.picking_id.sale_id
        if sale_order:
            sale_order.package_order_lines.filtered(lambda x: x.product_id == self.package_id ).sudo().unlink()
        moves = self.picking_id.move_ids_without_package.filtered(lambda x: x.package_id == self.package_id)
        moves.write({'quantity_done':0,'state':'draft'})
        moves.unlink()
