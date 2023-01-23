from odoo import models,fields,api,_
from odoo.exceptions import UserError

class kits_wizard_return_line(models.TransientModel):
    _name = 'kits.wizard.return.picking.line'
    _description = 'Kits Return wizard picking lines'

    wizard_id = fields.Many2one('kits.wizard.return.picking','Wizard')
    product_id = fields.Many2one('product.product','Product')
    barcode = fields.Char('Barcode')
    product_qty = fields.Integer('Qty')

class kits_wizard_return_picking(models.TransientModel):
    _name = 'kits.wizard.return.picking'
    _inherit = ["barcodes.barcode_events_mixin"]
    _description = 'Return Picking Wizard'


    def _get_default_scrap_location_id(self):
        company_id = self.env.context.get('default_company_id') or self.env.company.id
        return self.env['stock.location'].search([('scrap_location', '=', True), ('company_id', 'in', [company_id, False])], limit=1).id

    def _default_get_total_credits(self):
        picking = self.env['stock.picking'].browse(self._context.get('default_picking_id'))
        sale = picking.sale_id
        amount = sum(self.env['sale.order'].browse(self._context.get('default_sale_id')).kits_credit_payment_ids.mapped('amount'))
        return amount
    
    def _get_default_order_amount(self):
        picking = self.env['stock.picking'].browse(self._context.get('default_picking_id'))
        order_amount = picking.sale_id.amount_total
        return order_amount
    
    picking_id = fields.Many2one('stock.picking','Picking')
    total_qty = fields.Integer('Delivered Qty')
    return_qty = fields.Integer(compute="_compute_return_qty")
    return_type = fields.Selection([('to_scrap','To Scrap'),('return','Return')],default="return",string="Operation")
    line_ids = fields.One2many('kits.wizard.return.picking.line','wizard_id','Remove Lines')
    scrap_location_id = fields.Many2one('stock.location', 'Scrap Location', default=_get_default_scrap_location_id,required=True,)
    create_credit_note = fields.Boolean('Create Credit Note ?')
    order_amount = fields.Float('Order Amount',default=_get_default_order_amount,readonly=True,store=True)
    credit_amount = fields.Float('Credit Amount')
    total_credits = fields.Float('Total Credits',default=_default_get_total_credits,readonly=True,store=True)

    @api.depends('line_ids','line_ids.product_qty')
    def _compute_return_qty(self):
        total = 0
        for line in self.line_ids:
            total += line.product_qty
        self.return_qty = total
    
    def on_barcode_scanned(self,barcode):
        self._add_barcode(barcode)

    def _add_barcode(self,barcode):
        if self.picking_id:
            search_lines = self.line_ids.filtered(lambda ol: ol.product_id.barcode == barcode)
            move_ids = self.picking_id.move_ids_without_package.filtered(lambda x: x.product_id.barcode == barcode and x.scrapped == False)
            search_product = self.env["product.product"].search([("barcode","=",barcode)], limit = 1)
            return_picking = self.picking_id.sale_id.picking_ids.filtered(lambda x: not x.product_returned and x.kits_return_picking and x.state == 'done')
            returned_qty = sum(return_picking.move_ids_without_package.filtered(lambda x: x.product_id.barcode == barcode).mapped('quantity_done'))
            scraped_qty = sum(self.env['stock.scrap'].search([('picking_id','=',self.picking_id.id),('product_id','=',search_product.id)]).mapped('scrap_qty'))
            if search_product and search_product.id:
                if move_ids and move_ids.ids:
                    total = 0
                    for move in move_ids:
                        total += move.quantity_done
                    total = total - returned_qty - scraped_qty
                    if search_lines:
                        if search_lines.product_qty < total:
                            search_lines.product_qty += 1
                        else:
                            raise UserError(_("Scanned Product's delivered quantity is not enough."))
                    else:
                        if total <= 0:
                            raise UserError(_("Scanned product's quntity is Zero."))
                        else:
                            vals = {
                                'product_id': search_product.id,
                                'barcode':barcode,
                                'product_qty': 1,
                            }
                            new_line_ids = self.line_ids.new(vals)                                                                    
                            self.line_ids += new_line_ids
                else:
                    raise UserError(_("Scanned Product can not be found in order."))
            else:
                raise UserError(_("Scanned Barcode does not exist. Try manual entry."))
        else:
            raise UserError(_("Please select package first."))

    def action_process_to_return(self):
        if not self.line_ids:
            raise UserError(_('No products selected.'))
        picking_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        return_lines = {}
        return_dest_location_id = self.picking_id.location_id
        return_location_id = self.picking_id.location_dest_id
        picking_type_id = self.picking_id.picking_type_id.return_picking_type_id.id
        picking_vals = {
            'location_id':return_location_id.id,
            'location_dest_id':return_dest_location_id.id,
            'picking_type_id':picking_type_id,
            'move_type':'direct',
            'sale_id':self.picking_id.sale_id.id,
            'is_return_picking':True,
            'shipping_id':self.picking_id.shipping_id.id,
            'origin':self.picking_id.name or self.picking_id.origin or self.picking_id.sale_id.name or '',
            'user_id':self.env.user.id,
            'state':'draft',
        }
        return_picking_id = False
        if self.line_ids:
            return_picking_id = picking_obj.create(picking_vals)
            
        for line in self.line_ids:
            move_ids = self.picking_id.move_ids_without_package.filtered(lambda x: x.product_id.id == line.product_id.id and x.scrapped == False)
            if not move_ids:
                raise UserError(_('Product %s not found in order.'%(line.product_id.name)))
            for move in move_ids:
                stock_move = self._get_stock_move_vals(move,line.product_qty)
                stock_move.update({'picking_id':return_picking_id.id})
                if stock_move['product_id'] not in return_lines.keys():
                    return_lines[stock_move['product_id']] = stock_move
                else:
                    return_lines[stock_move['product_id']]['product_uom_qty'] = return_lines[stock_move['product_id']]['product_uom_qty']+stock_move['product_uom_qty']
            if move_ids:
                [self.env['stock.move'].create(return_lines[m]) for m in return_lines]
        self.picking_id.product_returned = True if self.line_ids and return_picking_id else False
        if self.create_credit_note and self.line_ids:
            res = self.env['account.payment'].sudo().kits_create_credit_payment(self.picking_id.partner_id,self.picking_id.sale_id,self.credit_amount)
            if res:
                self.picking_id.sale_id.kits_credit_payment_ids = [(6,0,self.picking_id.sale_id.kits_credit_payment_ids.ids+res.ids)]
                self.picking_id.credit_note_created = True

    def action_process_to_scrap(self):
        if not self.line_ids:
            raise UserError(_('No products selected.'))
        company_id = self.env.companies[0].id
        scrap_location_id = self.env['stock.location'].search([('scrap_location', '=', True), ('company_id', 'in', [company_id, False])], limit=1).id
        for line in self.line_ids:
            moves = self.picking_id.move_ids_without_package.filtered(lambda x: x.product_id == line.product_id and x.scrapped == False)
            if not moves:
                raise UserError(_('Product %s not found in order.'%(line.product_id.name)))
            product_move = moves[0] if len(moves) > 0 else moves
            scrap = self.env['stock.scrap'].create({'picking_id':product_move.picking_id.id,'company_id':company_id,'product_id':line.product_id.id,'scrap_qty':line.product_qty,'product_uom_id':product_move.product_uom.id,'scrap_location_id':scrap_location_id,'location_id':product_move.location_dest_id.id,'name':product_move.picking_id.name or product_move.origin or product_move.sale_line_id.order_id.name,'move_id':product_move.id})
            scrap.action_validate()
        self.picking_id.product_scraped = True if self.line_ids else False
        if self.create_credit_note and self.line_ids:
            res = self.env['account.payment'].sudo().kits_create_credit_payment(self.picking_id.partner_id,self.picking_id.sale_id,self.credit_amount)
            if res:
                self.picking_id.sale_id.kits_credit_payment_ids = [(6,0,self.picking_id.sale_id.kits_credit_payment_ids.ids+res.ids)]
                self.picking_id.credit_note_created = True

    def _get_stock_move_vals(self,move,return_qty):
        if not return_qty:
            raise UserError(_('Return quantity should be atleast 1.'))
        stock_move_vals = {
            'company_id':move.company_id.id,
            'date':fields.Date.today(),
            'location_id':move.location_dest_id.id,
            'location_dest_id':move.location_id.id,
            'name':move.name or move.origin or move.picking_id.name or '',
            'procure_method':'make_to_order',
            'product_id':move.product_id.id,
            'product_uom':move.product_uom.id,
            'product_uom_qty':return_qty,
            'quantity_done':return_qty,
        }
        return stock_move_vals
