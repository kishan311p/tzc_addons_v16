from odoo import api, fields, models, _
from odoo.exceptions import UserError


class sale_order_report_wizard_spt(models.TransientModel):
    _name = 'sale.order.report.wizard.spt'
    _description = 'Sale Order Report'

    name = fields.Selection(selection=[
            ('order', 'Full'),
            ('abbreviate', 'Abbreviate'),
            ('assorted', 'Assorted')
        ], string='Base ON', required=True,
        default='order')
    
    sale_id = fields.Many2one('sale.order')
    invoice_id = fields.Many2one('account.move')
    report_file = fields.Binary()

    def action_process(self):
        if self.name =='order' and self.sale_id:
            return self.sale_id.excel_report()
            # return self.env.ref('sale.action_report_saleorder').report_action(self.sale_id)
        
        if self.name =='abbreviate' and self.sale_id:
            return self.sale_id.excel_abbreviate_report()
            # return self.env.ref('tzc_sales_customization_spt.action_abbreviate_report_spt').report_action(self.sale_id)
        
        if self.name =='assorted' and self.sale_id:
            report_data = self.sale_id.excel_report_line()
            self.report_file = report_data
            active_id= self.id
            f_name ='Assorted-Inv-%s'%(self.sale_id.name)
            print(f_name)
            return {
                'type' : 'ir.actions.act_url',
                'url':   'web/content/?model=sale.order.report.wizard.spt&download=true&field=report_file&id=%s&filename=%s.xlsx' % (active_id, f_name),
                'target': 'self',
                }
        if self.name =='order' and self.invoice_id:
            # return self.invoice_id.excel_report()
            # return self.env.ref('account.account_invoices').report_action(self.invoice_id)
            pass
        
        if self.name =='abbreviate' and self.invoice_id:
            # return self.invoice_id.excel_abbreviate_report()
            # return self.env.ref('tzc_sales_customization_spt.action_abbreviate_invoice_report_spt').report_action(self.invoice_id)
            pass
        
        if self.name =='assorted' and self.invoice_id:
            # self.invoice_id.excel_report_line()
            # self.report_file = self.invoice_id.report_file
            # active_id= self.id
            # f_name ='Assorted Report For %s'%(self.name)
            # return {
            #     'type' : 'ir.actions.act_url',
            #     'url':   'web/content/?model=sale.order.report.wizard.spt&download=true&field=report_file&id=%s&filename=%s.xlsx' % (active_id, f_name),
            #     'target': 'self',
            #     }
            pass