from odoo import models,fields,api,_
from odoo.exceptions import UserError

class account_move(models.Model):
    _inherit = 'account.move'

    def _get_sales_manager_domain(self):
        managers = self.env.ref('tzc_sales_customization_spt.group_sales_manager_spt').sudo().users
        return [('id','in',managers.ids)]

    def _get_default_sale_manager_id(self):
        order = self.env['sale.order'].search([('invoice_ids','in',self.ids)],limit=1)
        return order.sale_manager_id.id

    commission_line_ids = fields.One2many('kits.commission.lines','invoice_id','Commissions')
    is_commission_paid = fields.Boolean('Paid ?')
    sale_manager_id = fields.Many2one('res.users','Sales Manager',domain=_get_sales_manager_domain,default=_get_default_sale_manager_id)

    def button_cancel(self):
        if self.state in ['draft']:
            self.commission_line_ids.action_cancel()
            # self.with_context(from_cancel=True).write({'is_commission_paid':False})
            sale_id = self.env['sale.order'].search([('invoice_ids','in',self.ids)],limit=1)
            if sale_id.picking_ids.filtered(lambda x: x.state != 'cancel' and 'WH/OUT' in x.name).state =='done':
                state = 'shipped'
            else:
                if sale_id.source_spt != 'Manually':
                    state = 'received'
                elif sale_id.state == 'cancel':
                    state = 'cancel'
                else:
                    state = 'draft'
            sale_id.write({'state': state})  
            return super(account_move,self).button_cancel()
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                        'title': 'Something is wrong.',
                        'message': 'Please reload your screen.',
                        'sticky': True,
                    }
                }
    
    def action_post(self):
        if self.state in ['draft']:
            res = super(account_move,self).action_post()
            self.commission_line_ids.filtered(lambda x: x.state == 'cancel').sudo().unlink()
            if res:
                commission_line_obj = self.env['kits.commission.lines']
                user_obj = self.env['res.users']
                for record in self:
                    users = dict(saleperson=user_obj,manager=user_obj)
                    if record.invoice_user_id:
                        if record.partner_id.user_ids and record.invoice_user_id.ids != record.partner_id.user_ids.ids:
                            users['saleperson'] = record.invoice_user_id
                    if record.sale_manager_id:
                        users['manager'] = record.sale_manager_id
                    for user in users:
                        values = self._get_commission_line_detail(user,users[user])
                        if record.state == 'posted' and values and values['amount']:
                            commission_id = commission_line_obj.search([('user_id','=',users[user].id),('is_product_brand_commissison','=',False),('state','=','draft'),('commission_for','=',user),('invoice_id','=',record.id)],limit=1)
                            if not commission_id:
                                commission_line_obj.create(values)
                            else:
                                commission_id.write(values)
                    if record.state == 'posted' and any(record.line_ids.mapped('product_id.product_brand_commission')):
                        if record.partner_id.user_ids and record.invoice_user_id.ids != record.partner_id.user_ids.ids:
                            brand_commission_line_id = commission_line_obj.search([('user_id','=',record.invoice_user_id.id),('is_product_brand_commissison','=',True),('state','=','draft'),('commission_for','=','saleperson'),('invoice_id','=',record.id)],limit=1)
                            commission = 0.0
                            for line in record.line_ids.filtered(lambda x:x.product_id.product_brand_commission):
                                commission += round(round(line.discount_unit_price,2) * line.quantity * line.product_id.product_brand_commission * 0.01,2)
                            vals = self.get_product_brand_commission_vals(record,commission)
                            if brand_commission_line_id and commission:
                                brand_commission_line_id.write(vals)
                            else:
                                if commission:
                                    brand_commission_line_id.create(vals)

                    if record.commission_line_ids and record.inv_payment_status in ['full','over']:
                        record.commission_line_ids.write({'state':'paid'})
                    elif record.commission_line_ids and record.inv_payment_status == 'partial':
                        record.commission_line_ids.write({'state':'draft'})
                    else:
                        record.commission_line_ids.write({'state':'draft'})
            return res
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                        'title': 'Something is wrong.',
                        'message': 'Please reload your screen.',
                        'sticky': True,
                    }
                }

    def _get_commission_line_detail(self,type,user):
        rule = user.manager_commission_rule_id if type == 'manager' else user.commission_rule_id
        vals = {
            # 'name':'Commission of invoice {} for {} {}. '.format(self.name,type,user.name),
            'invoice_id':self.id,
            'user_id':user.id,
            'amount':round(rule.get_commission(self),2) if rule else 0.0,
            'rule_id':rule.id,
            'commission_for':type,
            'create_type':'by_system',
        }
        return vals

    def get_product_brand_commission_vals(self,record,commission):
        vals = {'create_type':'by_system',
                'invoice_id':record.id,
                'amount':commission,
                'user_id':record.invoice_user_id.id,
                'commission_for':'saleperson',
                'is_product_brand_commissison':True}
        return vals

    def write(self,vals):
        res = super(account_move,self).write(vals)
        if 'inv_payment_status' in vals and not self._context.get('from_cancel'):
            if vals['inv_payment_status'] in ['over','full']:
                self.commission_line_ids.write({'state':'paid'})
            elif vals['inv_payment_status'] == 'partial':
                self.commission_line_ids.write({'state':'draft'})
        return res
