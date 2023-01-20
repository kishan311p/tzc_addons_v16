from odoo import models,fields,api,_
from odoo.exceptions import UserError

class kits_replace_sales_person_wizard(models.TransientModel):
    _name = 'kits.replace.sales.person.wizard'
    _description = 'Replace Salesperson Wizard'

    def _get_salesmanagers(self):
        managers = self.env.ref('tzc_sales_customization_spt.group_sales_manager_spt').users
        return [('id','in',managers.ids)]

    def _get_old_salesperson_domain(self):
        salespersons = self.env['res.users'].search([('is_salesperson','=',True)])
        managers = salespersons.filtered(lambda x: x.is_sales_manager)
        return [('id','in',(salespersons-managers).ids)]
    
    def _get_new_salesperson_domain(self):
        salespersons = self.env['res.users'].search([('is_salesperson','=',True)])
        managers = self.env.ref('tzc_sales_customization_spt.group_sales_manager_spt').sudo().users
        return [('id','in',salespersons.ids+managers.ids)]

    old_salesperson_id = fields.Many2one('res.users','Old Salesperson',domain=_get_old_salesperson_domain)
    new_salesperson_id = fields.Many2one('res.users','New Salesperson',domain=_get_new_salesperson_domain)

    old_manager_id = fields.Many2one('res.users','Old Sales Manager')
    new_manager_id = fields.Many2one('res.users','New Sales Manager',domain=_get_salesmanagers)
    do_archive = fields.Boolean('Archive ?')
    readonly_new_manager = fields.Boolean(compute="_compute_readonly_new_manager")

    @api.depends('new_salesperson_id')
    def _compute_readonly_new_manager(self):
        self.ensure_one()
        readonly = False if self.new_salesperson_id else True
        if self.new_salesperson_id and self.new_salesperson_id.has_group('tzc_sales_customization_spt.group_sales_manager_spt'):
            self.new_manager_id = False
            readonly = True
        self.readonly_new_manager = readonly

    @api.onchange('old_salesperson_id')
    def _onchange_old_salesperson_id(self):
        self.ensure_one()
        manager = self.env['res.users'].sudo().search([('allow_user_ids','in',self.old_salesperson_id.ids)],limit=1)
        self.old_manager_id = manager.id

    @api.onchange('new_salesperson_id')
    def _onchange_new_salesperson_id(self):
        self.ensure_one()
        manager = self.env['res.users'].sudo().search([('allow_user_ids','in',self.new_salesperson_id.ids)],limit=1)
        if not manager:
            manager = self.old_manager_id.id
        if not manager:
            try:
                manager = int(self.env['ir.config_parameter'].sudo().get_param('default_sales_person_id'))
            except:
                manager = False
        self.new_manager_id = manager if self.new_salesperson_id else False


    def action_process(self):
        if self.new_salesperson_id and self.old_salesperson_id and self.new_salesperson_id != self.old_salesperson_id:
            # remove old manager of new salesperson
            # manager = self.env['res.users'].search([('allow_user_ids','in',self.new_salesperson_id.ids)])
            # if manager and self.new_salesperson_id in manager.allow_user_ids and self.new_manager_id != manager:
            #     manager.allow_user_ids = manager.allow_user_ids - self.old_salesperson_id
            # # assign new manager to new salesperson
            # if self.new_salesperson_id not in self.new_manager_id.allow_user_ids:
                # self.new_manager_id.allow_user_ids = [(6,0,self.new_manager_id.allow_user_ids.ids+[self.new_salesperson_id.id])]

            if self.new_manager_id:
                self.new_salesperson_id.manager_id = self.new_manager_id.id
            countries = self.old_salesperson_id.country_ids.ids
            self.old_salesperson_id.country_ids = False
            self.new_salesperson_id.country_ids = [(6,0,countries+self.new_salesperson_id.country_ids.ids)]
            self.new_salesperson_id.contact_allowed_countries = [(6,0,self.new_salesperson_id.contact_allowed_countries.ids+self.old_salesperson_id.contact_allowed_countries.ids)]
            self.old_salesperson_id.contact_allowed_countries = False
            if self.new_salesperson_id._is_salesmanager() and self.old_salesperson_id._is_salesmanager():
                self.new_salesperson_id.allow_user_ids = [(6,0,self.old_salesperson_id.allow_user_ids.ids+self.new_salesperson_id.allow_user_ids.ids)]

            contacts = self.env['res.partner'].search([('user_id','=',self.old_salesperson_id.id),('is_user_internal','=',False)])
            contacts.with_context(bulk_salesperson_update=True).write({'user_id':self.new_salesperson_id.id})
            
            orders = self.env['sale.order'].search([('user_id','=',self.old_salesperson_id.id),('state','not in',('cancel','merged')),('partner_id.is_user_internal','=',False)])
            orders.with_context(bulk_salesperson_update=True).write({'user_id':self.new_salesperson_id.id,'sale_manager_id':self.new_manager_id.id})
            
            # pickings = self.env['stock.picking'].search([('user_id','=',self.old_salesperson_id.id),('state','!=','cancel'),('partner_id.is_user_internal','=',False)])
            # pickings.write({'user_id':self.new_salesperson_id.id})

            invoice_ids = self.env['account.move'].search([('invoice_user_id','=',self.old_salesperson_id.id),('state','!=','cancel'),('partner_id.is_user_internal','=',False)])
            invoice_ids.with_context(bulk_salesperson_update=True).write({'invoice_user_id':self.new_salesperson_id.id,'sale_manager_id':self.new_manager_id.id})

            # if self.old_salesperson_id._is_salesmanager():
            #     self.env['sale.order'].search([('sale_manager_id','=',self.old_manager_id.id),('state','not in',('cancel','merged'))]).write({'sale_manager_id':self.new_manager_id.id})
            #     self.env['account.move'].search([('sale_manager_id','=',self.old_manager_id.id),('state','!=','cancel')]).write({'sale_manager_id':self.new_manager_id.id})
            
            if self.do_archive:
                self.old_salesperson_id.active = False
                self.old_salesperson_id.partner_id.active = False
        else:
            raise UserError(_('Please select different Sales Persons.'))
        return {'type':'ir.actions.act_window_close'}
