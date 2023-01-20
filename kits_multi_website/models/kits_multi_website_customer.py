from odoo import api, fields, models, _
from passlib.context import CryptContext
from lxml import etree
from odoo.exceptions import UserError
DEFAULT_CRYPT_CONTEXT = CryptContext(
    # kdf which can be verified by the context. The default encryption kdf is
    # the first of the list
    ['pbkdf2_sha512', 'plaintext'],
    # deprecated algorithms are still verified as usual, but ``needs_update``
    # will indicate that the stored hash should be replaced by a more recent
    # algorithm. Passlib 1.6 supports an `auto` value which deprecates any
    # algorithm but the default, but Ubuntu LTS only provides 1.5 so far.
    deprecated=['plaintext'],
)

class kits_multi_website_customer(models.Model):
    _name = "kits.multi.website.customer"
    _description = "Kits Multi Website Customer"

    name = fields.Char("Name")
    email = fields.Char("Email")
    password = fields.Char("Password")
    address = fields.Text("Address")
    street = fields.Char("Street")
    street2 = fields.Char("Street2")
    city = fields.Char("City")
    zip = fields.Char("Zip")
    state_id = fields.Many2one("res.country.state", "State")
    country_id = fields.Many2one("res.country", "Country")
    currency_id = fields.Many2one("res.currency", "Currency",related="country_id.currency_id")
    website_id = fields.Many2one("kits.b2c.website","Website")
    wallet_amount = fields.Float("Wallet Amount", compute="_compute_wallet_amount")
    wallet_transaction_line_ids = fields.One2many("kits.multi.website.wallet.transaction","customer_id","Transaction Lines")
    url_validity = fields.Datetime("URL Validity")
    reset_password_url = fields.Text("Reset Password Url")
    token = fields.Text("Token")
    firstname = fields.Char("Firstname")
    lastname = fields.Char("Lastname")
    confirm_password = fields.Char("Confirm Password")
    customer_token_line_ids = fields.One2many('kits.multi.website.customer.token.line','customer_id','Customer Token Lines')
    contact_no = fields.Char("Contact No")
    address_ids = fields.One2many("kits.multi.website.address","customer_id","Addresses")
    sign_up_verified = fields.Boolean("Sign Up Verified")
    dob = fields.Date("Date of birth")
    gender = fields.Selection([('male','Male'),('female','Female'),('other','Other')],string="Gender")
    is_guest = fields.Boolean('Is Guest')
    # @Fenil
    recent_view_count = fields.Integer('#Recent Views',compute='_compute_recent_views')
    wishlist_count = fields.Integer('#Wishlist',compute='_compute_recent_views')
    preferred_language = fields.Selection([('af','Afrikaans'),('sq','Albanian'),('am','Amharic'),('ar','Arabic'),('hy','Armenian'),('az','Azerbaijani'),('eu','Basque'),('be','Belarusian'),('bn','Bengali'),('bs','Bosnian'),('bg','Bulgarian'),('my','Burmese'),('ca','Catalan'),('ceb','Cebuano'),('ny','Chichewa'),('zh-CN','Chinese/Simplified'),('zh-TW','Chinese/Traditional'),('co','Corsican'),('hr','Croatian'),('cs','Czech'),('da','Danish'),('nl','Dutch'),('en','English'),('eo','Esperanto'),('et','Estonian'),('tl','Filipino'),('fi','Finnish'),('fr','French'),('fy','Frisian'),('gl','Galician'),('ka','Georgian'),('de','German'),('el','Greek'),('gu','Gujarati'),('ht','Haitian Creole'),('ha','Hausa'),('haw','Hawaiian'),('iw','Hebrew'),('hi','Hindi'),('hmn','Hmong'),('hu','Hungarian'),('is','Icelandic'),('ig','Igbo'),('id','Indonesian'),('ga','Irish Gaelic'),('it','Italian'),('ja','Japanese'),('jw','Javanese'),('kn','Kannada'),('kk','Kazakh'),('km','Khmer'),('rw','Kinyarwanda'),('ko','Korean'),('ku','Kurdish/Kurmanji'),('ky','Kyrgyz'),('lo','Lao'),('la','Latin'),('lv','Latvian'),('lt','Lithuanian'),('lb','Luxembourgish'),('mk','Macedonian'),('mg','Malagasy'),('ms','Malay'),('ml','Malayalam'),('mt','Maltese'),('mi','Maori'),('mr','Marathi'),('mn','Mongolian'),('ne','Nepali'),('no','Norwegian'),('or','Odia/Oriya'),('ps','Pashto'),('fa','Persian'),('pl','Polish'),('pt','Portuguese'),('pa','Punjabi'),('ro','Romanian'),('ru','Russian'),('sm','Samoan'),('gd','Scots Gaelic'),('sr','Serbian'),('st','Sesotho'),('sn','Shona'),('sd','Sindhi'),('si','Sinhala'),('sk','Slovak'),('sl','Slovenian'),('so','Somali'),('es','Spanish'),('su','Sundanese'),('sw','Swahili'),('sv','Swedish'),('tg','Tajik'),('ta','Tamil'),('tt','Tatar'),('te','Telugu'),('th','Thai'),('tr','Turkish'),('tk','Turkmen'),('uk','Ukrainian'),('ur','Urdu'),('ug','Uyghur'),('uz','Uzbek'),('vi','Vietnamese'),('cy','Welsh'),('xh','Xhosa'),('yi','Yiddish'),('yo','Yoruba'),('zu','Zulu')],'Preferred Language Code',default='en')
    preferred_currency_id = fields.Many2one('res.currency','Preferred Currency')
    property_account_position_id = fields.Many2one('account.fiscal.position', company_dependent=True,
        string="Fiscal Position",
        help="The fiscal position determines the taxes/accounts used for this contact.")

    _sql_constraints = [
        ('unique_multi_website_customer_contact_no', 'UNIQUE(contact_no)','Customer with same Contact already exists!'),
        ('unique_multi_website_customer_email', 'UNIQUE(email)','Customer with same Email already exists!')
    ]

    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_customer, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res

    def name_get(self):
        result = []
        for record in self:
            name = ''
            if record.firstname:
                name = record.firstname.capitalize()
            if record.lastname:
                name = name  + ' ' + record.lastname.capitalize()
            result.append((record.id,name))
        return result

    def _crypt_context(self):
        return DEFAULT_CRYPT_CONTEXT
    
    def _get_encrypted_password(self,pw):
        # return the encrypted pw
        return self._crypt_context().encrypt(pw)

    def _compute_wallet_amount(self):
        for record in self:
            record.wallet_amount = 0
            wallet_transaction_ids = self.env['kits.multi.website.wallet.transaction'].search([('customer_id','=',record.id)])
            if wallet_transaction_ids:
                record.wallet_amount = sum(wallet_transaction_ids.mapped('amount'))

    @api.onchange('country_id')
    def _get_states(self):
        return{'domain': {'state_id': [('country_id','=',self.country_id.id)]}}

    def change_password(self):
        form_view_id = self.env.ref("kits_multi_website.kits_multi_website_change_password_form_view")
        return{
            'name': ('Change Password'), 
            'res_model': 'kits.multi.website.change.password',
            'type': 'ir.actions.act_window',
            'views': [(form_view_id.id, 'form')],
            'context': {'default_email':self.email, 'default_customer_id': self.id},
            'target': 'new',
        }

    @api.model
    def send_email(self,customer_email):
        customer_id = self.env['kits.multi.website.customer'].search([('email','=',customer_email)])
        if customer_email:
            mail_template = self.env.ref('kits_multi_website.multi_website_email_template')
            mail_template.sudo().send_mail(customer_id.id,force_send=True)
            return {"email_sent":True,"error": False}
        else:
            return {"email_sent":False,"error": "Customer Not Found"}

    def action_open_wallet_logs(self):
        form_view_id = self.env.ref('kits_multi_website.kits_multi_website_wallet_transaction_form_view')
        tree_view_id = self.env.ref('kits_multi_website.kits_multi_website_wallet_transaction_tree_view')
        return{
            'name': ('Wallet Transactions'), 
            'res_model': 'kits.multi.website.wallet.transaction',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id.id, 'tree'),(form_view_id.id, 'form')],
            'domain': [('customer_id','=',self.id)],
            'target': 'current',
        }

    def _compute_recent_views(self):
        for record in self:
            recent_views = self.env['kits.multi.website.recent.view'].search([('customer_id','=',record.id)],limit=1)
            record.recent_view_count = len(set(recent_views.mapped('product_id')))
            record.wishlist_count = len(set(self.env['kits.multi.website.wishlist'].search([('customer_id','=',record.id)]).mapped('product_id')))

    def action_show_recent_views(self):
        self.ensure_one()
        recent_view_ids = self.env['kits.multi.website.recent.view'].search([('customer_id','=',self.id)],limit=1)
        return {
            'name':_('Recent Views'),
            'type':'ir.actions.act_window',
            'res_model':'kits.multi.website.recent.view',
            'view_mode':'tree',
            'domain':[('id','in',recent_view_ids.ids)],
            'context':{'create':0,'edit':0,'delete':0,'duplicate':0,'import':0,'action':0},
            'target':'self',
        }
    def unlink(self):
        error = {}
        for record in self:
            error_list = []
            if self.env['kits.multi.website.invoice'].search([('customer_id','=',record.id)]):
                error_list.append(" invoice")
            
            if self.env['kits.multi.website.sale.order'].search([('customer_id','=',record.id)]):
                error_list.append(" sale order")
            
            if self.env['kits.multi.website.wallet.transaction'].search([('customer_id','=',record.id)]):
                error_list.append(" wallet transaction")
            

            if self.env['kits.multi.website.recent.view'].search([('customer_id','=',record.id)]):
                error_list.append(" recent view")
            

            if self.env['kits.multi.website.wishlist'].search([('customer_id','=',record.id)]):
                error_list.append(" wishlist")
            if error_list:
                if str(record.display_name) in error.keys():
                    error[str(record.display_name)] = error[str(record.display_name)].extend(error_list)
                else:
                    error[str(record.display_name)] = error_list
        if error:
            raise UserError(_(','.join(list([cus+' customer have'+','.join(error[cus])+', so can not delete this customer' for cus in error]))))
        return super(kits_multi_website_customer,self).unlink()

    @api.constrains('country_id,state_id,zip,city,street')
    def _constrains_property_account_position_id(self):
        position_id = self.env['account.fiscal.position'].search([('country_id','=',False)],limit=1).id
        for record in self:
            record.property_account_position_id = record.property_account_position_id._get_fpos_by_region(record.country_id.id,record.state_id.id, record.zip)
            if not record.property_account_position_id:
                record.property_account_position_id= position_id
    
    
    def action_show_wishlist(self):
        self.ensure_one()
        wishlist_ids = self.env['kits.multi.website.wishlist'].search([('customer_id','=',self.id)])
        return{
            'name': ('Wishlist'),
            'res_model': 'kits.multi.website.wishlist',
            'type': 'ir.actions.act_window',
            'views': [(self.env.ref('kits_multi_website.kits_multi_website_wishlist_view_tree').id, 'tree')],
             'view_mode':'tree',
            'domain':[('id','in',wishlist_ids.ids)],
            'context':{'create':0,'edit':0,'delete':0,'duplicate':0,'import':0,'action':0},
            'target':'self',
            'context':{'create':0,'edit':0,'delete':0,'duplicate':0,'import':0,'action':0},
        }
