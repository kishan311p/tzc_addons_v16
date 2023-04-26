from odoo import models,fields,api,_
from dateutil.relativedelta import relativedelta
from odoo.osv import expression
from odoo.tools.safe_eval import safe_eval
from datetime import datetime

class marketing_activity(models.Model):
    _inherit = 'marketing.activity'

    link_spt_id = fields.Many2one('link.tracker')
    total_mailgun_failed = fields.Integer(compute="_compute_statistics")
    total_odoo_fail = fields.Integer(compute="_compute_statistics")
    total_received = fields.Integer(compute="_compute_statistics")
    total_ignored = fields.Integer(compute="_compute_statistics")

    @api.onchange('parent_id','trigger_type')
    def _onchange_link_spt_id(self):
        tracker_obj = self.env['link.tracker']
        for rec in self:
            links = tracker_obj.browse()
            if rec.trigger_type == 'mail_click' and rec.parent_id:
                links |= tracker_obj.search([('mass_mailing_id','=',rec.parent_id.mass_mailing_id.id),('campaign_id','in',rec.campaign_id.utm_campaign_id.ids)])
            return {'domain':{'link_spt_id':[('id','in',links.ids)]}}


    def execute_on_traces(self,traces):
        parent_ids = traces.filtered(lambda x: x.child_ids.ids)
        child_ids = traces.filtered(lambda x: x.parent_id and x.activity_id.link_spt_id)
        traces = traces - parent_ids - child_ids
        if child_ids:
            parent_ids |= child_ids.filtered(lambda x: x.parent_id.clicked and x.activity_id.link_spt_id in x.parent_id.mailing_trace_ids.links_click_ids.mapped('link_id'))
        traces |= parent_ids
        res = super(marketing_activity,self.with_context(market_campaign_id=self.campaign_id.id)).execute_on_traces(traces)
        return res

    def action_kits_view_sent(self):
        self.ensure_one()
        contact_ids = self.env['campaign.report.contacts'].search([('campaign_id', '=', self.campaign_id.id)])
        return {
            "name":_("Mailing Contact"),
            "type":"ir.actions.act_window",
            'res_model':"campaign.report.contacts",
            'view_mode':'tree,form',
            "domain":[('id','in',contact_ids.ids)],
            'target':'self',
        }
    
    def action_kits_view_clicked(self):
        self.ensure_one()
        contact_ids = self.env['campaign.report.contacts'].search([('campaign_id', '=', self.campaign_id.id)]).filtered(lambda x: x.clicked)
        return {
            "name":_("Mailing Contact"),
            "type":"ir.actions.act_window",
            'res_model':"campaign.report.contacts",
            'view_mode':'tree,form',
            "domain":[('id','in',contact_ids.ids)],
            'target':'self',
        }
    
    def action_kits_view_opened(self):
        self.ensure_one()
        contact_ids = self.env['campaign.report.contacts'].search([('campaign_id', '=', self.campaign_id.id)]).filtered(lambda x: x.opened)
        return {
            "name":_("Mailing Contact"),
            "type":"ir.actions.act_window",
            'res_model':"campaign.report.contacts",
            'view_mode':'tree,form',
            "domain":[('id','in',contact_ids.ids)],
            'target':'self',
        }

    def action_kits_view_fialed_by_odoo(self):
        self.ensure_one()
        trace_ids = self.env['mailing.trace'].search([('campaign_id', '=', self.id),('trace_status','=','error')])
        contact_ids = self.env['campaign.report.contacts'].search([('trace_id', 'in', trace_ids.ids)])
        # contact_ids = self.env['campaign.report.contacts'].search([('campaign_id', '=', self.campaign_id.id)]).filtered(lambda x: x.exception)
        return {
            "name":_("Mailing Contact"),
            "type":"ir.actions.act_window",
            'res_model':"campaign.report.contacts",
            'view_mode':'tree,form',
            "domain":[('id','in',contact_ids.ids)],
            'target':'self',
        }

    def action_kits_view_fialed_by_mailgun(self):
        self.ensure_one()
        contact_ids = self.env['campaign.report.contacts'].search([('campaign_id', '=', self.campaign_id.id),('state','in',['ignored','failed_mailgun'])])
        # contact_ids = self.env['campaign.report.contacts'].search([('campaign_id', '=', self.campaign_id.id)]).filtered(lambda x: x.failed_by_mailgun)
        return {
            "name":_("Mailing Contact"),
            "type":"ir.actions.act_window",
            'res_model':"campaign.report.contacts",
            'view_mode':'tree,form',
            "domain":[('id','in',contact_ids.ids)],
            'target':'self',
        }

    def action_kits_view_received(self):
        self.ensure_one()
        contact_ids = self.env['campaign.report.contacts'].search([('campaign_id', '=', self.campaign_id.id)]).filtered(lambda x: x.received)
        return {
            "name":_("Mailing Contact"),
            "type":"ir.actions.act_window",
            'res_model':"campaign.report.contacts",
            'view_mode':'tree,form',
            "domain":[('id','in',contact_ids.ids)],
            'target':'self',
        }
    
    @api.depends('activity_type', 'trace_ids')
    def _compute_statistics(self):
        # Fix after ORM-pocalyspe : Update in any case, otherwise, None to some values (crash)
        self.update({
            'total_bounce': 0, 'total_reply': 0, 'total_sent': 0,
            'rejected': 0, 'total_click': 0, 'processed': 0, 'total_open': 0,
            'total_mailgun_failed':0, 'total_odoo_fail':0, 'total_received':0, 
            'total_ignored':0,
        })
        if self.ids:
            activity_data = {activity._origin.id: {} for activity in self}
            for stat in self._get_full_statistics():
                activity_data[stat.pop('activity_id')].update(stat)
            for activity in self:
                activity_data[activity._origin.id].update({'total_sent':len(self.env['marketing.participant'].search([('campaign_id','=',activity.campaign_id.id)])),
                                                           'processed':activity.total_received or 0,
                                                           'total_mailgun_failed':len(self.env['campaign.report.contacts'].search([('campaign_id', '=', activity.campaign_id.id),('state','in',['ignored','failed_mailgun'])])),
                                                           'rejected':len(self.env['campaign.report.contacts'].search([('campaign_id', '=', activity.campaign_id.id),('state','in',['ignored','failed_mailgun'])]))})
                activity.update(activity_data[activity._origin.id])

    def _get_full_statistics(self):
        self.env.cr.execute("""
            SELECT
                trace.activity_id,
                COUNT(stat.sent_datetime) AS total_sent,
                COUNT(stat.links_click_datetime) AS total_click,
                COUNT(stat.trace_status) FILTER (WHERE stat.trace_status = 'reply') AS total_reply,
                COUNT(stat.trace_status) FILTER (WHERE stat.trace_status in ('open', 'reply')) AS total_open,
                COUNT(stat.trace_status) FILTER (WHERE stat.trace_status = 'bounce') AS total_bounce,
                COUNT(stat.trace_status) FILTER (WHERE stat.trace_status = 'failed_mailgun') AS total_mailgun_failed,
                COUNT(stat.trace_status) FILTER (WHERE stat.trace_status = 'error') AS total_odoo_fail,
                COUNT(stat.trace_status) FILTER (WHERE stat.trace_status = 'cancel') AS total_ignored,
                COUNT(stat.trace_status) FILTER (WHERE stat.trace_status = 'received') AS total_received,
                COUNT(trace.state) FILTER (WHERE trace.state = 'processed') AS processed,
                COUNT(trace.state) FILTER (WHERE trace.state = 'rejected') AS rejected
            FROM
                marketing_trace AS trace
            LEFT JOIN
                mailing_trace AS stat
                ON (stat.marketing_trace_id = trace.id)
            JOIN
                marketing_participant AS part
                ON (trace.participant_id = part.id)
            WHERE
                (part.is_test = false or part.is_test IS NULL) AND
                trace.activity_id IN %s
            GROUP BY
                trace.activity_id;
        """, (tuple(self.ids), ))
        return self.env.cr.dictfetchall()
