from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class add_commission_wizard(models.TransientModel):
    _name = 'add.commission.wizard'
    _description = 'Add Commission Wizard'

    commission_on = fields.Selection([('on_date', 'Between Order Dates'),('on_sale_order','Orders')],string='Commission On',default='on_date')
    order_ids = fields.Many2many('sale.order',string='Orders')
    commission_for = fields.Selection([('saleperson', 'SalesPerson'),('manager', 'SalesManager')],string="Commission For",default='saleperson')
    user_id = fields.Many2one('res.users',string='User',required=True)
    start_date = fields.Date('Order Start Date')
    end_date = fields.Date('Order End Date')

    @api.onchange('commission_for')
    def onchange_commission_for(self):
        if self.commission_for == 'saleperson':
            domain = [('is_salesperson','=',True)]
        elif self.commission_for == 'manager':
            manager_users = self.env.ref('tzc_sales_customization_spt.group_sales_manager_spt').sudo().users
            domain = [('id','in',manager_users.ids)]
        return {'domain':{'user_id':domain}}

    def action_process(self):
        exist_commission_lines=[]
        rule = self.user_id.manager_commission_rule_id if self.commission_for == 'manager' else self.user_id.commission_rule_id
        if not rule:
            raise UserError('%s has no commission rule'%(self.user_id.name))
        if self.commission_on == 'on_date':
            if self.start_date and self.end_date:
                domain = [('date_order','>=',self.start_date),('date_order','<=',self.end_date)]
            elif self.start_date:
                domain = [('date_order','>=',self.start_date)]
            elif self.end_date:
                domain = [('date_order','<=',self.end_date)]
            else:
                domain = []
            domain.append(('state','=','open_inv'))
            self.order_ids = self.env['sale.order'].search(domain)
        for order in self.order_ids:
            invoice = self.env['account.move'].search([('order_id','=',order.id),('state','!=','cancel')])
            commission_line = invoice.commission_line_ids.filtered(lambda x:x.commission_for == self.commission_for)
            if commission_line:
                exist_commission_lines.append(commission_line.ids)
            else:
                vals={'invoice_id':invoice.id,
                      'user_id':self.user_id.id,
                      'amount':round(rule.get_commission(invoice),2) if rule else 0.0,
                      'rule_id':rule.id,
                      'commission_for':self.commission_for,
                      'create_type':'manual'}
                self.env['kits.commission.lines'].create(vals)
        if exist_commission_lines:
            return{
                'name':'Warning',
                'type':'ir.actions.act_window',
                'res_model':'exist.commission.line.wizard',
                'view_mode':'form',
                'context':{'default_commission_lines_ids':[(6,0,exist_commission_lines)]},
                'target':'new'
            }
