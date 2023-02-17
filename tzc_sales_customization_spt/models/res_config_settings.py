# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class res_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    kits_abandone_mail_delay = fields.Integer('Abandoned mail delay')
    catalog_delay = fields.Integer('Catalog Delay In Minutes')
    order_delay = fields.Integer('Order Delay In Minutes')
    # on_sale_cad_spt = fields.Float('On Sale CAD Rate')
    to_notify_user_ids = fields.Many2many('res.users','crm_res_config_settings_res_users_rel_spt','res_config_settings','res_users','Salespersons')
    new_arraival_remove_after = fields.Integer('Remove Products from New Arrivals After (Days)')
    # reset_pass_expire_hours = fields.Integer('Reset Password Link Expiration In Hours')
    case_weight_gm = fields.Float('Weight for cases (gm)',config_parameter="tzc_case_weight_gm",default="")
    kits_global_tax = fields.Many2one('account.tax','Sunglass Tax',config_parameter="tzc_sales_customization_spt.kits_global_tax",default="")
    commission_id = fields.Many2one('kits.commission.rules',default_model="kits.commission.rules",string="Default Commission",ondelete="restrict")
    default_sales_person_id = fields.Many2one('res.users','Default Salesporson', default_model='res.users')
    user_ids_spt = fields.Many2many('res.users','config_user_real','config_id','user_id','Notify Internal Users')
    cart_abandoned_delay = fields.Float(string="Send After")
    cart_recovery_mail_template = fields.Many2one('mail.template', string='Cart Recovery Email', domain="[('model', '=', 'sale.order')]")
    kits_shipping_method = fields.Boolean('Display Shipping Method')
    @api.model
    def get_values(self):
        res = super(res_config_settings, self).get_values()
        res['kits_shipping_method'] = eval(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.kits_shipping_method','False'))
        try:
            res['kits_abandone_mail_delay'] = int(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.kits_abandone_mail_delay','3'))
        except:
            res['kits_abandone_mail_delay'] = 3
        
        default_sales_person_id = self.env['ir.config_parameter'].sudo().get_param('default_sales_person_id', False)
        cart_recovery_mail_template = self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.cart_recovery_mail_template', default=None)
        try:
            res['commission_id'] = eval(self.env['ir.config_parameter'].sudo().get_param('kits_sale_commission.commission_id'))
        except:
            res['commission_id'] = False
        res['catalog_delay'] = int(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.catalog_delay', default=0))
        res['order_delay'] = int(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.order_delay', default=0))
        # res['on_sale_cad_spt'] = float(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.on_sale_cad_spt', default=0))
        res['to_notify_user_ids'] = [(6,0,eval(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.to_notify_user_ids', default='[]')))]
        res['new_arraival_remove_after'] = int(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.new_arraival_remove_after',default='5'))
        # res['reset_pass_expire_hours'] = int(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.reset_pass_expire_hours',default='24'))
        res['user_ids_spt'] = [(6,0,eval(self.env['ir.config_parameter'].sudo().get_param('user_ids_spt', '[]')))]
        res['default_sales_person_id'] = eval(default_sales_person_id) if default_sales_person_id else False
        res['cart_abandoned_delay'] = eval(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.cart_abandoned_delay') or '10')
        res['cart_recovery_mail_template'] = eval(cart_recovery_mail_template) if cart_recovery_mail_template else None
        return res

    @api.model
    def set_values(self):
        product_obj = self.env['product.product']
        self.env['ir.config_parameter'].sudo().set_param('tzc_sales_customization_spt.kits_shipping_method',self.kits_shipping_method)
        self.env['ir.config_parameter'].sudo().set_param('tzc_sales_customization_spt.kits_abandone_mail_delay',self.kits_abandone_mail_delay)
        self.env['ir.config_parameter'].sudo().set_param('tzc_sales_customization_spt.cart_recovery_mail_template', self.cart_recovery_mail_template.id)
        self.env['ir.config_parameter'].sudo().set_param('tzc_sales_customization_spt.cart_abandoned_delay', self.cart_abandoned_delay or 10)
        self.env['ir.config_parameter'].sudo().set_param('kits_sale_commission.commission_id', self.commission_id.id)
        self.env['ir.config_parameter'].sudo().set_param('tzc_sales_customization_spt.catalog_delay', self.catalog_delay)
        self.env['ir.config_parameter'].sudo().set_param('tzc_sales_customization_spt.order_delay', self.order_delay)
        # self.env['ir.config_parameter'].sudo().set_param('tzc_sales_customization_spt.on_sale_cad_spt', self.on_sale_cad_spt)
        self.env['ir.config_parameter'].sudo().set_param('tzc_sales_customization_spt.to_notify_user_ids', self.to_notify_user_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('tzc_sales_customization_spt.new_arraival_remove_after', self.new_arraival_remove_after)
        self.env['ir.config_parameter'].sudo().set_param('user_ids_spt', self.user_ids_spt.ids if self.user_ids_spt else [])
        self.env['ir.config_parameter'].sudo().set_param('default_sales_person_id', self.default_sales_person_id.id if self.default_sales_person_id else False)
        # self.env['ir.config_parameter'].sudo().set_param('tzc_sales_customization_spt.reset_pass_expire_hours', self.reset_pass_expire_hours)
        # product_ids = product_obj.search([('sale_type','!=',False),'|',('active','=',True),('active','=',False)])
        # for product_id in product_ids:
        #     on_sale_cad = 0.00
        #     on_sale_cad_in_percentage = 0.00
        #     if product_id.on_sale_cad:
        #         on_sale_cad = round(product_id.on_sale_usd * self.on_sale_cad_spt,2)
        #         if on_sale_cad and product_id.lst_price:
        #             on_sale_cad_in_percentage = round((1 -(on_sale_cad/product_id.lst_price))*100,2)

        #     product_id.on_sale_cad = on_sale_cad
        #     product_id.on_sale_cad_in_percentage = on_sale_cad_in_percentage
        
        # order_delay = 5
        # catalog_delay = 5
        # if not self.catalog_delay <= 0:
        #     catalog_delay = self.catalog_delay
        # if not self.order_delay <= 0:
        #     order_delay = self.order_delay
        # self.env.ref('tzc_sales_customization_spt.ir_cron_send_pendding_catalog_spt').interval_number = catalog_delay 
        # self.env.ref('tzc_sales_customization_spt.ir_cron_create_pendding_orders_spt').interval_number = order_delay 
        return super(res_config_settings, self).set_values()
