from odoo import models,fields,api,_

class kits_change_contact_country(models.TransientModel):
    _name = 'kits.change.contact.country'
    _description = 'Change Contact Country Wizard'

    def _get_default_message(self):
        partner = self.env['res.partner'].browse(self._context.get('default_partner_id'))
        message =  'You are modifying the country for client "{}".'.format(partner.name)
        if partner.sale_order_ids.filtered(lambda x: x.state not in ['draft_inv','open_inv','paid','cancel','merged']):
            message += "\nCurrency, Pricelist and Fiscal position of following orders will be changed.   Please Review following #orders: {}".format(','.join(partner.sale_order_ids.filtered(lambda x: x.state not in ['draft_inv','open_inv','done','cancel','merged']).mapped('name')))
        return message
    
    def _get_default_country_id(self):
        partner = self.env['res.partner'].browse(self._context.get('default_partner_id'))
        return partner.country_id.id
    
    partner_id = fields.Many2one('res.partner','Partner')
    country_id = fields.Many2one('res.country','Country',default=_get_default_country_id)
    state_id = fields.Many2one('res.country.state','State')
    message = fields.Text('Message',default=_get_default_message)

    @api.onchange('country_id')
    def _onchange_country_id(self):
        if self.country_id:
            self.state_id = self.env['res.country.state'].search([('country_id','=',self.country_id.id)],limit=1).id

    def action_process(self):
        user_obj = self.env['res.users']
        notify_users = user_obj.browse(eval(self.env['ir.config_parameter'].sudo().get_param('user_ids_spt','[]')))
        notify_users += user_obj.search([('id','not in',self.partner_id.user_ids.ids),('is_salesperson','=',True),('country_ids','in',self.country_id.ids)])
        notify_users += user_obj.search([('id','not in',self.partner_id.user_ids.ids),('is_salesmanager','=',True),('contact_allowed_countries','in',self.country_id.ids)])
        recipients = notify_users.mapped('partner_id')
        notify = False
        if self.country_id:
            notify = True if self.country_id != self.partner_id.country_id else False
            self.partner_id.country_id = self.country_id.id
        self.partner_id.state_id = self.state_id.id
        for record in self.partner_id.sale_order_ids.filtered(lambda x: x.state not in ['draft_inv','open_inv','paid','cancel','merged']):
            if record.pricelist_id != self.partner_id.property_product_pricelist:
                record.pricelist_id = self.partner_id.property_product_pricelist.id
            fiscal = self.env['account.fiscal.position']._get_fiscal_position(record.partner_id)
            record.fiscal_position_id = fiscal
            record.order_line._compute_tax_id()
            # [l.product_id_change() for l in record.order_line]
        # Notify admin for country change
        if notify:
            for recipient in recipients:
                self.with_context(recipient=recipient.name).env.ref('tzc_sales_customization_spt.partner_country_change_notify_admin_mail_template').sudo().send_mail(self.partner_id.id,force_send=True,email_values={'recipient_ids':[(6,0,recipient.ids)]})
