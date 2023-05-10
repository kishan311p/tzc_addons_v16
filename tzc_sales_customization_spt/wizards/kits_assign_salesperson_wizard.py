from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class kits_assign_salesperson_wizard(models.TransientModel):
    _name = "kits.assign.salesperson.wizard"
    _description = "Assign Salesperson Wizard"

    def _get_manager_domain(self):
        manager = self.env.ref('tzc_sales_customization_spt.group_sales_manager_spt').sudo().users
        return [('id','in',manager.ids)]

    def _get_new_salespersons(self):
        managers = self.env.ref('tzc_sales_customization_spt.group_sales_manager_spt').sudo().users
        return ['|',('is_salesperson','=',True),('id','in',managers.ids)]

    message = fields.Text('Message')
    sales_person_id = fields.Many2one('res.users',"Salesperson",domain=_get_new_salespersons)
    partner_id = fields.Many2one('res.partner','Partner')
    # archive_old = fields.Boolean('Archive old Salesperson ?')
    new_manager_id = fields.Many2one('res.users','New Sales Manager',domain=_get_manager_domain)
    readonly_new_manager = fields.Boolean(compute="_compute_readonly_new_manager")

    # Fields for delete contact flow.
    hide_button = fields.Boolean(help="Flag for hide button of wizard")
    change_contact_options = fields.Selection([('updt_cont','Update Customer'),('updt_ord_cont','Update Customer and Order')],default='updt_cont')
    partner_ids = fields.Many2many('res.partner','res_partner_assign_salesperson_wizard_rel','wizard_id','partner_id','Contacts')
    # selected_id = fields.Many2one('res.partner','Contact')

    @api.depends('sales_person_id')
    def _compute_readonly_new_manager(self):
        self.ensure_one()
        readonly = False if self.sales_person_id else True
        if self.sales_person_id and self.sales_person_id.has_group('tzc_sales_customization_spt.group_sales_manager_spt'):
            readonly = True
        self.readonly_new_manager = readonly

    @api.onchange('sales_person_id')
    def _onchange_salesperson_id_kits(self):
        if self.sales_person_id:
            manager = self.env['res.users'].sudo().search([('allow_user_ids','in',self.sales_person_id.ids)],limit=1)
            if self.sales_person_id.has_group('tzc_sales_customization_spt.group_sales_manager_spt'):
                manager = self.env['res.users'].sudo()
            self.new_manager_id = manager.id

    def update_orders(self):
        # old_salesperson = self.partner_id.user_id
        if self.sales_person_id:
            changed_orders = []
            for order in self.partner_id.sale_order_ids:
                res = order.with_context(bulk_salesperson_update=True).write({'user_id':self.sales_person_id.id,'sale_manager_id':self.new_manager_id.id})
                changed_orders.append(order.name) if res else None
            for invoice in self.partner_id.invoice_ids:
                invoice.with_context(bulk_salesperson_update=True).write({'invoice_user_id':self.sales_person_id.id,'sale_manager_id':self.new_manager_id.id})
            change_user = self.partner_id.sudo().write({'user_id':self.sales_person_id.id})
            if change_user:
                self.with_context(changed_orders=changed_orders).notify_admin_salesperson_name()
            # remove from old manager
            if self.new_manager_id:
                manager = self.env['res.users'].search([('allow_user_ids','in',self.sales_person_id.ids),('id','!=',self.new_manager_id.id)])
                if manager and self.sales_person_id in manager.allow_user_ids:
                    manager.allow_user_ids = manager.allow_user_ids - self.sales_person_id
            

            self.new_manager_id.sudo().write({'allow_user_ids':[(6,0,self.new_manager_id.allow_user_ids.ids+[self.sales_person_id.id])]})
            # remove countries from old salesperson
            # assign to new manager
            # old_countries = old_salesperson.country_ids.ids
            # old_contact_allowed_countries = old_salesperson.contact_allowed_countries.ids
            # self.sales_person_id.sudo().write({'contact_allowed_countries':[(6,0,self.sales_person_id.contact_allowed_countries.ids+old_contact_allowed_countries)]})
            # old_salesperson.country_ids = False
            # old_salesperson.sudo().write({'contact_allowed_countries': False})
            # self.sales_person_id.country_ids = [(6,0,self.sales_person_id.country_ids.ids+old_countries)]
            # if self.archive_old:
            #     old_salesperson.active = False
            #     old_salesperson.partner_id.active = False
        else:
            raise UserError(_('Select salesperson.'))

    def update_partner(self):
        old_salesperson = self.partner_id.user_id
        if self.sales_person_id:
            update_user = self.partner_id.sudo().write({'user_id':self.sales_person_id.id})
            if update_user:
                self.with_context(old_salesperson=old_salesperson.name).notify_admin_salesperson_name()
            if self.new_manager_id:
                self.sales_person_id.manager_id = self.new_manager_id.id
                # manager = self.env['res.users'].search([('allow_user_ids','in',self.sales_person_id.ids),('id','!=',self.sales_person_id.manager_id.id)])
                # if manager and self.sales_person_id in manager.allow_user_ids:
                #     manager.allow_user_ids = manager.allow_user_ids - self.sales_person_id
            self.new_manager_id.allow_user_ids = [(6,0,self.new_manager_id.allow_user_ids.ids+[self.sales_person_id.id])]
            # remove countries from old salesperson
            # old_countries = old_salesperson.country_ids.ids
            # old_contact_allowed_countries = old_salesperson.contact_allowed_countries.ids
            # self.sales_person_id.contact_allowed_countries = [(6,0,self.sales_person_id.contact_allowed_countries.ids+old_contact_allowed_countries)]
            # old_salesperson.country_ids = False
            # old_salesperson.contact_allowed_countries = False
            # self.sales_person_id.country_ids = [(6,0,self.sales_person_id.country_ids.ids+old_countries)]
            # if self.archive_old:
            #     old_salesperson.active = False
            #     old_salesperson.partner_id.active = False
        else:
            raise UserError(_('Select salesperson.'))
    
    def update_sales_Person(self):
        if self._context.get('active_id') and self.env['res.partner'].browse(self._context.get('active_id')) and self.env['res.partner'].browse(self._context.get('active_id')).check_partner_access_right():
            active_ids = self._context.get('active_ids')
            partner_ids = self.env['res.partner'].browse(active_ids).filtered(lambda x: not x.is_user_internal) if len(active_ids) > 1 else self.env['res.partner'].browse(active_ids)
            # old_salespersons = False
            if active_ids:
                # old_salespersons = partner_ids.mapped('user_id').sudo()
                update = partner_ids.with_context(bulk_salesperson_update=True).write({'user_id':self.sales_person_id.id})
                
                if self.new_manager_id:
                    self.sales_person_id.manager_id = self.new_manager_id.id
                    # old_managers = self.env['res.users'].search([('allow_user_ids','in',self.sales_person_id.ids),('id','!=',self.new_manager_id.id)])
                    # self.new_manager_id.allow_user_ids = [(6,0,self.new_manager_id.allow_user_ids.ids+[self.sales_person_id.id])]
                    # for old_manager in old_managers:
                    #     old_manager.allow_user_ids -= self.sales_person_id

                if self._context.get('multiple_customer_order_update') and update:
                    for partner in partner_ids:
                        order_vals = {'user_id':self.sales_person_id.id}
                        invoice_vals = {'invoice_user_id':self.sales_person_id.id}
                        if self.new_manager_id:
                            order_vals.update(sale_manager_id=self.new_manager_id.id)
                            invoice_vals.update(sale_manager_id=self.new_manager_id.id)
                        partner.sale_order_ids.with_context(bulk_salesperson_update=True).write(order_vals) if partner.sale_order_ids else None
                        partner.invoice_ids.with_context(bulk_salesperson_update=True).write(invoice_vals) if partner.invoice_ids else None
            # for old_salesperson in old_salespersons:
                # old_countries = old_salesperson.country_ids.ids
                # old_contact_allowed_countries = old_salesperson.contact_allowed_countries.ids
                # self.sales_person_id.contact_allowed_countries = [(6,0,self.sales_person_id.contact_allowed_countries.ids+old_contact_allowed_countries)]
                # old_salesperson.country_ids = False
                # old_salesperson.contact_allowed_countries = False
                # self.sales_person_id.country_ids = [(6,0,self.sales_person_id.country_ids.ids+old_countries)]
            # if self.archive_old:
            #     old_salespersons.write({'active':False})
            #     old_salespersons.mapped('partner_id').write({'active':False})
        else:
            raise UserError('You can\'t change your superior salesperson.')

    def notify_admin_salesperson_name(self):
        setting_admins = self.env['res.users'].sudo().browse(eval(self.env['ir.config_parameter'].sudo().get_param('user_ids_spt','[]')))
        recipients = setting_admins.mapped('partner_id')
        ctx = self._context.copy()
        ctx.update({'changed_orders':self._context.get('changed_orders')})
        for recipient in recipients:
            ctx.update(recipient=recipient.name)
            self.with_context(ctx).env.ref('tzc_sales_customization_spt.partner_salesperson_change_notify_admin_mail_template').sudo().send_mail(self.partner_id.id,force_send=True,email_values={'recipient_ids':[(6,0,recipient.ids)]},email_layout_xmlid="mail.mail_notification_light")

    def action_process(self):
        # deleted_ids = []
        # archived_count = 0
        # deleted_count = 0
        allow_contact_for_delete = []
        if self.sales_person_id:
            for partner in self.partner_ids:
                partner.sudo().write({'user_id':self.sales_person_id.id})
                if self.new_manager_id and partner.user_ids:
                    partner.user_ids[0].manager_id = self.new_manager_id.id
                if self.change_contact_options == 'updt_ord_cont':
                    if partner.user_ids:
                        order_id = self.env['sale.order'].search([('user_id','in',partner.user_ids[0].ids)])
                        order_id.user_id = self.sales_person_id.id
                        order_id.sale_manager_id = self.new_manager_id.id
                        if order_id.invoice_ids:
                            for inv in order_id.invoice_ids:
                                inv.invoice_user_id = self.sales_person_id.id
                                inv.sale_manager_id = self.new_manager_id.id
            # try:
            #     if self.partner_id.user_ids:
            #         for user in self.partner_id.user_ids:
            #             try:
            #                 user.active = False
            #                 user._cr.commit()
            #                 user.unlink()
            #             except:
            #                 self._cr.rollback()
            #                 pass
            #     self.partner_id.active = False
            #     self.partner_id._cr.commit()
            #     self.partner_id.unlink()
            #     deleted_ids.append(self.partner_id.id)
            #     deleted_count += 1
            # except:
            #     self._cr.rollback()
            #     partner_id = self.exists()
            #     deleted_ids.append(self.partner_id.id)
            #     archived_count += 1
            #     pass

            if self.partner_id.user_ids:
                allow_contact_for_delete.append(self.partner_id.id)

            # message = (f'Out of {self.env.context.get("total_count")} contacts {deleted_count} is deleted and following {archived_count} is archived')
            message = (f'Out of {self.env.context.get("total_count")} contacts {len(allow_contact_for_delete)} will be deleted.')
            return {
                    'name':_('Delete Contact'),
                    'type':'ir.actions.act_window',
                    'res_model':'kits.confirm.contact.delete.wizard',
                    'view_mode':'form',
                    'context':{'default_partner_ids':[(6,0,allow_contact_for_delete)],'default_message':message},
                    'target':'new',
                }
