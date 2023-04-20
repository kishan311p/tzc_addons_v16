# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning,UserError
from datetime import datetime

class stock_picking_barcode_line_spt(models.TransientModel):
    _name = "stock.picking.barcode.line.spt"
    _description = "Delivery Barcode Line"
    _order = 'sequence'

    product_id = fields.Many2one('product.product','Product')
    product_qty = fields.Integer('Qty',default=1)
    sb_order_id = fields.Many2one('stock.picking.barcode.spt','Barcode Order')
    barcode_spt = fields.Char('Barcode')
    sequence = fields.Integer(string='Sequence',index=True)
    scan_extra_item_wiz = fields.Boolean()

    @api.onchange('product_id','product_qty')
    def onchange_sound(self):
        if self and not self._context.get('scann') and -1 not in self.mapped('sequence'):
            sound_type = False
            last_line = self.filtered(lambda x:x.sequence == max(self.mapped('sequence')))
            if last_line and last_line.product_id:
                stock_move = self.sb_order_id.picking_id.move_ids_without_package.filtered(lambda x:x.product_id.barcode == last_line.product_id.barcode)
                qty = stock_move.quantity_done + self.product_qty if stock_move.quantity_done else last_line.product_qty
                if stock_move and stock_move.product_qty < qty:
                    sound_type = 'user_connection'
                elif not stock_move:
                    sound_type = 'user_connection'

                if sound_type:
                    invite_partner = self.env.user.partner_id
                    product_name = self.env['product.product'].search([('barcode','=',last_line.product_id.barcode)]).variant_name
                    if invite_partner:
                        title = _("Extra Item Scanned")
                        message = _("%s is scanned")% product_name
                        self.env['bus.bus'].sendone(
                            (self._cr.dbname, 'res.partner', invite_partner.id),
                            {'type': sound_type,'title': title, 'message': message, 'sticky': False}
                        )

    def action_product_selection(self):
        self.ensure_one()
        if self.sb_order_id:
            self.sb_order_id.product_id = self.product_id.id

            return {
                    'name': 'Scan Order',
                    'view_mode': 'form',
                    'target': 'new',
                    'res_id':self.sb_order_id.id,
                    'res_model': 'stock.picking.barcode.spt',
                    'type': 'ir.actions.act_window',
                    }

class stock_picking_barcode_spt(models.TransientModel):
    _name = "stock.picking.barcode.spt"
    _inherit = ["barcodes.barcode_events_mixin"]
    _order = 'id'
    _description = "Delivery Barcode"

    line_ids = fields.One2many('stock.picking.barcode.line.spt','sb_order_id',string='Barcode Picking Order Lines')
    # line_ids = fields.Many2many('stock.picking.barcode.line.spt',string='Barcode Picking Order Lines')
    product_qty_count = fields.Integer('Total Qty',compute="_compute_product_qty")
    picking_id = fields.Many2one('stock.picking','Order')
    _barcode_scanned = fields.Char()
    product_id = fields.Many2one('product.product','Manual')
    qty = fields.Integer(default=1)

    @api.depends('line_ids','line_ids.product_qty')
    def _compute_product_qty(self):
        for record in self:
            total_qty = 0.0
            for line in record.line_ids:
                total_qty += line.product_qty
            record.product_qty_count = total_qty
    
    def _add_product(self, barcode):
        ctx = self.env.context.copy()
        ctx.update({'scann':True})
        self.env.context = ctx 
        sequence = 0
        # self.line_ids.update({
        #         'sequence': 0,
        #         })
        search_lines = self.line_ids.filtered(lambda ol: ol.product_id.barcode == barcode)
        stock_move = self.picking_id.move_ids_without_package.filtered(lambda x:x.product_id.barcode == barcode)
        if search_lines:
            search_lines.barcode_spt = barcode
            search_lines.product_qty += 1
            # search_lines.sequence += sequence
            for line in self.line_ids:
                line.sequence += 1
            if self.line_ids:
                search_lines.sequence = min(self.line_ids.mapped('sequence'))-1
            else:
                search_lines.sequence = sequence
            notify_type = self.get_notify_type(stock_move,search_lines)
            self.get_notify(barcode,notify_type)
        else:
            search_product = self.env["product.product"].search([("barcode","=",barcode)], limit = 1)
            if search_product:
                qty = 1
                vals = {
                    'product_id': search_product.id,
                    'product_qty': qty,
                    'barcode_spt': barcode,
                    # 'sequence': sequence,
                }
                if self.line_ids:
                    if sequence - len(self.line_ids) in self.line_ids.mapped('sequence'):
                        vals.update({'sequence': sequence - len(self.line_ids)-1})
                    else:
                        vals.update({'sequence': sequence - len(self.line_ids)})
                else:
                    vals.update({'sequence': 0})
                new_line_ids = self.line_ids.new(vals)                                                                    
                self.line_ids += new_line_ids
                notify_type = self.with_context(product_quantity=qty).get_notify_type(stock_move)
                self.get_notify(barcode,notify_type)
            else:                   
                raise UserError(_("Scanned Barcode does not exist. Try manual entry."))

    def get_notify_type(self,move,line=False):
        qty = line.product_qty if line and not self._context.get('product_quantity') else self._context.get('product_quantity')
        notification_type = False
        if move:
            if move.product_uom_qty < qty if qty != None else 0:
                notification_type = 'user_connection'
            elif move.scan_extra_item:
                notification_type = 'user_connection'
        else:
            notification_type = 'user_connection'
        
        return notification_type
    
    def get_notify(self,barcode,type,product_id=False):
        # notification = []
        # notification.append([user.partner_id, 'simple_notification', body])
        # body = {
        #                     'type': 'simple_notification',
        #                     'title': 'Outgoing Mail Server Failed',
        #                     'message': _("Outgoing mail server '{}' is not working.".format(server.name)),
        #                     'sticky': True,
        #                     'warning': True
        #                 }
        # self.env['bus.bus']._sendmany(notification)
        if type == 'user_connection':
            notification = []
            invite_partner = self.env.user.partner_id
            if barcode:
                product_name = self.env['product.product'].search([('barcode','=',barcode)]).variant_name
            elif product_id:
                product_name = self.env['product.product'].browse(product_id).variant_name
            if invite_partner:
                body = {
                    'type': type,
                    'title': _("Extra Item Scanned"),
                    'message': _("%s is scanned")% product_name,
                    'sticky': False,
                }
                notification.append([invite_partner, 'simple_notification', body])
                self.env['bus.bus']._sendmany(notification)

                # title = _("Extra Item Scanned")
                # message = _("%s is scanned")% product_name
                # self.env['bus.bus']._sendone(
                #         (self._cr.dbname, 'res.partner', invite_partner.id),
                #         {'type': type,'title': title, 'message': message, 'sticky': False},
                #         message=message
                #     )
            
    def on_barcode_scanned(self, barcode):
        self._add_product(barcode)
    
    def action_process(self):
        self.ensure_one()
        stock_move_obj = self.env['stock.move']
        line_list = []
        product_list = []
        for data_line in self.line_ids:
            if data_line.product_id.id in product_list:
                line_id = list(filter(lambda line: line.product_id.id == data_line.product_id.id,line_list))[0]
                line_id.product_qty = data_line.product_qty + line_id.product_qty
            else:
                product_list.append(data_line.product_id.id)
                line_list.append(data_line)
                
        for line in line_list:
            move_id = self.picking_id.move_ids_without_package.filtered(lambda move: move.product_id == line.product_id)
            if move_id:
                move_id = self.picking_id.check_duplicate_move(move_id)
                move_id.quantity_done  =  move_id.quantity_done + line.product_qty 
            else:
                stock_move_id = stock_move_obj.create({
                    'location_id' : self.picking_id.location_id.id,
                    'location_dest_id' : self.picking_id.location_dest_id.id,
                    'product_id' : line.product_id.id,
                    'product_uom' : line.product_id.uom_id.id,
                    'date' : fields.Datetime.now(),
                    'company_id': self.picking_id.company_id.id,
                    'quantity_done' : line.product_qty,
                    'name':line.product_id.name,
                    'scan_extra_item':line.scan_extra_item_wiz,
                    'description_picking':line.product_id.name,
                    'product_uom_qty':0,
                })
                stock_move_id.move_line_ids.write({'qty_done':line.product_qty,'picking_id':self.picking_id.id})
                stock_move_id.picking_id = self.picking_id.id
        self.picking_id.action_assign()
        if self._context.get('sale_order_spt',False):
            return {
                'name': _(self.picking_id.name),
                'view_mode': 'form',
                'res_model': 'stock.picking',
                'view_id': self.env.ref('stock.view_picking_form').id,
                'type': 'ir.actions.act_window',
                'res_id': self.picking_id.id,
            }
        self.picking_id.sale_id.write({'state': 'in_scanning','updated_by':self.env.user.id,'updated_on':datetime.now()})
        self.picking_id.sale_id._amount_all()
        self.picking_id.update_sale_order_spt()
        self.picking_id.write({'state': 'in_scanning'})

    def action_edit_product(self):
        self.ensure_one()
        sequence = 0
        if self.product_id and self.qty:
            stock_move = self.picking_id.move_ids_without_package.filtered(lambda x:x.product_id.id == self.product_id.id)
            search_line = self.line_ids.filtered(lambda x:x.product_id.id == self.product_id.id)
            # self.line_ids.update({'sequence':0})
            if search_line:
                search_line.product_qty = self.qty
                for line in self.line_ids:
                    line.sequence += 1
                if self.line_ids:
                    search_line.sequence = min(self.line_ids.mapped('sequence'))-1
                else:
                    search_line.sequence = sequence
                # search_line.sequence = -1
                notify_type = self.get_notify_type(stock_move,search_line)
                self.get_notify(self.product_id.barcode,notify_type)
            else:
                notify_type = self.get_notify_type(stock_move,search_line)
                # notify_type = 'user_connection'
                self.get_notify(self.product_id.barcode,notify_type)
                # raise UserError('Product not found.')

            self.product_id = False
            self.qty = 1
        
            return {
                'name': 'Scan Order',
                'view_mode': 'form',
                'target': 'new',
                'res_id':self.id,
                'res_model': 'stock.picking.barcode.spt',
                'type': 'ir.actions.act_window',
                }
        else:
            if not self.product_id or not self.qty:
                raise UserError ('The product and quantity must be added.')

    def action_scan_product(self):
        self.ensure_one()
        sequence = 0
        if self.product_id and self.qty:
            stock_move = self.picking_id.move_ids_without_package.filtered(lambda x:x.product_id.id == self.product_id.id)
            search_line = self.line_ids.filtered(lambda x:x.product_id.id == self.product_id.id)
            # self.line_ids.update({'sequence':0})
            if search_line:
                search_line.product_qty += self.qty
                for line in self.line_ids:
                    line.sequence += 1
                if self.line_ids:
                    search_line.sequence = min(self.line_ids.mapped('sequence'))-1
                else:
                    search_line.sequence = sequence
                # search_line.sequence = -1
                notify_type = self.get_notify_type(stock_move,search_line)
                self.get_notify(self.product_id.barcode,notify_type)
            else:
                line_id = self.env['stock.picking.barcode.line.spt'].create({'product_id':self.product_id.id,'product_qty':self.qty,'sequence':-1,'sb_order_id':self.id,'scan_extra_item_wiz':True})
                if self.line_ids:
                    line_id.sequence = sequence - len(self.line_ids)+1
                else:
                    line_id.sequence = sequence
                notify_type = self.with_context(product_quantity=stock_move.product_uom_qty + self.qty if stock_move.quantity_done else self.qty).get_notify_type(stock_move)
                self.get_notify(self.product_id.barcode,notify_type)

            self.product_id = False
            self.qty = 1
        
            return {
                'name': 'Scan Order',
                'view_mode': 'form',
                'target': 'new',
                'res_id':self.id,
                'res_model': 'stock.picking.barcode.spt',
                'type': 'ir.actions.act_window',
                }
        else:
            if not self.product_id or not self.qty:
                raise UserError ('The product and quantity must be added.')

    def action_add_product(self):
        self.ensure_one()
        sequence = 0
        if self.product_id and self.qty:
            stock_move = self.picking_id.move_ids_without_package.filtered(lambda x:x.product_id.id == self.product_id.id)
            search_line = self.line_ids.filtered(lambda x:x.product_id.id == self.product_id.id)
            # self.line_ids.update({'sequence':0})
            if search_line:
                for line in self.line_ids:
                    line.sequence += 1
                if self.line_ids:
                    search_line.sequence = min(self.line_ids.mapped('sequence'))-1
                else:
                    search_line.sequence = sequence
                # search_line.sequence = -1
                search_line.product_qty += self.qty
                notify_type = self.get_notify_type(stock_move,search_line)
                self.get_notify(self.product_id.barcode,notify_type)
            else:
                line_id = self.env['stock.picking.barcode.line.spt'].create({'product_id':self.product_id.id,'product_qty':self.qty,'sequence':-1,'sb_order_id':self.id,'scan_extra_item_wiz':True})
                if self.line_ids:
                    line_id.sequence = sequence - len(self.line_ids)+1
                else:
                    line_id.sequence = sequence
                notify_type = self.get_notify_type(stock_move,search_line)
                self.get_notify(self.product_id.barcode,notify_type)
            
            self.product_id = False
            self.qty = 1
        
            return {
                'name': 'Scan Order',
                'view_mode': 'form',
                'target': 'new',
                'res_id':self.id,
                'res_model': 'stock.picking.barcode.spt',
                'type': 'ir.actions.act_window',
                }
        else:
            if not self.product_id or not self.qty:
                raise UserError ('The product and quantity must be added.')
