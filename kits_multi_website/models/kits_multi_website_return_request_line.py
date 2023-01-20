from odoo import api, fields, models, _
from odoo.exceptions import UserError

class kits_multi_website_return_request_line(models.Model):
    _name = "kits.multi.website.return.request.line"
    _description = "Kits Multi Website Return Request Line"
    _rec_name = "product_id"
    product_id = fields.Many2one("product.product", "Product")
    power_type_id = fields.Many2one('kits.multi.website.power.type',string="Power Type",domain="[('website_id','=',website_id)]")
    glass_type_id = fields.Many2one("kits.multi.website.glass.type","Glass Type")
    quantity = fields.Float("Quantity")
    return_request_id = fields.Many2one("kits.multi.website.return.request", "Return Request")
    sale_order_line_id = fields.Many2one("kits.multi.website.sale.order.line", "Sale Order Line")
    website_id = fields.Many2one("kits.b2c.website", "Website",related='sale_order_line_id.website_id',store=True)
    amount = fields.Float('Refund Amount')
    requested_date = fields.Datetime("Requested Date")
    approved_date = fields.Datetime("Approved Date")
    pickup_date = fields.Datetime("Pickup Date")
    received_date = fields.Datetime("Received Date")
    examined_date = fields.Datetime("Examined Date")
    returned_date = fields.Datetime("Returned Date")
    refunded_date = fields.Datetime("Refunded Date")
    scrapped_date = fields.Datetime("Scrapped Date")
    rejected_date = fields.Datetime("Rejected Date")
    description = fields.Text("Description")
    remark = fields.Text('Remark')
    return_request_reason_id = fields.Many2one("kits.multi.website.return.request.reason","Reason ")
    flag_show = fields.Boolean(compute='_compute_flag_show', string='Other reason')
    state = fields.Selection([('draft','In Process'), ('pick_up','Pick Up'), ('receive','Received'), ('examine','Examined'), ('approve','Approved'), ('rejected', 'Rejected'), ('return','Return'), ('scrap','Scrap'),('cancel','Cancelled')], default='draft')
    is_refund = fields.Boolean('Refund')
    
    @api.depends('return_request_reason_id')
    def _compute_flag_show(self):
        for record in self:
            record.flag_show = False
            if record.return_request_reason_id and 'other' in record.return_request_reason_id.name.lower():
                record.flag_show = True

    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_return_request_line, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res

    @api.model
    def create(self, vals):
        if 'quantity' in vals.keys() and vals.get('quantity') == 0:
            raise UserError("Quantity cannot be 0!")
        if ('quantity' in vals.keys() and vals.get('quantity')) and ('sale_order_line_id' in vals.keys() and vals.get('sale_order_line_id')):
            sol_id = self.env['kits.multi.website.sale.order.line'].browse(vals.get('sale_order_line_id'))
            if vals.get('quantity') > sol_id.quantity:
                raise UserError(f"You cannot return more than ordered quantity of {sol_id.product_id.display_name}!") 
        return super(kits_multi_website_return_request_line, self).create(vals)

    def write(self, vals):
        if 'quantity' in vals.keys() and vals.get('quantity') == 0:
            raise UserError("Quantity cannot be 0!")
        if 'quantity' in vals.keys() and vals.get('quantity'):
            if self.sale_order_line_id and vals.get('quantity') > self.sale_order_line_id.quantity:
                raise UserError(f"You cannot return more than ordered quantity of {self.sale_order_line_id.product_id.display_name}!")
        return super(kits_multi_website_return_request_line, self).write(vals)
        
         

    @api.constrains('state')
    def _constrains_state(self):
        for record in self:
            if record.return_request_id :
                if 'draft' not in record.return_request_id.return_request_line_ids.mapped('state'):
                    record.return_request_id._origin.state = 'in_progress'
            state = record.state
            if state == 'approve':
                record.write({'approved_date' :fields.Datetime.now()})
                record.sale_order_line_id.write({'return_approved_date': fields.Datetime.now()})
            elif state == 'pick_up':
                record.write({'pickup_date' : fields.Datetime.now()})
                record.sale_order_line_id.write({'return_pickup_date' :  fields.Datetime.now()})
            elif state == 'receive':
                record.write({'received_date' : fields.Datetime.now()})
                record.sale_order_line_id.write({'return_received_date' :  fields.Datetime.now()})
            elif state == 'examine':
                record.write({'examined_date' : fields.Datetime.now()})
                record.sale_order_line_id.write({'return_examined_date' :  fields.Datetime.now()})
            elif state == 'return':
                record.write({'returned_date' : fields.Datetime.now()})
                record.sale_order_line_id.write({'return_returned_date' :  fields.Datetime.now()})
            elif state == 'rejected':
                record.write({'rejected_date' : fields.Datetime.now()})
                record.sale_order_line_id.write({'return_rejected_date' :  fields.Datetime.now()})

            elif state == 'scrap':
                record.write({'scrapped_date' : fields.Datetime.now()})
                record.sale_order_line_id.write({'return_scrapped_date' :  fields.Datetime.now()})

            if state in ['return','rejected']:
                record.sale_order_line_id._origin.state = state

    def action_return(self):
        for record in self:
            if record.state == 'return':
                move_ids = self.env['stock.move'].search([('sale_order_line_id','=',record.sale_order_line_id.id)])
                move_ids.write({
                    'quantity_done': 0,
                    'state' : 'draft'
                })
                move_ids._action_cancel()
                record.sale_order_line_id.state = 'return'
                record.sale_order_line_id.return_returned_date =  fields.Datetime.now()
                record.returned_date =  fields.Datetime.now()
