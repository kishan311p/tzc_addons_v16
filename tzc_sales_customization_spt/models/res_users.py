from odoo import _, api, fields, models, tools
from odoo.http import request
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from odoo.exceptions import UserError, ValidationError
import logging
import uuid
from lxml import etree

_logger = logging.getLogger(__name__)
class res_users(models.Model):
    _name = 'res.users'
    _inherit = ['res.users','mail.thread']
    
    def _get_default_commission_rule(self):
        commission_id = False
        try:
            default_commission = eval(self.env['ir.config_parameter'].sudo().get_param('kits_sale_commission.commission_id'))
            if self.env['ir.config_parameter'].browse(commission_id).commission_for == 'sales_person':
                commission_id = default_commission
        except:
            pass
        return commission_id
    def _get_manager_domain(self):
        try:
            users = self.env.ref('tzc_sales_customization_spt.group_sales_manager_spt').sudo().users
            return [('id','in',users.ids)]
        except:
            return []

    is_salesperson = fields.Boolean('Is Salesperson',compute="_compute_is_sales_person",store=True,compute_sudo=True)
    manager_id = fields.Many2one('res.users',"Manager ",domain=_get_manager_domain)
    allow_user_ids = fields.One2many('res.users','manager_id','Sales Persons')
    is_email_verified = fields.Boolean(string='User Verified')
    country_ids = fields.Many2many('res.country','spt_res_user_res_country_rel','res_user_id','res_country_id','Sales Person\'s Notification Countries',tracking=True)
    show_country_ids = fields.Boolean(compute="_compute_show_country_ids")
    contact_allowed_countries = fields.Many2many('res.country','res_user_contact_allowed_country_rel','res_user_id','res_country_id','Sales Manager\'s  Designated Countries',tracking=True)
    is_internal_user = fields.Boolean(string="Is Internal User")
    show_contact_allowed_countries = fields.Boolean(compute="_compute_show_allowed_countries")
    manager_country_ids = fields.Many2many('res.country','res_country_manager_country_rel','res_user_id','res_manager_country_id',compute="_compute_manager_country_ids",string="Manager's Countries")

    is_warehouse = fields.Boolean("Is Wareshouse")    
    hidden_menu_ids = fields.Many2many('ir.ui.menu','ir_ui_menu_res_users_rel','menu_id','user_id','Hidden Menus')
    commission_rule_id = fields.Many2one('kits.commission.rules','Salesperson Commission Rule',default=_get_default_commission_rule)
    is_sales_manager = fields.Boolean('Is Sales Manager',compute="_compute_is_sales_manager")
    manager_commission_rule_id = fields.Many2one('kits.commission.rules','Manager Commission rule')
    signup_user_ip = fields.Char('Signup User IP ')
    alias_id = fields.Many2one('mail.alias', 'Alias', ondelete="set null", required=False,
            help="Email address internally associated with this user. Incoming "\
                 "emails will appear in the user's notifications.", copy=False, auto_join=True)
    alias_contact = fields.Selection([
        ('everyone', 'Everyone'),
        ('partners', 'Authenticated Partners'),
        ('followers', 'Followers only')], string='Alias Contact Security', related='alias_id.alias_contact', readonly=False)
    def _get_internal_salesperson_id(self):
        for record in self:
            if record.partner_id:
                record.internal_salesperson_id = record.partner_id.internal_id

    internal_salesperson_id = fields.Char('Internal ID',compute='_get_internal_salesperson_id')
    customer_count = fields.Integer('Customer Count',compute="_compute_customer_count")

    def _get_default_access_token(self):
        return str(uuid.uuid4())

    is_validate = fields.Boolean(string='Validate User')
    redirect_url = fields.Char('redirect_url')
    access_token = fields.Char('Security Token', copy=False, default=_get_default_access_token)
    show_country_ids = fields.Boolean(compute="_compute_show_country_ids")
    is_internal_user = fields.Boolean(string="Is Internal User")
    show_contact_allowed_countries = fields.Boolean(compute="_compute_show_allowed_countries")
    manager_country_ids = fields.Many2many('res.country','res_country_manager_country_rel','res_user_id','res_manager_country_id',compute="_compute_manager_country_ids",string="Manager's Countries")
    is_email_verified = fields.Boolean(string='User Verified')

    # wk_website_loyalty_points = fields.Float(
    #     related='partner_id.wk_website_loyalty_points'
    # )
    # token_ids = fields.One2many('kits.b2b.user.token', 'user_id', string='Token')

    @api.depends('groups_id')
    def _compute_is_sales_person(self):
        for rec in self:
            rec.is_salesperson = rec.has_group('sales_team.group_sale_salesman')
    
    def _is_salesmanager(self):
        self.ensure_one()
        return self.has_group('tzc_sales_customization_spt.group_sales_manager_spt')

    def _compute_manager_country_ids(self):
        managers = self.env['res.users'].search([('allow_user_ids','in',self.ids)])
        self.manager_country_ids = [(6,0,managers.mapped('contact_allowed_countries').ids)]

    def _compute_show_allowed_countries(self):
        if self.has_group("tzc_sales_customization_spt.group_sales_manager_spt"):
            self.show_contact_allowed_countries = True
        else:
            self.show_contact_allowed_countries = False
        self.is_internal_user= self.has_group('base.group_user')

    @api.constrains('country_ids','contact_allowed_countries')
    def check_country_assign(self):
        message =''
        user_obj = self.env['res.users']
        can_not_assign = []
        if self.country_ids:
            for country_id in self.country_ids:
                user_id = user_obj.search([('id','!=',self.id),('is_salesperson','=',True),('country_ids','in',country_id.ids)])
                if user_id and user_id.id:
                    can_not_assign.append("Country %s is already assigned to %s sales person."%(country_id.name,user_id.name))
        if self.contact_allowed_countries:
            for allow_country_id in self.contact_allowed_countries:
                user_id = user_obj.search([('id','!=',self.id),('is_salesmanager','=',True),('contact_allowed_countries','in',allow_country_id.ids)])
                if user_id:
                    can_not_assign.append("Country %s is already assigned to %s sales manager."%(allow_country_id.name,','.join(user_id.mapped('name'))))
        if len(can_not_assign) > 0:
            message = '\n'.join(can_not_assign)
            print(message)
            raise UserError(_(message))

    # @api.depends('is_salesperson')
    def _compute_show_country_ids(self):
        if self.is_salesperson == True or self.has_group("tzc_sales_customization_spt.group_sales_manager_spt"):
            self.show_country_ids = True
        else:
            self.show_country_ids = False

    @api.model
    def _fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(res_users, self)._fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if view_type == 'form':
            doc = etree.fromstring(res['arch'])
            for manager_id in doc.xpath("//field[@name='manager_id']"):
                manager_id.attrib['readonly'] = '0' if self.env.user.has_group('base.group_system') else '1'
            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res
    
    # def write(self,vals):
    #     if self.contact_allowed_countries:
    #         if vals.get('contact_allowed_countries') and (not vals.get('contact_allowed_countries')[0][-1] or vals.get('contact_allowed_countries')[0][0] == 5):
    #             if self._context.get('active_model') and self._context.get('active_model') != 'res.users':
    #                 raise UserError('You can not remove Sales manager designated countries.')
    #     return super(res_users,self).write(vals)

    def action_archive_uers(self):
        user_ids = self
        customer_ids_list = []
        for user in self:
            customer_ids = self.env['res.partner'].search([('user_id','=',user.id)])
            customer_ids_list.extend(customer_ids.ids)
            if customer_ids:
                user_ids -= user 

        # sales_person_manager = self.filtered(lambda x:x.is_salesperson or x.is_salesmanager).ids
        # success_message = "Out of %s users %s users will going to be archived."%(len(self),len(self - self.browse(sales_person_manager)))
        # failed_message = 'The following %s users will not going to be archived because they might be salesperson or sales manager.'%(len(sales_person_manager))
        success_message = "Out of %s users %s users will going to be archived."%(len(self),len(user_ids))
        failed_message = 'This internal user is set as a salesperson, so you can not archive it. Please change the salesperson in the following contact.'
        return {
                'name': _('User Messages'),
                'type': 'ir.actions.act_window',
                'res_model': "error.message.wizard",
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_success_message':success_message,
                    "default_failed_message":failed_message,
                    'default_failed_user_ids':[(6,0,(self - user_ids).ids)],
                    'default_user_ids': [(6,0,self.ids)],
                    'default_failed_partner_ids': [(6,0,customer_ids_list)],
                }
            }

    def action_unarchive_uers(self):
        for rec in self:
            rec.active = True

    def unlink(self):
        try:
            return super(res_users,self).unlink()
        except Exception as e:
            raise UserError('This user cannot be deleted since there might be some data attached to it. You may delete those data and try again.\n\n'+e.pgerror)
    
    def render_template(self):
        if self._context.get('error_report'):
            template_id = self.env.ref('tzc_sales_customization_spt.error_msg_mail_template').sudo()
            template_id.send_mail(res_id=self.env.user.id, force_send=True,notif_layout="mail.mail_notification_light")
    @api.model
    def create(self, values):
        self.env['ir.ui.menu'].clear_caches()
        if 'email' in values.keys() and values['email']:
            values.update({'email':values['email'].lower()})
        # ir_model_data = self.env['ir.model.data']
        # portal_user_id = ir_model_data.get_object_reference(
        #     'base', 'group_portal')[1]
        # wk_loyalty_program_id = self.env['website'].sudo().get_current_website().wk_loyalty_program_id
        # groups_id = values.get('groups_id')
        # portal_signup = (self.env.ref('base.group_portal').id in groups_id[0][2]) if groups_id else False
        # if wk_loyalty_program_id  and (portal_signup or values.get('in_group_1')):
        #     wk_website_loyalty_points = wk_loyalty_program_id._fetch_signup_loyalty_points()
        #     if wk_website_loyalty_points:
        #         values['wk_website_loyalty_points'] = wk_website_loyalty_points
        #         res = super(res_users, self).create(values)
        #         res.partner_id.wk_website_loyalty_points =wk_website_loyalty_points
        #         history_vals = {
        #             'partner_id': res.partner_id.id,
        #             'loyalty_id': wk_loyalty_program_id.id,
        #             'points_processed': wk_website_loyalty_points,
        #             'loyalty_process': 'addition',
        #             'process_reference': 'Sign Up',
        #         }

        #         self.env['website.loyalty.history'].sudo().create(history_vals)

        return super(res_users, self).create(values)

    def write(self, values):
        self.env['ir.ui.menu'].clear_caches()
        if 'contact_allowed_countries' in values.keys() or 'country_ids' in values.keys(): 
            self = self.with_context({'mail_create_nosubscribe':True,'tracking_disable':False})
        else:
            self = self.with_context({'mail_create_nosubscribe':True,'tracking_disable':True})
        if 'is_salesperson' in values and values['is_salesperson']:
            values.update({'commission_rule_id':self._get_default_commission_rule()})
	
        if 'email' in values.keys() and values['email']:
            values.update({'email':values['email'].lower()})
        return super(res_users, self).write(values)

    @api.depends('groups_id')
    def _compute_is_sales_manager(self):
        for rec in self:
            rec.is_sales_manager = rec.has_group('tzc_sales_customization_spt.group_sales_manager_spt')

    def kits_b2b_user_verification_sent_email(self):
        mail_template = self.env.ref('kits_b2b_website.mail_template_user_signup_confirmation')
        mail_template.sudo().send_mail(res_id= self.id,force_send=True)
        return{}

    
    def get_image(self):
        return {'image': self.partner_id.image_128}

    def action_change_salesperson_rule(self):
        return {
            'name':_('Change Salesperson Commission'),
            'type':'ir.actions.act_window',
            'res_model':'kits.change.commission.rule',
            'view_mode':'form',
            'context':{'default_commission_of':'saleperson','default_user_id':self.id},
            'target':'new',
            }
    
    def action_change_salesmanager_rule(self):
        return {
            'name':_('Change Salesperson Commission'),
            'type':'ir.actions.act_window',
            'res_model':'kits.change.commission.rule',
            'view_mode':'form',
            'context':{'default_commission_of':'manager','default_user_id':self.id},
            'target':'new',
            }

    @api.model
    def _check_credentials(self, password,env):
        result = super(res_users, self)._check_credentials(password,self.env)
        # ip_address = request.httprequest.environ['REMOTE_ADDR']
        # vals = {'name': self.name,
        #         'ip_address': ip_address
        #         }
        # self.env['login.detail'].sudo().create(vals)
        return result

    def action_reset_password(self):
        """ create signup token for each user, and send their signup url by email """
        # prepare reset password signup
        create_mode = bool(self.env.context.get('create_user'))

        # no time limit for initial invitation, only for reset password
        expiration = False if create_mode else now(days=+1)

        self.mapped('partner_id').signup_prepare(signup_type="reset", expiration=expiration)

        # send email to users with their signup url
        template = False
        if create_mode:
            try:
                template = self.env.ref('portal.mail_template_data_portal_welcome',raise_if_not_found=False)
            except ValueError:
                pass
        if not template:
            template = self.env.ref('auth_signup.reset_password_email')
        assert template._name == 'mail.template'

        template_values = {
            'email_to': '{{ (object.email) }}',
            'email_cc': False,
            'auto_delete': True,
            'partner_to': False,
            'scheduled_date': False,
        }
        template.write(template_values)

        for user in self:
            if not user.email:
                raise UserError(_("Cannot send email: user %s has no email address.") % user.name)
            with self.env.cr.savepoint():
                force_send = not(self.env.context.get('import_file', False))
                if create_mode:
                    wizard_id = self.env['portal.wizard'].create({"user_ids":[(6,0,self.ids)]})
                    portal_user = self.env['portal.wizard.user'].create({'user_id':user.id,'partner_id':user.partner_id.id,'wizard_id':wizard_id.id})
                    template.with_context(lang=user.lang).send_mail(portal_user.id, force_send=True, raise_exception=True,email_values={'recipient_ids':[(6,0,user.partner_id.ids)]})
                    _logger.info("Invitation email sent for user <%s> to <%s>", user.login, user.email)
                else:
                    template.with_context(lang=user.lang).send_mail(user.id, force_send=force_send, raise_exception=True)
                    _logger.info("Password reset email sent for user <%s> to <%s>", user.login, user.email)


    def action_sent_mail_spt(self):
        partner_ids = self.mapped('partner_id').filtered(lambda x: x.mailgun_verification_status == 'approved' and x.email).ids
        none_mails_partner_ids = self.mapped('partner_id').filtered(lambda x: not x.email).ids
        # mail_context = self._context.copy()
        message = 'Out of %s user %s user is eligible for mail.'%(len(self),len(partner_ids))
        return {
            'name': _('Send Mail'),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'binding_model':"res.partner",
            'view_mode' : 'form',
            'target': 'new',
            'context':{
                        'default_model': 'res.partner',
                        'default_partner_to': ','.join(str(id) for id in partner_ids),
                        'default_template_id': self.env.ref('tzc_sales_customization_spt.email_template_partner').id,
                        'default_composition_mode': 'mass_mail',
                        'campaign':True,
                        'raise_campaign':True,
                        'none_mails_partner_ids':none_mails_partner_ids,
                        'email_partner_ids':self.mapped('partner_id').ids,
                        'wiz_message':message,
                        'verify_partner_ids':partner_ids,
                        'default_mail_server_id':eval(self.env['ir.config_parameter'].sudo().get_param('mass_mailing.mail_server_id')),
                        'active_model':'mass.mailing.message.wizard',
                    },
        }
        # rejected_partner_ids = self.mapped('partner_id').filtered(lambda x: x.mailgun_verification_status == 'rejected').ids
        # if rejected_partner_ids:
        #     return self.mailgun_varified()
        # user_ids = self.mapped('partner_id').filtered(lambda x: not x.email).ids
        # mail_context = self._context.copy()
        # message = 'From the %s users %s user%s have no email.'%(len(self),len(user_ids),'s' if len(user_ids) > 1 else '')
        # if user_ids:
        #     mail_context.update({
        #                 'default_partner_ids':user_ids,
        #                 'default_email_partner_ids':self.mapped('partner_id').ids,
        #                 'default_message':message,
        #                 'active_model':'res.partner'
        #             })
        #     return {
        #             'name': _('Mass Mailing Message Wizard'),
        #             'type': 'ir.actions.act_window',
        #             'res_model': "user.mass.mailing.wizard",
        #             'view_type': 'form',
        #             'view_mode': 'form',
        #             'target': 'new',
        #             'context':mail_context,
        #         }
        # else:
        #     mail_context.update({
        #                     'default_composition_mode': 'mass_mail',
        #                     'default_partner_to': ','.join(str(id.id) for id in self.mapped('partner_id')),
        #                     'default_use_template': True,
        #                     'default_template_id': self.env.ref('mail.email_template_partner').id,
        #                     'default_no_auto_thread':False,
        #                     'default_model':"res.partner",
        #                     'user_bulk_mail':True,
        #                     'campaign':True,
        #                     'default_mail_server_id':eval(self.env['ir.config_parameter'].sudo().get_param('mass_mailing.mail_server_id')),
        #                     'raise_campaign':True,
        #                 })
        #     return {
        #         'name': _('Send Mail'),
        #         'type': 'ir.actions.act_window',
        #         'res_model': 'mail.compose.message',
        #         'view_mode' : 'form',
        #         'target': 'new',
        #         'context':mail_context,
        #     }
        
    def mailgun_varified(self):
        # partner_ids = self.filtered(lambda x: x.mailgun_verification == False)
        partner_ids = self.mapped('partner_id').filtered(lambda x: x.mailgun_verification_status == 'approved' and x.email).ids
        none_mails_partner_ids = self.mapped('partner_id').filtered(lambda x: not x.email).ids
        mail_context = self._context.copy()
        message = 'Out of %s user %s user is eligible for mail.'%(len(self),len(partner_ids))
        mail_context.update({
                    'default_partner_ids':partner_ids,
                    'default_none_mails_partner_ids':none_mails_partner_ids,
                    'default_email_partner_ids':self.mapped('partner_id').ids,
                    'default_message':message,
                    # 'campaign' : True,
                    # 'raise_campaign':True,
                })
        return {
                'name': _('User Mailgun Verification Wizard'),   
                'type': 'ir.actions.act_window',
                'res_model': "mass.mailing.message.wizard",
                'view_type': 'form',
                'view_mode': 'form',
                'target': 'new',
                'context':mail_context,
            }

    def action_user_customer(self):
        tree_view = self.env.ref('base.view_partner_tree')
        form_view = self.env.ref('base.view_partner_form')
        record = self.get_filtere_contact()

        action = {
            'name': _('Customers'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'view_mode' : 'tree,form',
            'views': [(tree_view.id,'tree'),(form_view.id,'form')],
            'target': 'current',
            'domain':[('id','in',record.ids)],
        }
        return action

    def get_filtere_contact(self):
        rec = self.env['res.partner']
        if self.has_group('base.group_system') or self.has_group('tzc_sales_customization_spt.group_partner_access_manager'):
            rec |= rec.search([(1,'=',1)])
        else:
            if self.has_group('base.group_user'):
                rec |= rec.search(['|',('id','=',self.partner_id.id),('is_user_internal','=',True)])
            if self.has_group('tzc_sales_customization_spt.group_partner_access_salesperson'):
                rec |= rec.search(['|',('user_id','=',self.id),('id','=',self.partner_id.id)])
            if self.has_group('base.group_portal') or self.has_group('base.group_public'):
                rec |= rec.search([('id', 'child_of', self.commercial_partner_id.id)])
            if self.has_group('tzc_sales_customization_spt.group_sales_manager_spt'):
                rec |= rec.search(['|','|',('user_ids','in',self.allow_user_ids.ids),('user_id','in',self.allow_user_ids.ids),('country_id','in',self.contact_allowed_countries.ids)])
            if self.has_group('base.group_private_addresses'):
                rec |= rec.search([('type','=','private')])
        return rec

    def action_delete_user(self):
        deleted_ids = []
        archived_count = 0
        deleted_count = 0
        for rec in self:
            if self.env.user.has_group('base.group_system') or self.env.user.has_group('tzc_sales_customization_spt.group_sales_manager_spt'):
                try:
                    rec.active = False
                    rec._cr.commit()
                    rec.unlink()
                    deleted_ids.append(rec.id)
                    deleted_count += 1
                except:
                    self._cr.rollback()
                    user_id = self.exists()
                    deleted_ids.append(rec.id)
                    archived_count += 1
                    pass
            else:
                raise UserError(_('Due to security restrictions, you are not allowed to access "User" (res.users) records \n Contact your administrator to request access if necessary.'))
        if deleted_ids:
            message = (f'Out of {archived_count + deleted_count} users {deleted_count} is deleted and following {archived_count} is archived')
            return {
                    'name':_('Confirm Delete'),
                    'type':'ir.actions.act_window',
                    'res_model':'kits.confirm.contact.delete.wizard',
                    'view_mode':'form',
                    'context':{'default_user_ids':[(6,0,deleted_ids)],'default_message':message,},
                    'target':'new',
                }


    def _compute_customer_count(self):
        record = self.get_filtere_contact()
        self.customer_count = len(record)


    def reset_password(self, login):
        """ retrieve the user corresponding to login (login or email),
            and reset their password
        """
        users = self.search([('login', '=', login)])
        if not users:
            users = self.search([('email', '=', login)])
        if len(users) != 1:
            raise Exception(_("Sorry, we don't recognize your email address. Did you use a different email when you registered?"))
        return users.action_reset_password()
    
    def _update_last_login(self):
        if self.is_email_verified: 
            self.env['res.users.log'].create({})


class LoginUpdate(models.Model):
    _name = 'login.detail'
    _description = 'Login Details'

    name = fields.Char(string="User Name")
    date_time = fields.Datetime(string="Login Date And Time", default=lambda self: fields.datetime.now())
    ip_address = fields.Char(string="IP Address")
