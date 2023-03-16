from odoo import _, api, fields, models

class sale_catalog(models.Model):
    _inherit = 'sale.catalog'
    

    def catalog_email(self,partner_id):
        for record in self:
            so_id  = self.env['sale.order'].search([('partner_id','=',partner_id),('catalog_id','=',record.id)])
            verified = so_id.partner_verification()
            quotation_template_id = self.env.ref('tzc_sales_customization_spt.tzc_email_template_catalog_quotation_spt') if verified else None
            quotation_template_id.send_mail(so_id.id,force_send=True) if verified else None
            confirmation_template_id = self.env.ref('tzc_sales_customization_spt.tzc_email_template_saleperson_quotation_spt')
            confirmation_template_id.send_mail(so_id.id,email_values={'email_to': so_id.user_id.partner_id.email},force_send=True)
        return {}