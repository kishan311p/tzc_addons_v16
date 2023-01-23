from odoo import models,fields,api,_
from odoo.exceptions import UserError
from datetime import datetime

class remove_product_spt(models.TransientModel):
    _name="remove.product.spt"
    _inherit = ["barcodes.barcode_events_mixin"]
    _description = 'Remove Product'

    line_ids = fields.One2many("remove.product.qty.spt",'product_remove_line_id',string="Order Lines")
    # line_ids = fields.Many2many("remove.product.qty.spt",string="Order Lines")
    product_qty_count = fields.Integer("Total Qty",compute="_compute_product_qty")
    partner_id = fields.Many2one("res.partner","Customer")

    def _get_domain(self):
        product_ids = False
        if self._context and self._context.get('default_sale_id'):
            order_id = self.env['sale.order'].browse([self._context.get('default_sale_id')])
            if order_id:
                product_ids = self.env['product.product'].search([('id','in',order_id.order_line.product_id.ids)])

        return [('id','in',product_ids.ids)] if product_ids else []

    product_id = fields.Many2one("product.product","Manual",domain=_get_domain)
    sale_id = fields.Many2one("sale.order","Order")
    qty = fields.Integer(default=1)

    @api.depends('line_ids','line_ids.product_qty')
    def _compute_product_qty(self):
        for record in self:
            total = 0
            for line in self.line_ids:
                total += line.product_qty
            record.product_qty_count = total

    def _add_product(self,barcode):
        sequence = 0
        # self.line_ids.update({
        #         'sequence': 0,
        #         })   
        search_lines = self.line_ids.filtered(lambda ol: ol.product_id.barcode == barcode)
        sol_ids = self.sale_id.order_line.filtered(lambda x: x.product_id.barcode == barcode)
        search_product = self.env["product.product"].search([("barcode","=",barcode)], limit = 1)
        if search_product and search_product.id:
            if sol_ids and sol_ids.ids:
                total = 0
                for sol in sol_ids:
                    total += sol.product_uom_qty
                if search_lines:
                    if search_lines.product_qty < total:
                        search_lines.product_qty += 1
                        for line in self.line_ids:
                            line.sequence += 1
                        if self.line_ids:
                            search_lines.sequence = min(self.line_ids.mapped('sequence'))-1
                        else:
                            search_lines.sequence = sequence
                        # search_lines.sequence += sequence
                    else:
                        raise UserError(_("Scanned Product's quantity is not enough."))
                else:
                    if sol_ids and sol_ids.ids:
                        if total == 0:
                            raise UserError(_("Scanned product's quntity is Zero."))
                        else:
                            vals = {
                                'product_id': search_product.id,
                                'product_qty': 1,
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
                raise UserError(_("Scanned Product can not be found in order."))
        else:
            raise UserError(_("Scanned Barcode does not exist. Try manual entry."))
            

    def on_barcode_scanned(self, barcode):
        self._add_product(barcode)

    def action_process(self):
        sol_obj = self.env['sale.order.line']
        messages =[]
        flag = False
        if self.line_ids and self.line_ids.ids:
            for line in self.line_ids:
                if line.product_id and line.product_id.id:
                    sol_ids = sol_obj.search([('order_id','=',self.sale_id.id),('product_id','=',line.product_id.id)])
                    qty = line.product_qty
                    if sol_ids and sol_ids.ids:
                        for i in range(0,len(sol_ids)):
                            if qty > 0:
                                qty = qty - sol_ids[i].product_uom_qty
                                sol_ids[i].write({"product_uom_qty":0 if qty >= 0 else sol_ids[i].product_uom_qty - abs(sol_ids[i].product_uom_qty + qty)})
                                sol_ids.order_id.write({'updated_by':self.env.user.id,'updated_on':datetime.now()})
                            else:
                                continue
                    else:
                        messages.append("Order line not found for product %s."%(line.product_id.display_name))
                        flag = True
                else:
                    raise UserError(_("No product found in line. Please select atleast one product."))
        if flag:
            raise UserError('\n'.join(messages))
        self.sale_id.order_line.filtered(lambda line: line.product_uom_qty in [0.0,000]).unlink()

    def action_edit_product(self):
        self.ensure_one()
        sequence = 0
        if self.product_id and self.qty:
            search_line = self.line_ids.filtered(lambda x:x.product_id.id == self.product_id.id)
            line_ids = self.sale_id.order_line.filtered(lambda x: x.product_id.barcode == self.product_id.barcode)
            # self.line_ids.update({'sequence':0})
            if line_ids and line_ids.ids:
                if search_line:
                    if self.qty <= line_ids.product_uom_qty:
                        # search_line.sequence = -1
                        search_line.product_qty = self.qty
                        for line in self.line_ids:
                            line.sequence += 1
                        if self.line_ids:
                            search_line.sequence = min(self.line_ids.mapped('sequence'))-1
                        else:
                            search_line.sequence = sequence
                    else:
                        raise UserError (_("A scanned product's quantity is more than the order quantity."))
                else:
                    raise UserError ('Product not found.')
            else:
                raise UserError ('Product not found.')

            self.product_id = False
            self.qty = 1

            return {
                    'name': 'Remove Items',
                    'view_mode': 'form',
                    'target': 'new',
                    'res_id':self.id,
                    'res_model': 'remove.product.spt',
                    'type': 'ir.actions.act_window',
                }
        else:
            if not self.product_id or not self.qty:
                raise UserError ('The product and quantity must be added.') 

    def action_remove_product(self):
        self.ensure_one()
        sequence = 0
        if self.product_id and self.qty:
            search_line = self.line_ids.filtered(lambda x:x.product_id.id == self.product_id.id)
            line_ids = self.sale_id.order_line.filtered(lambda x: x.product_id.barcode == self.product_id.barcode)
            total = 0
            for line in line_ids:
                total += line.product_uom_qty
            # self.line_ids.update({'sequence':0})
            if line_ids and line_ids.ids:
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
                        raise UserError (_("A scanned product's quantity is more than the order quantity."))
                else:
                    if total == 0:
                        raise UserError(_("Scanned product's quantity is Zero!"))
                    else:
                        if total < self.qty:
                            raise UserError (_("A scanned product's quantity is more than the order quantity."))
                        else:
                            line_id = self.env['remove.product.qty.spt'].create({'product_id':self.product_id.id,'product_qty':self.qty,'sequence':-1,'product_remove_line_id':self.id})
                            if self.line_ids:
                                line_id.sequence = sequence - len(self.line_ids)+1
                            else:
                                line_id.sequence = sequence

            self.product_id = False
            self.qty = 1

            # if search_line:
            #     search_line.sequence = -1
            #     search_line.product_qty += 1
            # else:
            #     self.env['remove.product.qty.spt'].create({'product_id':self.product_id.id,'product_qty':1,'sequence':-1,'product_remove_line_id':self.id})
        
            return {
                    'name': 'Remove Items',
                    'view_mode': 'form',
                    'target': 'new',
                    'res_id':self.id,
                    'res_model': 'remove.product.spt',
                    'type': 'ir.actions.act_window',
                }
        else:
            if not self.product_id or not self.qty:
                raise UserError ('The product and quantity must be added.') 
    def _add_product(self,barcode):
        sequence = 0
        # self.line_ids.update({
        #         'sequence': 0,
        #         })   
        search_lines = self.line_ids.filtered(lambda ol: ol.product_id.barcode == barcode)
        sol_ids = self.sale_id.order_line.filtered(lambda x: x.product_id.barcode == barcode)
        search_product = self.env["product.product"].search([("barcode","=",barcode)], limit = 1)
        if search_product and search_product.id:
            if sol_ids and sol_ids.ids:
                sol_ids = sol_ids.filtered(lambda x: not x.package_id)
                total = 0
                for sol in sol_ids:
                    total += sol.product_uom_qty
                if search_lines:
                    if search_lines.product_qty < total:
                        search_lines.product_qty += 1
                        for line in self.line_ids:
                            line.sequence += 1
                        if self.line_ids:
                            search_lines.sequence = min(self.line_ids.mapped('sequence'))-1
                        else:
                            search_lines.sequence = sequence
                        # search_lines.sequence += sequence
                    else:
                        raise UserError(_("Scanned Product's quantity is not enough."))
                else:
                    if sol_ids and sol_ids.ids:
                        if total == 0:
                            raise UserError(_("Scanned product's quntity is Zero."))
                        else:
                            vals = {
                                'product_id': search_product.id,
                                'product_qty': 1,
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
                    # raise error for packaged product
                    else:
                        raise UserError(_("Scanned product without package can not be found in order."))
            else:
                raise UserError(_("Scanned Product can not be found in order."))
        else:
            raise UserError(_("Scanned Barcode does not exist. Try manual entry."))
            

    def on_barcode_scanned(self, barcode):
        self._add_product(barcode)

    def action_process(self):
        sol_obj = self.env['sale.order.line']
        messages =[]
        flag = False
        if self.line_ids and self.line_ids.ids:
            for line in self.line_ids:
                if line.product_id and line.product_id.id:
                    sol_ids = sol_obj.search([('order_id','=',self.sale_id.id),('product_id','=',line.product_id.id)])
                    qty = line.product_qty
                    if sol_ids and sol_ids.ids:
                        for i in range(0,len(sol_ids)):
                            if qty > 0:
                                qty = qty - sol_ids[i].product_uom_qty
                                sol_ids[i].write({"product_uom_qty":0 if qty >= 0 else sol_ids[i].product_uom_qty - abs(sol_ids[i].product_uom_qty + qty)})
                                sol_ids.order_id.write({'updated_by':self.env.user.id,'updated_on':datetime.now()})
                            else:
                                continue
                    else:
                        messages.append("Order line not found for product %s."%(line.product_id.display_name))
                        flag = True
                else:
                    raise UserError(_("No product found in line. Please select atleast one product."))
        if flag:
            raise UserError('\n'.join(messages))
        self.sale_id.order_line.filtered(lambda line: line.product_uom_qty in [0.0,000]).unlink()

class remove_product_qty_spt(models.TransientModel):
    _name = "remove.product.qty.spt"
    _order = "sequence"
    _description = 'Remove Product Qty'

    def _get_domain(self):
        product_ids = False
        if self._context and self._context.get('default_sale_id'):
            order_id = self.env['sale.order'].browse([self._context.get('default_sale_id')])
            if order_id:
                product_ids = self.env['product.product'].search([('id','in',order_id.order_line.product_id.ids)])

        return [('id','in',product_ids.ids)] if product_ids else []

    product_id = fields.Many2one("product.product","Product",domain=_get_domain)
    product_qty = fields.Integer("Qty",default=1)
    product_remove_line_id = fields.Many2one('remove.product.spt','Wizard Id')
    sequence = fields.Integer('Sequence',index=True)

    # def action_product_selection(self):
    #     self.ensure_one()
    #     if self.product_remove_line_id:
    #         self.product_remove_line_id.product_id = self.product_id.id

    #         return {
    #                 'name': 'Remove Items',
    #                 'view_mode': 'form',
    #                 'target': 'new',
    #                 'res_id':self.product_remove_line_id.id,
    #                 'res_model': 'remove.product.spt',
    #                 'type': 'ir.actions.act_window',
    #                 }
