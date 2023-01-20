from odoo import models,fields,api,_
from odoo.exceptions import UserError

class kits_replace_sales_manager_wizard(models.TransientModel):
    _name = 'kits.replace.sales.manager.wizard'
    _description = 'Replace Sales Manager'

    def _get_sale_managers(self):
        managers = self.env.ref('tzc_sales_customization_spt.group_sales_manager_spt').users
        both  = self.env['res.users'].search(['|',('active','=',True),('active','=',False),('is_salesperson','=',True)]).filtered(lambda x: x._is_salesmanager())
        return [('id','in',(managers+both).ids)]
    
    old_manager_id = fields.Many2one('res.users','Old Sales Manager',domain=_get_sale_managers)
    new_manager_id = fields.Many2one('res.users','New Sales Manager')
    do_archive = fields.Boolean('Archive ?')

    @api.onchange('old_manager_id')
    def _onchange_old_manager_id(self):
        managers = self.env.ref('tzc_sales_customization_spt.group_sales_manager_spt').users
        return {'domain':{'new_manager_id':[('id','in',managers.ids),('id','!=',self.old_manager_id.id)]}}

    def action_process(self):
        self.ensure_one()
        now = fields.Datetime.now()
        if self.old_manager_id != self.new_manager_id:
            # new managers countries,salespersons
            self.new_manager_id.contact_allowed_countries = [(6,0,self.new_manager_id.contact_allowed_countries.ids+self.old_manager_id.contact_allowed_countries.ids)]
            self.old_manager_id.contact_allowed_countries = False
            # remove countries and salespersons of old manager
            countries = self.old_manager_id.country_ids.ids
            salespersons = self.old_manager_id.allow_user_ids.ids
            self.old_manager_id.country_ids = False
            self.old_manager_id.allow_user_ids = False
            self.new_manager_id.country_ids = [(6,0,countries+self.new_manager_id.country_ids.ids)]
            self.new_manager_id.allow_user_ids = [(6,0,self.new_manager_id.allow_user_ids.ids+salespersons)]
            
            self.env['res.partner'].search([('user_id','=',self.old_manager_id.id),('is_user_internal','=',False)]).with_context(bulk_salesperson_update=True).write({'user_id':self.new_manager_id.id})

            orders = self.env['sale.order'].search(['|',('sale_manager_id','=',self.old_manager_id.id),('user_id','=',self.old_manager_id.id),('partner_id.is_user_internal','=',False)]).with_context(bulk_salesperson_update=True).write({'sale_manager_id':self.new_manager_id.id,'user_id':self.new_manager_id.id})
            invoices = self.env['account.move'].search(['|',('sale_manager_id','=',self.old_manager_id.id),('invoice_user_id','=',self.old_manager_id.id),('partner_id.is_user_internal','=',False)]).with_context(bulk_salesperson_update=True).write({'sale_manager_id':self.new_manager_id.id,'invoice_user_id':self.new_manager_id.id})
            if self.do_archive:
                self.old_manager_id.active = False
                self.old_manager_id.partner_id.active = False
            
        if self.old_manager_id == self.new_manager_id:
            raise UserError(_('Old Manager and New Manager can not be same.'))
        return {'type':'ir.actions.act_window_close'}
