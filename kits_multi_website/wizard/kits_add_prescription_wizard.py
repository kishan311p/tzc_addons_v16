from odoo import api, fields, models, _

class kits_add_prescription_wizard(models.TransientModel):
    _name = "kits.add.prescription.wizard"
    _description = "Kits Prescription Wizard"

    select_prescription = fields.Selection([('new','Add New'),('old','Select From Account')],'Select Prescription',default='old')
    prescription = fields.Binary('Prescription')
    file_name = fields.Char('File Name')
    customer_id = fields.Many2one("kits.multi.website.customer", "Customer") 
    prescription_id = fields.Many2one("kits.multi.website.prescription", "Prescription",domain="[('customer_id','=',customer_id)]") 
    name = fields.Char('Name')
    
    def action_add_prescription(self):
        self.ensure_one()
        if self.select_prescription == 'new':
            prescription_id = self.env['kits.multi.website.prescription'].create({
                'file_name':self.file_name,
                'prescription_file_data': self.prescription,
                'name' : self.name,
                'customer_id' : self.customer_id.id
            })
        else: 
            prescription_id = self.prescription_id

        if self._context.get('active_id') and self._context.get('active_model'):
            line_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
            line_id.prescription_id = prescription_id.id
            line_id.state = 'prescription_added'
            line_id.show_add_glass_button = True
            state_list = line_id.sale_order_id.sale_order_line_ids.mapped('state')
            if 'prescription_added' in state_list:
                line_id.sale_order_id.state = 'prescription_added'
            if 'waiting_for_prescription' in state_list:
                line_id.sale_order_id.state = 'waiting_for_prescription'


