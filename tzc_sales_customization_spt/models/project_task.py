from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from datetime import datetime,timedelta
from pytz import utc
import pandas
from odoo.addons.resource.models.resource import Intervals, sum_intervals, string_to_datetime
from collections import defaultdict

def timezone_datetime(time):
    if not time.tzinfo:
        time = time.replace(tzinfo=utc)
    return time

class project_task(models.Model):
    _inherit = "project.task"

    def _get_admin_user(self):
        if self.env.ref('base.group_system').users:
            return [('id','in',self.env.ref('base.group_system').users.ids)]

    task_type = fields.Selection([('bug','Bug'), ('improvement','Improvement'), ('new_development','New Development')],default="improvement", string="Type")
    task_priority = fields.Selection([('-1','-1'),('1','1'),('2','2'),('3','3')], string="Priroity",default="1", tracking=True)
    estimated_days = fields.Float("Estimated Days", tracking=True)
    task_follow_up = fields.Selection([('done','Done'), ('reject','Rejected'), ('attention','Needs Attention')])    
    is_bug = fields.Boolean("Creeping Bug")
    planned_date_begin = fields.Date("Start date", tracking=True)
    planned_date_end = fields.Date("End date", tracking=True)
    follow_up_by = fields.Many2one("res.users", "Follow Up By", domain=lambda self: [('groups_id','in',[self.env.ref('project.group_project_user').id, self.env.ref('project.group_project_manager').id])])
    task_progress = fields.Integer("Progress")
    check_date = fields.Boolean("Current Date", compute="_check_date")
    current_date = fields.Date('Current Date & Time',compute="_compute_current_date")
    user_id = fields.Many2one('res.users',string='Assigned to',default=lambda self: self.env.uid,index=True, tracking=True,domain=_get_admin_user)
    task_status = fields.Selection(string='Status',related='stage_id.progress_status')

    @api.constrains('sequence')
    def onchange_time_duration(self):
        for rec in self:
            sequence_list = self.search([('stage_id.name','ilike','pending'),('project_id','=',rec.project_id.id)]).mapped('sequence')
            if rec.stage_id.name.lower() == 'pending' and rec.sequence != 0 and rec.estimated_days != 0.0:
                last_task_id = self.search([('sequence','=',rec.sequence-1),('stage_id.name','ilike','pending'),('project_id','=',rec.project_id.id)],limit=1)
                if last_task_id.planned_date_end:
                    task_start_date = last_task_id.planned_date_end + relativedelta(days=1)
                    rec.planned_date_begin = task_start_date
                    rec._set_date_end_deadline()
                else:
                    below_task_seq = sequence_list[:rec.sequence]
                    for seq in below_task_seq[::-1]:
                        task_id = self.search([('sequence','=',seq),('stage_id.name','ilike','pending'),('project_id','=',rec.project_id.id)],limit=1)
                        if task_id.planned_date_end:
                            task_start_date = task_id.planned_date_end + relativedelta(days=1)
                            rec.planned_date_begin = task_start_date
                            rec._set_date_end_deadline()
                            break

    def _compute_current_date(self):
        for rec in self:
            rec.current_date = datetime.now()
            if rec.active:
                if not rec.planned_date_begin or not rec.planned_date_end:
                    rec.color = 2
                elif rec.planned_date_begin and rec.planned_date_begin > rec.current_date and rec.active:
                    rec.color = 10
                elif rec.planned_date_begin and rec.planned_date_begin < rec.current_date and rec.stage_id.progress_status in ('pending','in_progress'):
                # elif rec.planned_date_begin and rec.planned_date_begin < rec.current_date and rec.stage_id.name.lower() in ('pending','inprogress','revision'):
                    if rec.active:
                        rec.color = 1
                    else:
                        rec.color = 10
                else:
                    rec.color = 10
            elif rec.active == False:
                rec.color = 4

    @api.onchange('estimated_days', 'planned_date_begin')
    def _set_date_end_deadline(self):
        for record in self:
            if record.estimated_days and record.planned_date_begin:
                # Input start date in YYYY-MM-DD format
                start_date = str(timezone_datetime(datetime.combine(record.planned_date_begin,datetime.max.time())).date())

                # Input number of days to include
                num_days = record.estimated_days

                # Convert start date string to datetime object
                start = datetime.strptime(start_date, "%Y-%m-%d")

                # Define a function to check if a date is a weekend day
                def is_weekend(date):
                    return date.weekday() >= 5  # Saturday has weekday() value of 5, Sunday has value of 6

                # Loop through each date in the range
                date_list = []
                delta = timedelta(days=1)
                while len(date_list) < num_days:
                    if not is_weekend(start):
                        date_list.append(start.strftime("%Y-%m-%d"))  # Add date to the list in YYYY-MM-DD format
                    start += delta

                record.planned_date_end = datetime.strptime(max(date_list), '%Y-%m-%d')

    @api.onchange('estimated_days')
    def _onchange_estimated_days(self):
        for record in self:
            if record.estimated_days == 0:
                record.planned_date_begin = False
                record.planned_date_end = False

    def calculate_days_list(self,from_datetime,to_datetime,user_id,leave_date_list):
        date_list = []
        date_obj = user_id.resource_calendar_id._get_resources_day_total(from_datetime, to_datetime,user_id.resource_ids)
        date_list.extend(list(date_obj[user_id.resource_calendar_id.id].keys()))
        rng = tuple(date_list)
        for working_date in rng:
            if working_date in leave_date_list:
                date_list.pop(date_list.index(working_date))
        date_list.sort()
        return len(date_list),date_list[-1] if date_list and date_list[-1] else None

    _sql_constraints = [(
        'name_uniq', 'UNIQUE(name)', 'The name of the Task must be Unique! A Task with this name already exists!'
    )]

    def write(self, vals):
        if vals and vals.get('active') == False:
            vals.update({'color':4})
        if vals and vals.get('stage_id'):
            stage_id = self.env['project.task.type'].browse(vals.get('stage_id'))
            if self.task_status in ['in_progress','done'] and stage_id.progress_status in ['pending']:
                raise UserError('You can\'t change task status to Pending.')

        res = super(project_task, self).write(vals)
        if self._context.get('params',{}).get('view_type','') == 'gantt':
            if ('estimated_days' not in vals.keys()) and ('planned_date_begin' in vals.keys() or 'planned_date_end' in vals.keys()):
                self.update_estimated_days()    
        return res
    
    @api.model_create_multi
    def create(self,vals):
        res = super(project_task,self).create(vals)
        if res and res.project_id:
            max_list = self.env['project.task'].search([('project_id','=',res.project_id.id),('stage_id','ilike','pending')]).mapped('sequence')
            if max_list :
                max_seq = max(max_list)
                if max_seq:
                    res.sequence = max_seq + 1
        return res


    def update_estimated_days(self):
        for record in self:
            record.estimated_days = (record.planned_date_end - record.planned_date_begin).days

    def _check_date(self):
        for record in self:
            record.check_date = False
            if record.planned_date_end and (record.planned_date_end > fields.date.today()):
                record.check_date = True

    def action_shift_timeline(self):
        return {
            "name":_("Shift Timeline"),
            "type":"ir.actions.act_window",
            "res_model":"time.shift.wizard",
            "view_mode":"form",
            "context":{"default_task_ids":[(6,0,self.ids)],},
            "target":"new",
        }

    def unlink(self):
        try:
            res = super(project_task,self).unlink()
            return res
        except Exception as e:
            raise UserError('This task cannot be deleted since there might be some data attached to it. You may delete those data and try again.\n\n'+e.pgerror)

    @api.depends('planned_date_begin', 'planned_date_end', 'company_id.resource_calendar_id', 'user_ids')
    def _compute_allocated_hours(self):
        task_working_hours = self.filtered(lambda s: s.allocation_type == 'working_hours' and (s.user_ids or s.company_id))
        task_duration = self - task_working_hours
        for task in task_duration:
            # for each planning slot, compute the duration
            task.allocated_hours = task.duration * (len(task.user_ids) or 1)
        # This part of the code comes in major parts from planning, with adaptations.
        # Compute the conjunction of the task user's work intervals and the task.
        if not task_working_hours:
            return
        # if there are at least one task having start or end date, call the _get_valid_work_intervals
        start_utc = utc.localize(datetime.combine(min(task_working_hours.mapped('planned_date_begin')),datetime.min.time()))
        end_utc = utc.localize(datetime.combine(max(task_working_hours.mapped('planned_date_end')),datetime.max.time()))
        # work intervals per user/per calendar are retrieved with a batch
        user_work_intervals, calendar_work_intervals = task_working_hours.user_ids._get_valid_work_intervals(
            start_utc, end_utc, calendars=task_working_hours.company_id.resource_calendar_id
        )
        for task in task_working_hours:
            start = max(start_utc, utc.localize(datetime.combine(task.planned_date_begin,datetime.min.time())))
            end = min(end_utc, utc.localize(datetime.combine(task.planned_date_end,datetime.max.time())))
            interval = Intervals([(
                start, end, self.env['resource.calendar.attendance']
            )])
            sum_allocated_hours = 0.0
            if task.user_ids:
                # we sum up the allocated hours for each user
                for user in task.user_ids:
                    sum_allocated_hours += sum_intervals(user_work_intervals[user.id] & interval)
            else:
                sum_allocated_hours += sum_intervals(calendar_work_intervals[task.company_id.resource_calendar_id.id] & interval)
            task.allocated_hours = sum_allocated_hours

    def _gantt_progress_bar_user_ids(self, res_ids, start, stop):
        start_naive, stop_naive = start.replace(tzinfo=None), stop.replace(tzinfo=None)
        users = self.env['res.users'].search([('id', 'in', res_ids)])
        self.env['project.task'].check_access_rights('read')

        project_tasks = self.env['project.task'].sudo().search([
            ('user_ids', 'in', res_ids),
            ('planned_date_begin', '<=', stop_naive),
            ('planned_date_end', '>=', start_naive),
        ])

        planned_hours_mapped = defaultdict(float)
        user_work_intervals, _dummy = users.sudo()._get_valid_work_intervals(start, stop)
        for task in project_tasks:
            # if the task goes over the gantt period, compute the duration only within
            # the gantt period
            max_start = max(start, utc.localize(datetime.combine(task.planned_date_begin,datetime.min.time())))
            min_end = min(stop, utc.localize(datetime.combine(task.planned_date_end,datetime.max.time())))
            # for forecast tasks, use the conjunction between work intervals and task.
            interval = Intervals([(
                max_start, min_end, self.env['resource.calendar.attendance']
            )])
            nb_hours_per_user = (sum_intervals(interval) / (len(task.user_ids) or 1)) if task.allocation_type == 'duration' else 0.0
            for user in task.user_ids:
                if task.allocation_type == 'duration':
                    planned_hours_mapped[user.id] += nb_hours_per_user
                else:
                    work_intervals = interval & user_work_intervals[user.id]
                    planned_hours_mapped[user.id] += sum_intervals(work_intervals)
        # Compute employee work hours based on its work intervals.
        work_hours = {
            user_id: sum_intervals(work_intervals)
            for user_id, work_intervals in user_work_intervals.items()
        }
        return {
            user.id: {
                'value': planned_hours_mapped[user.id],
                'max_value': work_hours.get(user.id, 0.0),
            }
            for user in users
        }
