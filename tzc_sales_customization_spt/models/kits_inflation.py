from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class kits_inflation(models.Model):
    _name = 'kits.inflation'

    name = fields.Char('Name')
    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')
    is_active = fields.Boolean("Is Active",default=False,copy=False)
    inflation_rule_ids = fields.One2many('kits.inflation.rule','inflation_id','Inflation')

    @api.constrains('is_active')
    def active_rec_validation(self):
        if self.is_active:
            active_rec = self.search([('is_active','=',True)])
            if len(active_rec) > 1:
                raise UserError(f'You can not have 2 inflation campaigns at the same time please First Deactivate {active_rec.name}')

    def action_active(self):
        for rec in self:
            rec.is_active = False

    def action_deactive(self):
        active_rec = self.search([('is_active','=',True)])
        for rec in self:
            if not active_rec:
                rec.is_active = True
            else:
                raise UserError(f'You can not have 2 inflation campaigns at the same time please First Deactivate {active_rec.name}')
