from odoo import api, fields, models, _
from odoo.exceptions import UserError
from  lxml import etree

class kits_multi_website_return_request(models.Model):
    _name ="kits.multi.website.return.request"
    _description = "Kits Multi Website Return Request"
    _order = 'id desc'
    name = fields.Char("Name")
    sale_order_id = fields.Many2one("kits.multi.website.sale.order", "Sale Order")
    return_request_line_ids = fields.One2many("kits.multi.website.return.request.line", "return_request_id", "Return Request Lines") 
    state = fields.Selection([('draft','Draft'),('in_progress','In Progress'),('confirm','Confirm'),('refund','Refund'),('cancel','Cancelled')], default='draft')
    customer_id = fields.Many2one("kits.multi.website.customer","Customer")
    website_id = fields.Many2one("kits.b2c.website","Wesbite")
    so_sales_person_id = fields.Many2one('res.users','Sales Person',related='sale_order_id.user_id')
    user_id = fields.Many2one('res.users','Assignee')


    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_return_request, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res

    @api.model
    def create(self, vals):
        res = super(kits_multi_website_return_request, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('unique.multi.website.return.request.sequence')
        return res

    def action_cancel(self):
        move_obj =  self.env['stock.move']
        for record in self:
            for line in self.return_request_line_ids:
                if line.state == 'return' and record.state == 'confirm':
                    move_ids = move_obj.search([('sale_order_line_id','=',line.sale_order_line_id.id)])
                    for move in move_ids:
                        move.write({'quantity_done':line.quantity,'state': 'done'})
                line.state = 'cancel'
            record.write({
                'state': 'cancel',
            })
    def action_confirm(self):
        for record in self:
            line = record.sale_order_id.sale_order_line_ids - record.return_request_line_ids.mapped('sale_order_line_id')
            if line:
                line.write({'state': 'done'})
            if all(record.return_request_line_ids.mapped(lambda line: True if line.state == 'return' or line.state == 'scrap' or line.state == 'rejected' else False)):
                record.state = 'confirm'
                record.return_request_line_ids.action_return()
            else:
                raise UserError(_('All return lines must be in return or scrap state.'))

    def action_refund(self):
        form_view_id = self.env.ref("kits_multi_website.kits_multi_website_refund_option_form_view")            
        self.ensure_one()
        if all(self.return_request_line_ids.mapped(lambda line: True if line.state == 'return' or line.state == 'scrap' or line.state == 'rejected' else False)):
            total = 0
            total = sum(self.return_request_line_ids.filtered(lambda line: line if line.state in ['return','scrap'] else None).mapped('amount'))
            self.return_request_line_ids.filtered(lambda line: line if line.state in ['return','scrap'] else None).mapped('sale_order_line_id').write({
                'return_refunded_date': fields.Datetime.now()
            })
            
            return{
                'name': ('Refund Credit Option'),
                'res_model': 'kits.multi.website.refund.option',
                'type': 'ir.actions.act_window',
                'views': [(form_view_id.id, 'form')],
                'context': {'default_return_request_id':self.id,'default_amount': total},
                'target': 'new',
            }
        else:
            raise UserError(_('The order will be refunded only after taking everything and bringing it in return status'))

    def action_sale_order_line(self):
        if list(set(self.sale_order_id.sale_order_line_ids.ids) - set(self.return_request_line_ids.mapped('sale_order_line_id').ids)):
            ctx = dict()
            form_view_id = self.env.ref('kits_multi_website.kits_sale_order_line_select_wizard_form_view')
            self.ensure_one()
            wizard_id = self.env['kits.sale.order.line.select.wizard'].create({'return_request_id': self.id})
            ctx['domain']=self.id
            ctx.update(self._context)
            return{
                    'name': ('Select Product'),
                    'res_model': 'kits.sale.order.line.select.wizard',
                    'type': 'ir.actions.act_window',
                    'views': [(form_view_id.id, 'form')],
                    'context': ctx,
                    'res_id': wizard_id.id,
                    'target': 'new'
                }
        else:
            raise UserError(_('Product not found for return.'))
