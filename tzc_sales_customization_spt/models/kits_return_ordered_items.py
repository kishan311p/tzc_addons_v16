from odoo import _, api, fields, models
from odoo.exceptions import UserError
class kits_return_ordered_items_line(models.Model):
    _name = 'kits.return.ordered.items.line'
    _description = 'Return Orderded Items Line'
    
    product_id = fields.Many2one('product.product', string='Product')
    return_order_id = fields.Many2one('kits.return.ordered.items', string='Return Order')
    scrap_order_id = fields.Many2one('kits.return.ordered.items', string='Return Order')
    product_qty = fields.Integer('Quantity',default="1")
    return_type = fields.Selection([
        ('return', 'Return'),('scrap', 'Scrap')
    ], string='Return Type')
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        for record in self:
            if not record.return_type:
                record.return_type = 'scrap' if record.scrap_order_id else 'return'
            if record.product_id:
                if record.return_type == 'return':
                    if not record.return_order_id.return_line_ids.filtered(lambda line : line.product_id.id == record.product_id.id  and not line.id!= record.id):
                        self._cr.execute(('SELECT id FROM sale_order_line WHERE product_id = %s AND order_id IN %s ORDER BY order_id'%(record.product_id.id,tuple(record.return_order_id.order_ids.ids))).replace(',)', ')'))
                        line_ids = self._cr.fetchall()
                        line_ids = [sol_id[0] for sol_id in line_ids ]
                        if not line_ids:
                            raise UserError(_('Product not found in selected order.'))
                    else:
                        raise UserError(_('Duplicate product found.'))
                    
                if record.return_type == 'scrap':
                    if not record.scrap_order_id.scrap_line_ids.filtered(lambda line : line.product_id.id == record.product_id.id  and not line.id!= record.id):
                        self._cr.execute(('SELECT id FROM sale_order_line WHERE product_id = %s AND order_id IN %s ORDER BY order_id'%(record.product_id.id,tuple(record.scrap_order_id.order_ids.ids))).replace(',)', ')'))
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
                if record.return_type == 'return':
                    self._cr.execute(('SELECT id FROM sale_order_line WHERE product_id = %s AND order_id IN %s ORDER BY order_id'%(record.product_id.id,tuple(record.return_order_id.order_ids.ids))).replace(',)', ')'))
                    line_ids = self._cr.fetchall()
                    line_ids = [sol_id[0] for sol_id in line_ids ]
                    line_ids = self.env['sale.order.line'].browse(line_ids)
                    if sum(line_ids.mapped('product_qty')) < record.product_qty:
                        raise UserError(_('Product quantity more than delivered quantity.'))
                if record.return_type == 'scrap':
                    self._cr.execute(('SELECT id FROM sale_order_line WHERE product_id = %s AND order_id IN %s ORDER BY order_id'%(record.product_id.id,tuple(record.scrap_order_id.order_ids.ids))).replace(',)', ')'))
                    line_ids = self._cr.fetchall()
                    line_ids = [sol_id[0] for sol_id in line_ids ]
                    line_ids = self.env['sale.order.line'].browse(line_ids)
                    if sum(line_ids.mapped('product_qty')) < record.product_qty:
                        raise UserError(_('Product quantity more than delivered quantity.'))
                    
class kits_return_ordered_items(models.Model):
    _name = 'kits.return.ordered.items'
    _description = 'Return Orderded Items'
    
    name = fields.Char('Name')
    order_ids = fields.Many2many('sale.order', string='Order')
    partner_id = fields.Many2one('res.partner', string='Customer')
    state = fields.Selection([
        ('draft', 'Draft'),('in_scanning', 'In Scanning'),('return', 'Return'),('cancel', 'Cancel'),
    ], string='State',default='draft')
    return_line_ids = fields.One2many('kits.return.ordered.items.line', 'return_order_id', string='Return Order Line')
    scrap_line_ids = fields.One2many('kits.return.ordered.items.line', 'scrap_order_id', string='Scrap Order Line')
    delivery_count = fields.Integer(string='Return Orders', compute='_compute_picking_ids')    

    def _compute_picking_ids(self):
        picking_obj = self.env['stock.picking']
        for record in self:
            record.delivery_count = len(picking_obj.search([('return_order_id','=',record.id)]))
 
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('kits.return.ordered.items.sequence')
        return super().create(vals_list)
    
    def action_reset_to_draft(self):
        for record in self:
            record.state = 'draft'

    def action_cancel(self):
        picking_obj = self.env['stock.picking']
        for record in self:
            picking_ids = picking_obj.search([('return_order_id','=',record.id),('state','!=','cancel')])
            for stock_picking in picking_ids:
                stock_picking.state = 'cancel'
                stock_picking.move_lines.stock_quant_update_spt()
            record.state = 'cancel'


    def action_return(self):
        for record in self:
            move_line_list = []
            for line in self.return_line_ids:
                move_line_list.append((0,0,{
                    'name': self.name or '' +':'+ line.product_id.variant_name or '',
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': self.env.ref('stock.stock_location_customers').id,
                    'location_dest_id': self.env.ref('stock.stock_location_stock').id,
                    'company_id': self.env.company.id,
                    'quantity_done' : line.product_qty,
                    'reference' : 'Return' +':'+ self.name or '',
                    'return_order_line_id' : line.id
                }))
                
            for line in self.scrap_line_ids:
                move_line_list.append((0,0,{
                    'name': self.name or '' +':'+ line.product_id.variant_name or '',
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.product_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': self.env.ref('stock.stock_location_customers').id,
                    'location_dest_id': self.env.ref('tzc_sales_customization_spt.kits_return_scrap_location').id,
                    'company_id': self.env.company.id,
                    'quantity_done' : line.product_qty,
                    'reference' : 'Scrap' +':'+ self.name or '',
                    'return_order_line_id' : line.id
                }))
            picking_type_id =  self.env['stock.picking.type'].search([('code','=','incoming'),('company_id','=',self.env.user.company_id.id)],limit=1)
            picking_id = self.env['stock.picking'].create({
                'partner_id' : self.partner_id.id,
                'picking_type_id' : picking_type_id.id,
                'location_id' : self.partner_id.property_stock_customer.id,
                'location_dest_id' : picking_type_id.default_location_dest_id.id,
                'origin' : self.name,
                'return_order_id' : self.id,
                'company_id': self.env.company.id,
                'move_ids_without_package' : move_line_list,
                'carrier_id' :False,
                'recipient_id' :False,
            })
            picking_id.action_confirm()
            picking_id.with_context(is_return_order = True).button_validate()
            picking_id.state = 'done'
            record.state = 'return'


    def action_open_scan_items(self):
        if not self.order_ids:
            raise UserError(_('Order not found please select order.'))
        self.state = 'in_scanning'
        wizard_id = self.env['kits.scan.return.items.wizard'].create({'return_order_id':self.id})
        return {
            'name':_("Scan Return Items"),
            'type':'ir.actions.act_window',
            'res_model':"kits.scan.return.items.wizard",
            'view_mode':'form',
            'res_id' : wizard_id.id,
            'target':'new',
        }

    def action_view_delivery(self):
        self.ensure_one()
        pickings = self.env['stock.picking'].search([('return_order_id','=',self.id)])
        action = {
            'name':_("Return Orders"),
            'type':'ir.actions.act_window',
            'res_model':"stock.picking",
            'view_mode':'form',
            'target':'self',
        }
        if len(pickings) == 1:
            action['res_id']=pickings.id
        else:
            action['view_mode'] = 'tree,form'
            action['domain'] = [('id','in',pickings.ids)]
        return  action
