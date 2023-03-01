from odoo import models,fields,api,_

class campaign_report_contacts(models.Model):
    _name = 'campaign.report.contacts'
    _description = 'Campaing Report Contacts'

    state = fields.Selection([('draft','Draft'),('sent','Sent'),('opened','Opened'),('clicked','Clicked'),('replied','Replied'),('bounced','Bounced'),('ignored','Ignored'),('failed','Failed'),('received','Received'),('failed_mailgun','Mailgun Failed')],compute='_compute_contact_state',string="State",store=True,default='draft',compute_sudo=True)
    set_state = fields.Boolean(compute="_compute_contact_state",compute_sudo=True)
    active = fields.Boolean(default=True)
    trace_id = fields.Many2one('mailing.trace','Mailing Trace',required=True,ondelete='cascade')
    email = fields.Char('Email',required=True)
    mailing_contact_id = fields.Many2one('mailing.contact','Mailing Contact',ondelete="cascade",required=True)
    activity_id = fields.Many2one('marketing.activity','Marketing Activity',ondelete="cascade",required=True)
    campaign_id = fields.Many2one('marketing.campaign','Marketing Campaign',ondelete="cascade",required=True)
    mass_mailing_id = fields.Many2one('mailing.mailing','Mass Mailing',ondelete="set null")

    sent = fields.Datetime('Sent',related="trace_id.sent_datetime")
    opened = fields.Datetime('Opened',related="trace_id.open_datetime")
    clicked = fields.Datetime('Clicked',related="trace_id.links_click_datetime")
    replied = fields.Datetime('Replied',related="trace_id.reply_datetime")
    # ignored = fields.Datetime('Ignored',related="trace_id.ignored")
    # bounced = fields.Datetime('Bounced',related="trace_id.bounced")
    # exception = fields.Datetime('Failed',related="trace_id.exception")
    received = fields.Datetime('Received',related="trace_id.received")
    failed_by_mailgun = fields.Datetime('Failed By Mailgun',related="trace_id.failed_mailgun")

    @api.depends('trace_id.sent_datetime','trace_id.open_datetime','trace_id.links_click_datetime','trace_id.reply_datetime','trace_id.received','trace_id.failed_mailgun')
    def _compute_contact_state(self):
        for rec in self:
            rec.set_state = False
            state = 'draft'
            if rec.trace_id.sent_datetime:
                rec.sent = rec.trace_id.sent_datetime
                state = 'sent'
            if rec.trace_id.open_datetime:
                rec.opened = rec.trace_id.open_datetime
                state='opened'
            if rec.trace_id.links_click_datetime:
                state = 'clicked'
                rec.clicked = rec.trace_id.links_click_datetime
            if rec.trace_id.reply_datetime:
                state = 'replied'
                rec.replied = rec.trace_id.reply_datetime
            if rec.trace_id.failed_mailgun:
                rec.failed_by_mailgun = rec.trace_id.failed_mailgun
                state = 'failed_mailgun'
            if rec.trace_id.received:
                rec.received = rec.trace_id.received
                state = 'received'
            rec.state = state

    name = fields.Char('Name',compute="_compute_mailing_contact",store=True,compute_sudo=True)
    mailing_country = fields.Many2one('res.country','Country ',compute="_compute_mailing_contact",store=True,compute_sudo=True)
    mailing_territory = fields.Many2one('res.country.group','Territory',compute="_compute_mailing_contact",store=True,compute_sudo=True)
    mailing_tag_ids = fields.Many2many('res.partner.category',string="Tags",compute="_compute_mailing_contact",store=True,compute_sudo=True)
    mailing_source = fields.Selection([('imported','Imported'),('odoo_contact','Odoo Contact'),('newsletter','Newsletter'),('mixed','Mixed')],compute="_compute_mailing_contact",string="Source",compute_sudo=True)
    mailing_prospect_level = fields.Selection([('zero','0'),('one','1')],compute="_compute_mailing_contact",string="Prospect Level",compute_sudo=True)
    mailing_status_type = fields.Selection([('b2c','B2C'),('b2b_regular','B2B-Regular	'),('b2b_fs','B2B-Fs')],compute="_compute_mailing_contact",string="Status Type",compute_sudo=True)
    mailing_action_type = fields.Selection([('confirmed','Confirmed'),('not_connected','Not Connected')],compute="_compute_mailing_contact",string="Action Type",compute_sudo=True)
    mailing_write_date = fields.Datetime('Last Updated On',compute="_compute_mailing_contact",store=True,compute_sudo=True)
    mailing_orders = fields.Integer(compute="_compute_mailing_contact",string="#Orders",store=True,compute_sudo=True)
    mailing_internal_id = fields.Char(compute="_compute_mailing_contact",string="Internal ID",store=True,compute_sudo=True)
    mailing_odoo_contact_id = fields.Many2one('res.partner',compute="_compute_mailing_contact",string="Odoo Contact ID",store=True,compute_sudo=True)
    mailing_salesperson_id = fields.Many2one('res.users',string="Salesperson",store=True,readonly=True,compute='_compute_mailing_contact',compute_sudo=True)
    marketing_activity_ids = fields.Text('Marketing Activities',readonly=True,store=True,compute="_compute_mailing_contact",compute_sudo=True)
    # mailing_promo_code_ids = fields.Many2many('sale.coupon.program',compute="_compute_mailing_contact",string="Promotion Coupons",store=True,compute_sudo=True)
 

    @api.depends('email','trace_id.email','trace_id','state','mailing_contact_id')
    def _compute_mailing_contact(self):
        user_obj = self.env['res.users']
        for rec in self:
            rec.name = rec.mailing_contact_id.name
            rec.mailing_country = rec.mailing_contact_id.country_id.id
            rec.mailing_territory = rec.mailing_contact_id.territory.id
            rec.mailing_tag_ids = [(6,0,rec.mailing_contact_id.tag_ids.ids or [])]
            rec.mailing_source = rec.mailing_contact_id.source
            rec.mailing_prospect_level = rec.mailing_contact_id.prospect_level
            rec.mailing_status_type = rec.mailing_contact_id.status_type
            rec.mailing_action_type = rec.mailing_contact_id.action_type
            rec.mailing_write_date = rec.mailing_contact_id.write_date
            rec.mailing_orders = rec.mailing_contact_id.orders
            rec.mailing_internal_id = rec.mailing_contact_id.internal_id
            rec.mailing_odoo_contact_id = rec.mailing_contact_id.odoo_contact_id.id
            # rec.mailing_promo_code_ids = [(6,0,rec.mailing_contact_id.promo_code_ids.ids)]
            salesperson = rec.mailing_contact_id.odoo_contact_id.user_id
            if not salesperson and rec.trace_id.email:
                salesperson = self.env['res.partner'].search([('email','=',rec.trace_id.email)],limit=1).user_id
            if not salesperson and rec.mailing_contact_id.country_id:
                salesperson = user_obj.search([('contact_allowed_countries','in',rec.mailing_contact_id.country_id.ids)],limit=1)
            rec.mailing_salesperson_id = salesperson.id
            activities = rec.trace_id.marketing_trace_id.activity_id.mapped("name") if rec.trace_id.marketing_trace_id.activity_id else rec.marketing_activity_ids.split(',')
            rec.marketing_activity_ids = ','.join([str(activity) for activity in activities if activity])

    def action_send_mail_contact_report(self):
        return {
            'name': _('Send Mail'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'binding_model':"res.partner",
            'view_mode' : 'form',
            'target': 'new',
            'context':{
                        'default_model': 'res.partner',
                        'default_res_id': self.env['res.partner'].search([],limit=1).id if not self else self[0].id,
                        'default_partner_to': ','.join(str(id.id) for id in self.mailing_odoo_contact_id),
                        'default_template_id': self.env.ref('mail.email_template_partner').id,
                        'default_composition_mode': 'mass_mail',
                        'campaign':True,
                        'resend':True,
                        'raise_campaign':True,
                    },
        }
