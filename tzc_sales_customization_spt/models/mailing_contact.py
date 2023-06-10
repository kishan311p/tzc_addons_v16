import requests
from odoo import models,fields,api,_
from odoo.http import request
import re 
from odoo.exceptions import UserError
class mailing_contact(models.Model):
    _inherit = "mailing.contact"
    
    internal_id = fields.Char('Internal ID')
    odoo_contact_id = fields.Many2one('res.partner','Odoo Contact ID')
    territory = fields.Many2one('res.country.group','Territory',store=True,compute="_compute_territory",compute_sudo=True)
    phone = fields.Char('Phone')
    street = fields.Char('Address1')
    street2 = fields.Char('Address2')
    city = fields.Char('City')
    state_id = fields.Many2one('res.country.state', 'State/Province', domain="[('country_id', '=', country_id)]")
    zip = fields.Char('Zip/PostalCode')
    no_of_stores = fields.Integer('No. of Stores')
    website = fields.Char('Website')
    source = fields.Selection([('imported','Imported'),('odoo_contact','Odoo Contact'),('newsletter','Newsletter'),('mixed','Mixed')],'Source')
    prospect_level = fields.Selection([('zero','0'),('one','1')],'Prospect Level')
    status_type = fields.Selection([('b2c','Pending'),('b2b_regular','Verified')],'Status Type')
    action_type = fields.Selection([('confirmed','Confirmed'),('not_connected','Not Connected')],'Action Type')
    orders = fields.Integer('# Orders')
    active = fields.Boolean("Active",default=True)
    # partner_promo_code_ids = fields.Many2many('sale.coupon.program','partner_sale_coupon_program_mailing_contact_real','mailing_contact_id','sale_coupon_id','Partner Promotion Coupons',related='odoo_contact_id.promo_code_ids')
    # promo_code_ids = fields.Many2many('sale.coupon.program','sale_coupon_program_mailing_contact_real','mailing_contact_id','sale_coupon_id','Promotion Coupons',compute='_compute_promocodes',store=True,compute_sudo=True)
    unsubscribe_from_website = fields.Boolean('Unsubscribe from Website')
    salesperson_id = fields.Many2one('res.users',"Salesperson")
    marketing_activities_compute = fields.Boolean(compute="_compute_contact_marketing_activities",compute_sudo=True)
    is_final = fields.Boolean('Final')
    mailgun_verification = fields.Boolean('Is Mailing Partner Verification')
    mailgun_verification_status = fields.Selection([('approved','Mg Approved'),('rejected','MG Rejected')],'MG Status',default="rejected")
   
    def _get_mailgun_status(self):
        for rec in self:
            if rec.mailgun_verification:
                rec.mailgun_verification_status = 'approved'
            else:
                rec.mailgun_verification_status = 'rejected'
    def _compute_contact_marketing_activities(self):
        user_obj = self.env['res.users']
        for rec in self.with_context({'update_salesperson':True}):
            salesperson = rec.odoo_contact_id.user_id.id
            if not salesperson and rec.email:
                salesperson = self.env['res.partner'].search([('email','=',rec.email)],limit=1).user_id.id
            if not salesperson and rec.country_id:
                salesperson = user_obj.search([('contact_allowed_countries','in',rec.country_id.ids)],limit=1).id
            if not salesperson:
                salesperson = int(self.env['ir.config_parameter'].sudo().get_param('default_sales_person_id'))
            rec.salesperson_id = salesperson
            rec.marketing_activities_compute = False

    # @api.depends('partner_promo_code_ids')
    # def _compute_promocodes(self):
    #     for record in self:
    #         record.promo_code_ids = [(6,0,record.partner_promo_code_ids.ids)]

    @api.depends('country_id','country_id.territory_id')
    def _compute_territory(self):
        for record in self:
            territory = False
            if record.country_id:
                territory = self.env['res.country.group'].search([('country_ids','=',record.country_id.id)])
            record.territory = territory[0] if territory else False

    @api.model
    def default_get(self, fields):
        vals = super(mailing_contact,self).default_get(fields)
        vals['internal_id'] = self.env['ir.sequence'].next_by_code('mailing.contact')
        return vals

    @api.model_create_multi
    def create(self,values):
        vals = super(mailing_contact,self).create(values)
        website_contact = request.context.get('website_contact')
        for val in vals:
            if website_contact:
                val.source = 'newsletter'
            if 'email' in values.keys():
                if values['email']:
                    values['email'] = values['email'].lower()
        return vals

    def write(self,values):
        if not self._context.get('update_salesperson',False) and not self._context.get('update_final_flag',False):
            values['is_final'] = False
        vals = super(mailing_contact,self).write(values)
        website_contact = request.context.get('website_contact')
        if website_contact:
            values['source'] = 'newsletter'
        if 'email' in values.keys():
            if values['email']:
                values['email'] = values['email'].lower()
                if not self._context.get('from_cron'):
                    self.mailgun_verification = False 
                    partner_id = self.env['res.partner'].search([('id','=',self.odoo_contact_id.id)])
                    partner_id.mailgun_verification = False
                    partner_id.fail_reason = False
                    partner_id.result = False
                    partner_id.mail_risk = False
        return vals

    def action_assign_mailing_lists(self):
        return {
            "name" :_("Assign Mailing List"),
            "view_mode":"form",
            "type":"ir.actions.act_window",
            "res_model":"mailing.list.assign.wizard",
            "context":{
                "default_mailing_contacts":[(6,0,self.ids)]
            },
            "target":"new",
        }

    @api.constrains('email')
    def _check_email_validation(self):
        for record in self:
            single_email_re = re.compile(r"""^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\D{2,4})+$""", re.VERBOSE)
            if record.email and not single_email_re.match(record.email):
                raise UserError(_('Invalid Email! Please enter a valid email address.'))


    @api.constrains('email')
    def _check_email(self):
        if not self._context.get('force_email'):
            for partner in self:
                if partner.email:
                    partners = partner.search([('email','=',partner.email.lower()),('id','!=',partner.id)])
                    if len(partners) >0:
                        message = "This email is already assigned to "+ partners[0].display_name
                        raise UserError(_(message))
    
    @api.constrains('internal_id')
    def _check_internal_id(self):
        for partner in self:
            if partner.internal_id:
                partners = partner.search([('internal_id','=',partner.internal_id),('id','!=',partner.id)])
                if len(partners) >0:
                    message = "This internal id is already assigned to "+ partners[0].display_name
                    raise UserError(_(message))

    def action_sync_contacts(self):
        partner_ids = False
        if self._context.get('campaign') and self._context.get('partner_id'):
            partner_ids = self.env['res.partner'].search([('id','=',self._context.get('partner_id').id)])
        else:
            partner_ids = self.env['res.partner'].search([])
        res = partner_ids.action_partner_assign_tp_mailing_cantact()
        if not self._context.get('from_cron'):
            return res

    def action_blacklist_contacts(self):
        blacklist_obj = self.env['mail.blacklist']
        for record in self:
            if record.email:
                blacklist_ids  = blacklist_obj.search([('email','=',record.email),'|',('active','=',True),('active','=',False)])
                if blacklist_ids:
                    for blacklist_id in blacklist_ids:
                        blacklist_id.active = True
                else:
                        blacklist_obj.create({'email': record.email,'active': True})

    def action_clear_blacklist_contacts(self):
        blacklist_obj = self.env['mail.blacklist']
        for record in self:
            if record.email:
                blacklist_ids  = blacklist_obj.search([('email','=',record.email),'|',('active','=',True),('active','=',False)])
                if blacklist_ids:
                    blacklist_ids.unlink()
                    # for blacklist_id in blacklist_ids:
                    #     blacklist_id.active = False

    def import_to_oddo_contacts(self):
        partner_obj = self.env['res.partner'].sudo()
        new_created,already_available,not_final = [],[],[]
        for record in self:
            contact = partner_obj.search(['|',('email','=',record.email),('id','=',record.odoo_contact_id.id)],limit=1)
            vals = {
                'name':record.name or '',
                'email':record.email or '',
                'street':record.street or '',
                'street2':record.street2 or '',
                'city':record.city or '',
                'state_id':record.state_id.id or False,
                'zip':record.zip or False,
                'country_id':record.country_id.id or False,
                'territory':record.territory.id or False,
                'phone':record.phone or '',
                'website':record.website or '',
                'user_id':record.salesperson_id.id or False,
                # 'promo_code_ids':record.promo_code_ids.ids or [],
                'company_name':record.company_name or '',
                'title':record.title_id.id or False,
            }
            if not contact:
                if record.is_final:
                    new_partner = partner_obj.create(vals)
                    if new_partner:
                        new_created.append(record.id)
                        record.sudo().write({'odoo_contact_id':new_partner.id,'internal_id':new_partner.internal_id})
                else:
                    not_final.append(record.id)
            else:
                already_available.append(record.id)
                
        success_message = "From the %s mailing contacts %s contacts are successfully exported to contacts."%(len(self),len(new_created))
        failed_message = "%s contacts already exists."%(len(already_available))
        not_final_error = "%s contacts can not be imported beacuse they are not final."%(len(not_final))
        return {
            'name':_('Success'),
            'type':"ir.actions.act_window",
            'res_model':'message.wizard',
            'view_mode':'form',
            'context':{'default_message':success_message,'default_failed_message':failed_message,'default_not_final_contact_error':not_final_error,'default_success_contacts':[(6,0,new_created)],'default_available_contacts':[(6,0,already_available)],'default_not_final_contacts':[(6,0,not_final)]},
            'target':'new',
        }

    def action_do_final(self):
        self.with_context({'update_final_flag':True}).write({'is_final':True})
    
    def action_not_final(self):
        self.with_context({'update_final_flag':True}).write({'is_final':False})

    def action_mailgun_verification(self):
        # for rec in self.filtered(lambda x:x.email and not x.mailgun_verification):
        for rec in self.filtered(lambda x:x.email and x.mailgun_verification_status == 'rejected'):
            partner_id = rec.odoo_contact_id or self.env['res.partner'].search([('email','=',rec.email)])
            rec.fail_reason = False
            rec.result = False
            rec.mail_risk = False
            if partner_id:
                if partner_id.mailgun_verification_status == 'approved':
                    rec.mailgun_verification_status = 'approved'
                    rec._cr.commit()
                else:
                    email_verified = self.email_verification(rec.email)
                    if email_verified.get('result') == 'deliverable':
                        rec.mailgun_verification_status = 'approved'
                        partner_id.mailgun_verification_status = 'approved'
                    else:
                        rec.fail_reason = email_verified.get('reason')[0]
                    rec.result = email_verified.get('result')
                    rec.mail_risk = email_verified.get('risk')
                    rec._cr.commit()
            else:
                email_verified = self.email_verification(rec.email)
                if email_verified.get('result') == 'deliverable':
                    rec.mailgun_verification_status = 'approved'
                else:
                    rec.fail_reason = email_verified.get('reason')[0]
                rec.result = email_verified.get('result')
                rec.mail_risk = email_verified.get('risk')
                rec._cr.commit()

    def email_verification(self,email):
        api_key = self.env['ir.config_parameter'].sudo().get_param('mailgun.webhook.signin.key',False)
        params = {"address":email}
        request = requests.get("https://api.mailgun.net/v4/address/validate",auth=("api", api_key),params=params)
        return request.json()
