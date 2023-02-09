from odoo import _, api, fields, models, tools
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError
from datetime import datetime
from pytz import utc

def timezone_datetime(time):
    if not time.tzinfo:
        time = time.replace(tzinfo=utc)
    return time

class time_shift_wizard(models.TransientModel):
    _name = 'time.shift.wizard'
    _description = "Time Shift Wizard"

    estimate_date = fields.Float('Days')
    task_ids = fields.Many2many('project.task',string='Project')


    def action_process(self):
        if self.task_ids and self.estimate_date:
            for task in self.task_ids:
                if task.planned_date_begin and task.estimated_days:
                    total_estimated_days = self.estimate_date
                    planned_date_end = task.planned_date_begin
                    from_datetime = timezone_datetime(datetime.combine(task.planned_date_begin,datetime.max.time()))
                    leave_date_list = []
                    to_datetime = timezone_datetime(datetime.combine(planned_date_end,datetime.max.time()))
                    data_date_list =  [(date.date_from.date(),date.date_to.date()) for date in task.user_id.resource_calendar_id.global_leave_ids if date.date_from.date() >= from_datetime.date() or date.date_to.date() <= to_datetime.date()] 
                    
                    for date_tuple in data_date_list:
                        leave_date_list.append(date_tuple[0])
                        leave_date_list.append(date_tuple[1])
                        for count  in range(0,(date_tuple[1]-date_tuple[0]).days):

                            date = date_tuple[0]+  relativedelta(days= count+1)
                            leave_date_list.append(date)
                    total_day_count = 0
                    while total_day_count < total_estimated_days:
                        if total_day_count:
                            to_datetime = to_datetime + relativedelta(days = self.estimate_date-total_day_count)
                        total_day_count,date = task.calculate_days_list(from_datetime,to_datetime,task.user_id,leave_date_list)
                    
                    task.planned_date_begin = timezone_datetime(datetime.combine(date,datetime.max.time()))
                    task._set_date_end_deadline()
