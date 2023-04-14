from odoo import models,fields,api,_

class kits_commission_lines(models.Model):
    _name = 'kits.commission.lines'
    _description = 'Commission Lines'

    # def _get_user_id_domain(self):
    #     domain = [('id','=',False)]
    #     manager = self.env['res.users'].search([('allow_user_ids','in',self.invoice_id.user_id.ids)],limit=1)
    #     if self.commission_for == 'saleperson':
    #         domain.append(('id','=',self.invoice_id.user_id.id))
    #     elif self.commission_for == 'manager':
    #         domain.append(('id','=',manager.id))
    #     else:
    #         domain = [('id','in',[user.id for user in (manager,self.invoice_id.user_id) if user.id])]
    #     return domain
            
    
    def _get_default_rule(self):
        rule_domain = False
        if self.commission_for == 'saleperson':
            rule_domain = self.user_id.commission_rule_id.id
        elif self.commission_for == 'manager':
            rule_domain = self.user_id.manager_commission_rule_id.id
        return rule_domain
        
    name = fields.Char('Name',compute="_compute_commission_line_name")
    invoice_id = fields.Many2one('account.move','Invoice',ondelete="cascade",states={'draft': [('readonly',False)]})
    user_id = fields.Many2one('res.users','User',ondelete="cascade",states={'draft': [('readonly',False)]})
    # state = fields.Selection([('draft','Draft'),('paid','Paid'),('cancel','Cancelled')],default="draft",string='State')
    amount = fields.Float('Commission',states={'draft': [('readonly',False)]})
    rule_id = fields.Many2one('kits.commission.rules','Rule',default=_get_default_rule)
    commission_for = fields.Selection([('saleperson','SalesPerson'),('manager','SalesManager')],string="User Role")
    create_type = fields.Selection([('by_system','System'),('manual','Manual')],default="manual",string="Create Type",states={'draft': [('readonly',False)]})
    is_product_brand_commissison = fields.Boolean('Product Brand Commission')
    commission_date = fields.Date('Date',related='invoice_id.invoice_date')
    kits_order_id = fields.Many2one('sale.order','Order',compute="_compute_order_id",store=True)
    state = fields.Selection([('draft','Draft'),('full','Fully Paid'),('partial','Partial Paid'),('over','Over Paid'),('cancel','Cancel')],'Status',compute="_compute_state",copy=False,store=True)

    @api.depends('invoice_id.order_id.payment_status')
    def _compute_state(self):
        for rec in self:
            if rec.invoice_id.inv_payment_status:
                rec.state = rec.invoice_id.inv_payment_status
            else:
                rec.state = 'draft'

    @api.depends('invoice_id')
    def _compute_order_id(self):
        for rec in self:
            order_id = self.env['sale.order'].search([('invoice_ids','in',rec.invoice_id.ids)],limit=1)
            rec.kits_order_id = order_id.id

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
    
    @api.depends('invoice_id','commission_for','user_id')
    def _compute_commission_line_name(self):
        for record in self:
            if record.is_product_brand_commissison:
                record.name = 'Extra Commission of invoice {} for {} {}. '.format(record.invoice_id.name or '',record.commission_for or '',record.user_id.name or '')
            else:
                record.name = 'Commission of invoice {} for {} {}. '.format(record.invoice_id.name or '',record.commission_for or '',record.user_id.name or '')

    @api.onchange('invoice_id','commission_for','user_id')
    def _onchange_domain_user_id(self):
        # onchange domain on user_id
        user_domain = [('id','=',False)]
        manager = self.env.ref('tzc_sales_customization_spt.group_sales_manager_spt').users
        if self.commission_for == 'saleperson':
            self.rule_id = self.user_id.commission_rule_id.id
            user_domain = [('is_salesperson','=',True)]
        elif self.commission_for == 'manager':
            self.rule_id = self.user_id.manager_commission_rule_id.id
            user_domain = [('id','=',manager.ids)]
        else:
            pass
        return {'domain':{'user_id':user_domain}}
