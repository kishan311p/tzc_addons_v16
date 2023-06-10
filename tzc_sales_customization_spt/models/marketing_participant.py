from odoo import _,api,fields,models

class marketing_participant(models.Model):
    _inherit = 'marketing.participant'

    # Use for rule.
    salesperson_id = fields.Many2one('res.users','Salesperson')
    partner_id = fields.Many2one('res.partner','Partner')
        

    @api.onchange('resource_ref')
    def update_salesperson_id_spt(self):
        for rec in self:
            partner_model = self.env.ref('base.model_res_partner')
            if rec.model_id.id == partner_model.id:
                rec.salesperson_id = self.resource_ref.user_id
                rec.partner_id = self.resource_ref

    @api.model_create_multi
    def create(self,vals):
        res = super(marketing_participant,self).create(vals)
        for rec in res:
            partner_model = self.env.ref('base.model_res_partner')
            if rec.model_id.id == partner_model.id:
                partner_id = self.env['res.partner'].browse(rec.res_id)
                rec.salesperson_id = partner_id.user_id
                rec.partner_id = partner_id
        return res


    # @api.onchange('res_id')