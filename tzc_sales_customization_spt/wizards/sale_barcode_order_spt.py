from odoo import models, fields, api, _
from odoo.exceptions import Warning,UserError

class sale_barcode_order_spt(models.TransientModel):
    _name = "sale.barcode.order.spt"
    _inherit = ["barcodes.barcode_events_mixin"]
    _order = 'id'
    _description = 'Sale Order Barcode'

    line_ids = fields.One2many('sale.barcode.order.line.spt','barcode_order_id',string='Barcode Order Lines')
    # line_ids = fields.Many2many('sale.barcode.order.line.spt',string='Barcode Order Lines')
    product_qty_count = fields.Integer('Total Qty',compute="_compute_product_qty")
    product_id = fields.Many2one('product.product','Manual')
    qty = fields.Integer(default=1)
    partner_id = fields.Many2one('res.partner','Customer')
    sale_id = fields.Many2one('sale.order','Order')
    
    @api.depends('line_ids','line_ids.product_qty')
    def _compute_product_qty(self):
        for record in self:
            total_qty = 0.0
            for line in record.line_ids:
                total_qty += line.product_qty
            record.product_qty_count = total_qty
      
    def action_process(self):
        self.ensure_one()
        sale_order_line_obj = self.env['sale.order.line']
        # line_list = []
        # product_list = []

        # for data_line in self.line_ids:
        #     if data_line.product_id.id in product_list:
        #         line_id = list(filter(lambda line: line.product_id.id == data_line.product_id.id,line_list))[0]
        #         line_id.product_qty = data_line.product_qty + line_id.product_qty
        #     else:
        #         product_list.append(data_line.product_id.id)
        #         line_list.append(data_line)
                
        product_prices = self.env['kits.b2b.multi.currency.mapping'].get_product_price(self.partner_id.id,[i.product_id.id for i in self.line_ids])
        for line in self.line_ids:
            order_line_id = self.sale_id.order_line.filtered(lambda x:x.product_id.id == line.product_id.id)
            if order_line_id:
                order_line_id.product_uom_qty += line.product_qty
            else:
                product_data = product_prices.get(line.product_id.id)
                extra_pricing = line.product_id.inflation_special_discount(self.sale_id.partner_id.country_id.ids,bypass_flag=self.sale_id.partner_id.b2b_pricelist_id.is_pricelist_excluded)
                price_unit = product_data.get('price')
                unit_discount_price = product_data.get('discounted_unit_price')

                if extra_pricing.get('is_inflation'):
                    price_unit = price_unit+(price_unit*extra_pricing.get('inflation_rate') /100)
                    unit_discount_price = unit_discount_price+(unit_discount_price*extra_pricing.get('inflation_rate') /100)
                if extra_pricing.get('is_special_discount'):
                    unit_discount_price = (unit_discount_price - unit_discount_price * extra_pricing.get('special_disc_rate') / 100)
                
                fix_discount_price = price_unit - unit_discount_price
                discount = (fix_discount_price*100/price_unit)
                
                vals = {
                    'product_id' : line.product_id.id,
                    'product_uom_qty' : line.product_qty,
                    'order_id' : self.sale_id.id,
                    'price_unit': round(price_unit,2),
                    'sale_type': product_data.get('sale_type'),
                    'unit_discount_price':round(unit_discount_price,2),
                    'fix_discount_price':round(fix_discount_price,2),
                    'discount':round(discount,2),
                }

                sale_order_line = sale_order_line_obj.create(vals)
                sale_order_line.product_id_change()
                sale_order_line._onchange_fix_discount_price_spt()
            
            # Adding case product.
            if line.product_id.sale_type != 'clearance':
                case_product_id = self.env['product.product'].browse(line.product_id.id).case_product_id.id
                case_order_line_id = self.sale_id.order_line.filtered(lambda x:x.product_id.id == case_product_id and x.is_included_case==True)
                if case_order_line_id:
                    if self.sale_id.state in ['draft','sent','received']:
                        qty = sum(self.sale_id.non_case_order_line.filtered(lambda x: x.product_id.case_product_id.id==case_product_id).mapped('product_uom_qty'))
                        case_order_line_id.product_uom_qty = qty
                    else:
                        case_order_line_id.product_uom_qty += line.product_qty
                    pass
                else:
                    case_product_price = self.env['kits.b2b.multi.currency.mapping'].get_product_price(self.partner_id.id,[case_product_id])
                    if case_product_id:
                        case_vals = {
                            'product_id' : case_product_id,
                            'product_uom_qty' : line.product_qty,
                            'order_id' : self.sale_id.id,
                            'price_unit': 0.00,
                            # 'sale_type': case_product_price.get(case_product_id).get('sale_type'),
                            'unit_discount_price':0.00,
                            'is_included_case':True
                        }
                        # case_vals = {
                        #     'product_id' : case_product_id,
                        #     'product_uom_qty' : line.product_qty,
                        #     'order_id' : self.sale_id.id,
                        #     'price_unit': round(case_product_price.get(case_product_id).get('price'),2),
                        #     'sale_type': case_product_price.get(case_product_id).get('sale_type'),
                        #     'unit_discount_price':round(case_product_price.get(case_product_id).get('sale_type_price'),2),
                        #     'is_included_case':True
                        # }
                        sale_case_order_line = sale_order_line_obj.create(case_vals)
                        sale_case_order_line.product_id_change()
                        # sale_case_order_line._onchange_fix_discount_price_spt()
        # self.sale_id.merge_order_lines()
        self.sale_id._amount_all()
        
    def _add_product(self, barcode):
        sequence = 0
        # self.line_ids.update({
        #         'sequence': 0,
        #         })   
                
        search_lines = self.line_ids.filtered(lambda ol: ol.product_id.barcode == barcode)
                
        if search_lines:
            search_lines.product_qty += 1
            for line in self.line_ids:
                line.sequence += 1
            if self.line_ids:
                search_lines.sequence = min(self.line_ids.mapped('sequence'))-1
            else:
                search_lines.sequence = sequence
            # search_lines.sequence += sequence
        else:
            search_product = self.env["product.product"].search([("barcode","=",barcode)], limit = 1)
            if search_product:
                vals = {
                    'product_id': search_product.id,
                    'product_qty': 1,
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
            else:                   
                raise UserError(_("Scanned Barcode does not exist. Try manual entry."))

    def on_barcode_scanned(self, barcode):
        self._add_product(barcode)

    def action_edit_product(self):
        self.ensure_one()
        sequence = 0
        if self.product_id and self.qty:
            search_line = self.line_ids.filtered(lambda x:x.product_id.id == self.product_id.id)
            # self.line_ids.update({'sequence':0})
            if search_line:
                # search_line.sequence = -1
                for line in self.line_ids:
                    line.sequence += 1
                if self.line_ids:
                    search_line.sequence = min(self.line_ids.mapped('sequence'))-1
                else:
                    search_line.sequence = sequence
                search_line.product_id = self.product_id.id
                search_line.product_qty = self.qty
            else:
                raise UserError('Product not found.')
            
            self.product_id = False
            self.qty = 1
        
            return {
                'name': 'Scan Order',
                'view_mode': 'form',
                'target': 'new',
                'res_id':self.id,
                'res_model': 'sale.barcode.order.spt',
                'type': 'ir.actions.act_window',
                }
        else:
            if not self.product_id or not self.qty:
                raise UserError ('The product and quantity must be added.')

    def action_add_product(self):
        self.ensure_one()
        sequence = 0
        if self.product_id and self.qty:
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
            else:
                line_id = self.env['sale.barcode.order.line.spt'].create({'product_id':self.product_id.id,'product_qty':self.qty,'sequence':-1,'barcode_order_id':self.id})
                if self.line_ids:
                    line_id.sequence = sequence - len(self.line_ids)+1
                else:
                    line_id.sequence = sequence
            
            self.product_id = False
            self.qty = 1
        
            return {
                'name': 'Scan Order',
                'view_mode': 'form',
                'target': 'new',
                'res_id':self.id,
                'res_model': 'sale.barcode.order.spt',
                'type': 'ir.actions.act_window',
                }
        else:
            if not self.product_id or not self.qty:
                raise UserError ('The product and quantity must be added.')

class sale_barcode_order_line_spt(models.TransientModel):
    _name = "sale.barcode.order.line.spt"
    _order = 'sequence'
    _description = "Sale Order Barcode Line"
    
    product_id = fields.Many2one('product.product','Product')
    product_qty = fields.Integer('Qty',default=1)
    barcode_order_id = fields.Many2one('sale.barcode.order.spt','Barcode Order')
    sequence = fields.Integer(string='Sequence',index=True)

    def action_product_selection(self):
        self.ensure_one()
        if self.barcode_order_id:
            self.barcode_order_id.product_id = self.product_id.id

            return {
                    'name': 'Scan Order',
                    'view_mode': 'form',
                    'target': 'new',
                    'res_id':self.barcode_order_id.id,
                    'res_model': 'sale.barcode.order.spt',
                    'type': 'ir.actions.act_window',
                    }
