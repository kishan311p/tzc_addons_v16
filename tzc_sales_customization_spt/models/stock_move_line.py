from odoo import models,fields,api,_
from odoo.exceptions import UserError

class stock_move_line(models.Model):
    _inherit = 'stock.move.line'

    qty_on_hand = fields.Integer(compute="_compute_qty_on_hand",string='Qty On Hand')
    available_qty = fields.Integer(compute="_compute_qty_on_hand",string='Available Qty')
    status = fields.Selection([('added', 'Added'), ('removed', 'Removed'), ('reserved', 'Reserved'),('shipped','Shipped'),('return','Return'),('scrap','Scrap'),('cancelled','Cancelled')],string='State',compute='_compute_line_status',store=True)


    @api.depends('state','location_id','location_dest_id')
    def _compute_line_status(self):
        for rec in self:
            rec.status = False
            is_locations = rec.location_id and rec.location_dest_id
            if rec.state in ['waiting','draft','confirmed','partially_available','assigned'] and 'customers' in rec.location_dest_id.name.lower() and 'wh/stock' in rec.location_id.display_name.lower():
                rec.status = 'reserved'
            if rec.state == 'cancel':
                rec.status = 'cancelled'
            if rec.state == 'done' and is_locations and 'customers' in rec.location_dest_id.name.lower() and 'wh/stock' in rec.location_id.display_name.lower():
                rec.status = 'shipped'
            if is_locations and 'virtual locations' in rec.location_id.display_name.lower() and 'wh/stock' in rec.location_dest_id.display_name.lower():
                rec.status = 'added'
            if is_locations and 'virtual locations' in rec.location_dest_id.display_name.lower() and 'wh/stock' in rec.location_id.display_name.lower():
                rec.status = 'removed'
            if rec.move_id.return_order_line_id:
                status = 'scrap' if rec.move_id.return_order_line_id.return_type == 'scrap' else 'return' 
                if rec.state == 'cancel':
                    status = 'cancelled'
                rec.status = status
                    

    @api.depends('location_id','state')
    def _compute_qty_on_hand(self):
        for rec in self:
            lines = self.env['stock.move.line'].search([('product_id','=',rec.product_id.id),('state','=','done'),('id','<=',rec.id)],order='id asc')
            reserved_lines = self.env['stock.move.line'].search([('product_id','=',rec.product_id.id),('state','not in',('draft','cancel','done')),('id','<=',rec.id)]).filtered(lambda x: x.location_id.display_name.startswith('WH/Stock'))
            virtual_loc_lines = lines.filtered(lambda x : x.location_id.display_name.startswith('Virtual Locations/') or x.location_id.display_name.startswith('Partner Locations/') and x.location_dest_id.display_name.startswith('WH/Stock'))
            wh_stock_lines = lines.filtered(lambda x : x.location_id.display_name.startswith('WH/Stock'))
            rec.qty_on_hand = sum(virtual_loc_lines.mapped('qty_done')) - sum(wh_stock_lines.mapped('qty_done'))
            rec.available_qty = rec.qty_on_hand  - sum(reserved_lines.mapped('qty_done'))
    
    # def write(self,vals):
    #     res = super(stock_move_line,self).write(vals)
    #     if self.picking_id.state not in ['scanned','assigned','done','cancel'] or self._context.get('ship') or self._context.get('cancel_delivery') or self._context.get('cancel_order'):
    #         return res
    #     else:
    #         raise UserError ('You can not add product after order scanning completed.')
