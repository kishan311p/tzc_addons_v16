from odoo import _, api, fields, models
import datetime
class sale_order(models.Model):
    _inherit = 'sale.order'
    
    def compute_all(self):
        for record in self:
            record.order_line._compute_amount()
            record._amount_all()
        return True
    
    def action_confirm(self):
        res = super(sale_order, self).action_confirm()
        for so in self:
            currency_rate = self.env['kits.b2b.multi.currency.mapping'].search([('currency_id','=',so.b2b_currency_id.id)],limit =1).currency_rate
            if currency_rate:
                for sol in so.order_line:
                    sol.b2b_currency_rate = currency_rate
        return res


    def kits_bambora_payment_email_of_b_to_b_website(self,dictionary):
        order_id = self.env['sale.order'].search([('name','=',dictionary.get('order'))],limit=1)
        if dictionary.get('payment_status') == 'approved':
            template_id = self.env.ref('tzc_sales_customization_spt.mail_template_for_approve_payment')
            template_id = template_id.with_context(order = order_id.name,date=datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),amount = order_id.currency_id.name + ' ' + order_id.currency_id.symbol + str(dictionary.get('amount',0.00)))
            template_id.sudo().send_mail(order_id.id,force_send=True,email_layout_xmlid="mail.mail_notification_light")
            
        if dictionary.get('payment_status') == 'declined':
            template_id = self.env.ref('tzc_sales_customization_spt.mail_template_for_decline_payment')
            template_id = template_id.with_context(order = order_id.name,date=datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),amount = order_id.currency_id.name + ' ' + order_id.currency_id.symbol + str(dictionary.get('amount',0.00)))
            template_id.sudo().send_mail(order_id.id,force_send=True,email_layout_xmlid="mail.mail_notification_light")
        return {}
    
    
    def kits_b2b_order_confrim_mail_send(self):
        
        salesman_mail_template = self.env.ref('tzc_sales_customization_spt.tzc_email_template_sales_person_sale_order_confirm')
        salesman_mail_template.send_mail(self.id,force_send=True)
        order_mail_template = self.env.ref('tzc_sales_customization_spt.tzc_email_template_sale_confirm_spt')
        order_mail_template.send_mail(self.id,force_send=True)
        return{}
    
    
    def kits_b2b_order_catalog_mail_send(self):
        self.env.ref('tzc_sales_customization_spt.kits_mail_cancel_saleorder_to_customer').send_mail(self.id, force_send=True)
        self.env.ref('tzc_sales_customization_spt.kits_mail_cancel_saleorder_to_sales_person').send_mail(self.id, force_send=True)
        return{}
    