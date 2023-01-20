from odoo import api, fields, models, _

class kits_multi_website_change_password(models.TransientModel):
    _name = "kits.multi.website.change.password"
    _description = "Kits Multi Website Change Password"

    email = fields.Char("Email")
    new_password = fields.Char("New Password")
    customer_id = fields.Many2one("kits.multi.website.customer", "Customer")

    def action_change_password(self):
        for record in self:
            encrypted_password = record.customer_id._get_encrypted_password(record.new_password)
            record.customer_id.password = encrypted_password 

