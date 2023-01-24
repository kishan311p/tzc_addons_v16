from odoo import models,fields,api,_
from odoo.exceptions import UserError

class kits_remove_package_product_lines(models.TransientModel):
    _name = 'kits.remove.package.product.lines'
    _description = 'Scan Package Product Lines'

    wiz_id = fields.Many2one('kits.remove.package.products','Wiard')
    product_id = fields.Many2one('product.product','Product')
    package_id = fields.Many2one('kits.package.product','Package')
    barcode_spt = fields.Char('Barcode')
    product_qty = fields.Integer('Qty')



class kits_remove_package_products(models.TransientModel):
    _name = 'kits.remove.package.products'
    _inherit = ["barcodes.barcode_events_mixin"]
    _description = 'Remove Package Products'

    def _get_available_packages(self):
        picking_id = self.env['stock.picking'].browse(self.env.context.get('default_picking_id'))
        packages = picking_id.move_ids_without_package.filtered(lambda x: x.package_id).mapped('package_id')
        return [('id','in',packages.ids)]

    line_ids = fields.One2many('kits.remove.package.product.lines','wiz_id','Lines')
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
        if self.package_id:
            search_lines = self.line_ids.filtered(lambda ol: ol.product_id.barcode == barcode)
            move_ids = self.picking_id.move_ids_without_package.filtered(lambda x: x.product_id.barcode == barcode)
            search_product = self.env["product.product"].search([("barcode","=",barcode)], limit = 1)
            if search_product and search_product.id:
                move_ids = move_ids.filtered(lambda x: x.package_id == self.package_id)
                if move_ids and move_ids.ids:
                    total = 0
                    for move in move_ids:
                        total += move.quantity_done
                    if search_lines:
                        if search_lines.product_qty < total:
                            search_lines.product_qty += 1
                        else:
                            raise UserError(_("Scanned Product's quantity is not enough."))
                    else:
                        if total == 0:
                            raise UserError(_("Scanned product's quntity is Zero."))
                        else:
                            vals = {
                                'product_id': search_product.id,
                                'product_qty': 1,
                            }
                            new_line_ids = self.line_ids.new(vals)                                                                    
                            self.line_ids += new_line_ids
                else:
                    raise UserError(_("Scanned Product with package %s can not be found in order."%(self.package_id.name)))
            else:
                raise UserError(_("Scanned Barcode does not exist. Try manual entry."))
        else:
            raise UserError(_("Please select package first."))

    def action_process(self):
        messages=[]
        flag=False
        for line in  self.picking_id.move_ids_without_package:
            self.picking_id.check_duplicate_move(line)
        for line in self.line_ids:
            if line.product_id and line.product_id.id:
                move_ids = self.picking_id.move_ids_without_package.filtered(lambda x: x.product_id == line.product_id)
                qty = line.product_qty
                qty_line = line.product_qty
                if move_ids and move_ids.ids:
                    move_ids = move_ids.filtered(lambda x: x.package_id == self.package_id)
                    if move_ids and move_ids.ids:
                        for i in range(0,len(move_ids)):
                            try:
                                if qty > 0:
                                    qty = qty - move_ids[i].quantity_done
                                    move_ids[i].write({"quantity_done":0 if qty >= 0 else move_ids[i].quantity_done-abs(move_ids[i].quantity_done+qty)})
                                else:
                                    continue
                            except:
                                for move in move_ids.mapped('move_line_ids'):
                                    if qty_line > 0:
                                        qty_line = qty_line - move.quantity_done
                                    move.write({"qty_done":0 if qty_line >= 0 else move.qty_done-abs(move_ids.qty_done+qty_line)})
                                else:
                                    continue
                    else:
                        raise UserError(_("Scanned product with package %s not found in order."%(self.package_id.name)))
                else:
                    messages.append('No order for product %s.'%(line.product_id.name))
                    flag=True
            else:
                messages.append("No product found in line.")
                flag=True
        if flag:
            raise UserError('\n'.join(messages))
