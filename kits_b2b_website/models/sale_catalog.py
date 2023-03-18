from odoo import _, api, fields, models

class sale_catalog(models.Model):
    _inherit = 'sale.catalog'
    
    def catalog_reject_mail(self,partner_id,message) :
        self.env.ref('tzc_sales_customization_spt.kits_mail_reject_catalog_to_sales_person').with_context(message=message,customer=partner_id).send_mail(self.id, force_send=True,email_layout_xmlid="mail.mail_notification_light")
        return {}

    def catalog_email(self,partner_id):
        for record in self:
            so_id  = self.env['sale.order'].search([('partner_id','=',partner_id),('catalog_id','=',record.id)])
            verified = so_id.partner_verification()
            quotation_template_id = self.env.ref('tzc_sales_customization_spt.tzc_email_template_catalog_quotation_spt') if verified else None
            url = ''
            pdf_links = self.env['ir.model'].sudo().generate_report_access_link(
                'sale.catalog',
                record.id,
                'sale.action_report_saleorder',
                partner_id,
                'pdf'
            )
            if pdf_links.get('success') and pdf_links.get('url'):
                url = pdf_links.get('url')
            quotation_template_id.with_context(pdf_url=url).send_mail(so_id.id,force_send=True,email_layout_xmlid="mail.mail_notification_light") if verified else None
            confirmation_template_id = self.env.ref('tzc_sales_customization_spt.tzc_email_template_saleperson_quotation_spt')
            confirmation_template_id.send_mail(so_id.id,email_values={'email_to': so_id.user_id.partner_id.email},force_send=True,email_layout_xmlid="mail.mail_notification_light")
        return {}
