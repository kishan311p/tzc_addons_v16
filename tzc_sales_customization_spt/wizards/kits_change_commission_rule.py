from odoo import models,fields,api,_

class kits_change_commission_rule(models.TransientModel):
    _name = 'kits.change.commission.rule'
    _description = 'Change Commission Rule'

    def _get_rule_domain(self):
        if self._context.get('default_commission_of') == 'saleperson':
            return ['|',('commission_for','=','sales_person'),('commission_for','=','both')]
        elif self._context.get('default_commission_of') == 'manager':
            return ['|',('commission_for','=','sales_manager'),('commission_for','=','both')]
        # elif self._context.get('default_commission_of') == 'both':
        #     return [('commission_for','=','both')]
        else:
            return None

    message = fields.Text('Message',compute="_compute_message")
    user_id = fields.Many2one('res.users','User')
    commission_of = fields.Char('Commission of')
    new_rule_id = fields.Many2one('kits.commission.rules','New Rule',domain=_get_rule_domain,required=True)
    change_old_commissions = fields.Boolean('Change Old Commissions ?')
    start_date = fields.Date('Start Date')

    def get_old_commissions(self):
            domain = []
            if self.start_date:
                domain.append(('invoice_date','>=',self.start_date))
            invoices = self.env['account.move'].search(domain)
            if self.commission_of in ('saleperson','manager'):
                lines = invoices.commission_line_ids.filtered(lambda x: x.state == 'draft' and x.user_id == self.user_id and x.commission_for == self.commission_of and not x.is_product_brand_commissison)
            # elif self.commission_of == 'both':
            #     lines = invoices.mapped('commission_line_ids').filtered(lambda x: x.state == 'draft' and x.user_id == self.user_id and x.create_type == 'by_system' and not x.is_product_brand_commissison)
            return lines


    @api.depends('user_id','new_rule_id','start_date')
    def _compute_message(self):
        self.ensure_one()
        message = False
        old_commissions = self.get_old_commissions()
        orders = old_commissions.mapped('invoice_id')
        if orders:
            message = "Your commission in following invoices will be updated according to new rule \"{}\"{}".format(self.new_rule_id.name or '',":\n{}".format(', '.join(orders.sorted(lambda x: x.name).mapped('name'))))
        self.message = message
    

    def action_change_rule_id(self):
        notify = False
        if self.commission_of == 'saleperson':
            if self.user_id.commission_rule_id.id != self.new_rule_id.id:
                notify = True
            self.user_id.commission_rule_id = self.new_rule_id.id
        elif self.commission_of == 'manager':
            if self.user_id.manager_commission_rule_id.id != self.new_rule_id.id:
                notify = True
            self.user_id.manager_commission_rule_id = self.new_rule_id.id
        # elif self.commission_of == 'both':
        #     notify = True if (self.user_id.commission_rule_id != self.new_rule_id and self.user_id.manager_commission_rule_id != self.new_rule_id) else False
        #     self.user_id.write({'commission_rule_id':self.new_rule_id.id,'manager_commission_rule_id':self.new_rule_id.id})
        else:
            pass
        if self.change_old_commissions: 
            old_commissions = self.get_old_commissions()
            for commission_line in old_commissions:
                commission_line.write({'amount':self.new_rule_id.get_commission(commission_line.invoice_id)})
            ctx = dict()
            ctx.update(rule_name=self.new_rule_id.name,updated_orders=', '.join(old_commissions.mapped('invoice_id').sorted(lambda x: x.name).mapped('name')))
            if notify:
                self.env.ref('tzc_sales_customization_spt.kits_sales_commission_notify_salesperson_commission_change').sudo().with_context(ctx).send_mail(self.user_id.id,force_send=True)
