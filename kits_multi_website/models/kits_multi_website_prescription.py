from odoo import api, fields, models, _
from odoo.exceptions import UserError

class kits_multi_website_prescription(models.Model):
    _name = "kits.multi.website.prescription"
    _description = "Prescription"

    name = fields.Char('Name')
    customer_id = fields.Many2one('kits.multi.website.customer', string='Used For The Customer')
    prescription_file_data = fields.Text('Prescription File')
    file_name = fields.Char('File Name')
    prescription_line_ids = fields.One2many('kits.multi.website.prescription.line','prescription_id','Eye Information')
    state = fields.Selection([('unverified', 'Unverified'),('verified', 'Verified')], string='state',default="unverified")

    def action_download_prescription(self):
        self.ensure_one()
        if self.prescription_file_data:
            f_name = (self.file_name or '').replace(' ','_') 
            wizard = self.env['kits.file.download.wizard'].create({
                'file': self.prescription_file_data
            })
            active_id = wizard.id
            return {
                    'type': 'ir.actions.act_url',
                    'url': 'web/content/?model=kits.file.download.wizard&download=true&field=file&id=%s&filename=%s' % (active_id, f_name),
                    'target': 'self',
            }
        else:
            raise UserError(_('File Data not Found'))
    
    @api.model_create_multi
    def create(self, vals):
        res =  super(kits_multi_website_prescription,self).create(vals)
        for record in res:
            if not record.prescription_line_ids:
                record.prescription_line_ids = [
                    (0,0,{'eye_name_id':self.env.ref('kits_multi_website.SPHERICAL').id}),
                    (0,0,{'eye_name_id':self.env.ref('kits_multi_website.CYLINDRICAL').id}),
                    (0,0,{'eye_name_id':self.env.ref('kits_multi_website.AXIS').id}),
                    (0,0,{'eye_name_id':self.env.ref('kits_multi_website.AP').id})]
        return res