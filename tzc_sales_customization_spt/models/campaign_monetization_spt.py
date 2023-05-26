from odoo import models, fields, api, _

class campaign_monetization_spt(models.Model):
    _name = 'campaign.monetization.spt'
    _description = 'Campaign Monetization'

    name = fields.Char('Name')
    email = fields.Char('Email')
    internal_id = fields.Char('Internal ID')
    odoo_contact_id = fields.Many2one('res.partner','Odoo Contact ID')
    before_source = fields.Selection([('imported','Imported'),('odoo_contact','Odoo Contact'),('newsletter','Newsletter'),('mixed','Mixed')],'Source  Before')
    after_source = fields.Selection([('imported','Imported'),('odoo_contact','Odoo Contact'),('newsletter','Newsletter'),('mixed','Mixed')],'Source After')
    before_prospect_level = fields.Selection([('zero','0'),('one','1')],'Prospect Level  Before')
    after_prospect_level = fields.Selection([('zero','0'),('one','1')],'Prospect Level After')
    before_status_type = fields.Selection([('b2c','Pending'),('b2b_regular','Verified')],'Status Type Before')
    after_status_type = fields.Selection([('b2c','Pending'),('b2b_regular','Verified')],'Status Type After')
    before_action_type = fields.Selection([('confirmed','Confirmed'),('not_connected','Not Connected')],'Action Type Before')
    after_action_type = fields.Selection([('confirmed','Confirmed'),('not_connected','Not Connected')],'Action Type After')
    before_orders = fields.Integer('# Orders Before')
    after_orders = fields.Integer('# Orders After')
    # before_promo_code_ids = fields.Many2many('sale.coupon.program','before_sale_coupon_program_monetization_real','monetization_id','sale_coupon_id','Promotion Coupons Before')
    # after_promo_code_ids = fields.Many2many('sale.coupon.program','after_sale_coupon_program_monetization_real','monetization_id','sale_coupon_id','Promotion Coupons After')
    campaign_id = fields.Many2one('marketing.campaign','Marketing Campaign')
    participant_id = fields.Many2one('marketing.participant','Participant',ondelete="cascade")
    salesperson_id = fields.Many2one('res.users','Salesperson')
    marketing_activity_ids = fields.Text('Marketing Activities')
    compute_salesperson = fields.Boolean(compute="_compute_salesperson_id")

    def _compute_salesperson_id(self):
        user_obj = self.env['res.users']
        for rec in self:
            salesperson = rec.odoo_contact_id.user_id
            if not salesperson and rec.email:
                salesperson =  self.env['res.partner'].search([('email','=',rec.email)],limit=1).user_id
            if not salesperson and rec.participant_id and rec.participant_id.resource_ref and rec.participant_id.model_name == 'mailing.contact':
                salesperson = rec.participant_id.resource_ref.salesperson_id
            rec.salesperson_id = salesperson.id
            rec.compute_salesperson = False
            traces = self.env['mailing.trace'].search([('email','=',rec.email)]) if rec.email else None
            activity_ids = traces.mapped("marketing_trace_id").mapped("activity_id").mapped('name') if traces else rec.marketing_activity_ids.split(',') if rec.marketing_activity_ids else ''
            rec.marketing_activity_ids = ','.join([str(activity) for activity in activity_ids if activity])
