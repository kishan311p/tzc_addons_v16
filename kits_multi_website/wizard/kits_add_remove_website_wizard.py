from odoo import api, fields, models, _

class kits_add_remove_website_wizard(models.TransientModel):
    _name = "kits.add.remove.website.wizard"
    _description = "Kits Add Remove Website Wizard"

    website_id = fields.Many2one('kits.b2c.website', string='website')
    
    res_id = fields.Char('IDs')
    res_model = fields.Char('Model')
    is_add = fields.Boolean('Add Website')

    def kits_action_add_remove_website(self):
        for record in self:
            record_ids = self.env[record.res_model].browse(eval(record.res_id))
            if record.is_add:
                record_ids.write({'website_id': record.website_id.id})
            else:
                record_ids.write({'website_id':False})