from odoo import models,fields,api,_
from odoo.exceptions import UserError
from datetime import datetime

class remove_done_quantity_spt(models.TransientModel):
    _name = "remove.done.quantity.spt"
    _inherit = ["barcodes.barcode_events_mixin"]
    _description = 'Remove Done Quantity'

    product_ids = fields.Many2many("product.product")
    line_ids = fields.One2many("remove.stock.done.qty.line.spt",'product_line_id')
    picking_id = fields.Many2one('stock.picking',"Picking")
    total_qty = fields.Integer("Total Qty",compute="_compute_total_qty")
    product_id = fields.Many2one('product.product','Manual')
    qty = fields.Integer(default=1)
    # product_id = fields.Many2one('product.product','Manually Product Select')

    @api.depends('line_ids','line_ids.product_qty')
    def _compute_total_qty(self):
        total = 0
        for line in self.line_ids:
            total += line.product_qty
        self.total_qty = total

    def _add_product(self,barcode):
        sequence = 0
        # self.line_ids.update({
        #         'sequence': 0,
        #         })   
        search_product = self.env['product.product'].search([('barcode','=',barcode)])
        if search_product and search_product.id:
            search_lines = self.line_ids.filtered(lambda x: x.product_id.barcode == barcode)
            move = self.picking_id.move_ids_without_package.filtered(lambda x: x.product_id.barcode == barcode)
            total = 0
            for move_rec in move:
                total += move_rec.quantity_done
            if move and move.ids:
                if search_lines:
                    if total > search_lines.product_qty:
                        search_lines.product_qty += 1
                        for line in self.line_ids:
                            line.sequence += 1
                        if self.line_ids:
                            search_lines.sequence = min(self.line_ids.mapped('sequence'))-1
                        else:
                            search_lines.sequence = sequence
                        # search_lines.sequence += sequence
                    else:
                        raise UserError(_("Scanned product's 'Done' quantity is not enough !"))
                else:
                    if total == 0:
                        raise UserError(_("Scanned product's quantity is Zero!"))
                    else:
                        vals = {
                            'product_id':search_product.id,
                            'product_qty':1,
                            # 'sequence':sequence,
                        }
                        if self.line_ids:
                            if sequence - len(self.line_ids) in self.line_ids.mapped('sequence'):
                                vals.update({'sequence': sequence - len(self.line_ids)-1})
                            else:
                                vals.update({'sequence': sequence - len(self.line_ids)})
                        else:
                            vals.update({'sequence': 0})

                        new_line_ids = self.line_ids.create(vals)
                        self.line_ids += new_line_ids
            else:
                raise UserError('Scanned product not found in Order !')
        else:
            raise UserError("Scanned barcode not found in any products !")
            
    
    def action_process(self):
        messages=[]
        flag=False
        if self.line_ids:
            for line in self.line_ids:
                if line.product_id and line.product_id.id:
                    move_ids = self.picking_id.move_ids_without_package.filtered(lambda x: x.product_id == line.product_id)
                    qty = line.product_qty
                    qty_line = line.product_qty
                    if move_ids and move_ids.ids:
                        for i in range(0,len(move_ids)):
                            try:
                                if qty > 0:
                                    qty = qty - move_ids[i].quantity_done
                                    move_ids[i].write({"quantity_done":0 if qty >= 0 else move_ids[i].quantity_done-abs(move_ids[i].quantity_done+qty)})
                                    move_ids[i].picking_id.write({'updated_by':self.env.user.id,'updated_on':datetime.now()})
                                    move_ids[i].sale_line_id.order_id.write({'updated_by':self.env.user.id,'updated_on':datetime.now()})
                                    line.sudo().product_id.product_import_product_published()
                                else:
                                    continue
                            except:
                                for move in move_ids.mapped('move_line_ids'):
                                    if qty_line > 0:
                                        qty_line = qty_line - move.qty_done
                                    move.write({"qty_done":0 if qty_line >= 0 else move.qty_done-abs(move_ids.quantity_done+qty_line)})
                                    move.picking_id.write({'updated_by':self.env.user.id,'updated_on':datetime.now()})
                                    move.picking_id.sale_id.write({'updated_by':self.env.user.id,'updated_on':datetime.now()})
                                    line.sudo().product_id.product_import_product_published()
                                else:
                                    continue
                    else:
                        messages.append('No order for product %s.'%(line.product_id.name))
                        flag=True
                else:
                    messages.append("No product found in line.")
                    flag=True
            self.picking_id._compute_qty()
            # self.picking_id.sale_id._compute_qty()
        if flag:
            raise UserError('\n'.join(messages)) 

    def on_barcode_scanned(self, barcode):
        self._add_product(barcode)
    
    def action_edit_product(self):
        self.ensure_one()
        sequence = 0
        if self.product_id and self.qty:
            # self.line_ids.update({'sequence':0})
            search_line = self.line_ids.filtered(lambda x:x.product_id.id == self.product_id.id)
            move = self.picking_id.move_ids_without_package.filtered(lambda x: x.product_id.barcode == self.product_id.barcode)
            if move and move.ids:
                if search_line:
                    if self.qty <= move.quantity_done:
                        # search_line.sequence = -1
                        search_line.product_qty = self.qty
                        for line in self.line_ids:
                            line.sequence += 1
                        if self.line_ids:
                            search_line.sequence = min(self.line_ids.mapped('sequence'))-1
                        else:
                            search_line.sequence = sequence
                    else:
                        raise UserError(_("Scanned product's 'Done' quantity is not enough !"))
                else:
                    raise UserError(_("Product not found."))
            else:
                raise UserError(_("Product not found."))

            self.product_id = False
            self.qty = 1

            return {
                'name': 'Remove Items',
                'view_mode': 'form',
                'target': 'new',
                'res_id':self.id,
                'res_model': 'remove.done.quantity.spt',
                'type': 'ir.actions.act_window',
                }
        else:
            if not self.product_id or not self.qty:
                raise UserError ('The product must be selected.')

    def action_remove_product(self):
        self.ensure_one()
        sequence = 0
        if self.product_id and self.qty:
            # self.line_ids.update({'sequence':0})
            search_line = self.line_ids.filtered(lambda x:x.product_id.id == self.product_id.id)
            move = self.picking_id.move_ids_without_package.filtered(lambda x: x.product_id.barcode == self.product_id.barcode)
            total = 0
            for move_rec in move:
                total += move_rec.quantity_done
            if move and move.ids:
                if search_line:
                    if total > search_line.product_qty:
                        search_line.product_qty += self.qty
                        # search_line.sequence = -1
                        for line in self.line_ids:
                            line.sequence += 1
                        if self.line_ids:
                            search_line.sequence = min(self.line_ids.mapped('sequence'))-1
                        else:
                            search_line.sequence = sequence
                    else:
                        raise UserError(_("Scanned product's 'Done' quantity is not enough !"))
                else:
                    if total == 0:
                        raise UserError(_("Scanned product's quantity is Zero!"))
                    else:
                        if total < self.qty:
                            raise UserError(_("Scanned product's 'Done' quantity is not enough !"))
                        else:
                            line_id = self.env['remove.stock.done.qty.line.spt'].create({'product_id':self.product_id.id,'product_qty':self.qty,'sequence':-1,'product_line_id':self.id})
                            if self.line_ids:
                                line_id.sequence = sequence - len(self.line_ids)+1
                            else:
                                line_id.sequence = sequence

            self.product_id = False
            self.qty = 1

            return {
                'name': 'Remove Items',
                'view_mode': 'form',
                'target': 'new',
                'res_id':self.id,
                'res_model': 'remove.done.quantity.spt',
                'type': 'ir.actions.act_window',
                }
        else:
            if not self.product_id or not self.qty:
                raise UserError ('The product must be selected.')

class remove_stock_done_qty_line_spt(models.TransientModel):
    _name = "remove.stock.done.qty.line.spt"
    _description = 'Remove Stock Done Qty Line'

    def _get_domain(self):
        product_ids = False
        if self._context and self._context.get('default_picking_id'):
            delivery_id = self.env['stock.picking'].browse([self._context.get('default_picking_id')])
            if delivery_id:
                product_ids = self.env['product.product'].search([('id','in',delivery_id.move_ids_without_package.product_id.ids)])

        return [('id','in',product_ids.ids)] if product_ids else []

    product_id = fields.Many2one('product.product','Product',domain=_get_domain)
    product_qty = fields.Integer("Qty",default=1)
    product_line_id = fields.Many2one('remove.done.quantity.spt',"Product")
    sequence = fields.Integer(string='Sequence',index=True)

    def action_product_selection(self):
        self.ensure_one()
        if self.product_line_id:
            self.product_line_id.product_id = self.product_id.id

            return {
                    'name': 'Remove Items',
                    'view_mode': 'form',
                    'target': 'new',
                    'res_id':self.product_line_id.id,
                    'res_model': 'remove.done.quantity.spt',
                    'type': 'ir.actions.act_window',
                    }
