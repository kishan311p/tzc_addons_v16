from odoo import api, fields, models, _
from io import BytesIO
import pandas as pd
import base64
from openpyxl import Workbook
from odoo.exceptions import UserError
import xlsxwriter

class kits_task_report_of_users(models.TransientModel):
    _name = "kits.task.report.of.users"
    _description = "Kits Task Report Of Users"

    date_from = fields.Date("From")
    date_to = fields.Date("To")
    follow_up_user_ids = fields.Many2many("res.users", "task_report_res_users_rel", "task_report_id", "user_id", "Follow Up By", domain=lambda self: [('groups_id','in',[self.env.ref('project.group_project_user').id, self.env.ref('project.group_project_manager').id])])
    assigned_to_user_ids = fields.Many2many("res.users", "assigned_to_res_users_rel", "assigned_to_id", "user_id", "Assigned To", domain=lambda self: [('groups_id','in',[self.env.ref('project.group_project_user').id, self.env.ref('project.group_project_manager').id])])
    task_follow_up = fields.Selection([('done','Done'), ('reject','Rejected'), ('attention','Needs Attention')])    
    task_type = fields.Selection([('bug','Bug'), ('improvement','Improvement'), ('new_development','New Development')], string="Type")
    is_bug = fields.Selection([('true','True'), ('false', 'False')], string="Creeping Bug")
    task_priority = fields.Selection([('0','0'), ('5','5'), ('4','4'), ('3','3'), ('2','2'), ('1','1')], string="Priroity")
    project_task_type_ids = fields.Many2many("project.task.type", "project_task_users_task_report_rel", "project_task_id", "users_task_report_id", "Stage")
    file = fields.Binary("File")

    def action_excel_report(self):
        for record in self:
            user_list = []
            task_list = []
            user_ids = record.follow_up_user_ids if record.follow_up_user_ids else self.env['res.users'].search([('groups_id','in',[self.env.ref('project.group_project_user').id, self.env.ref('project.group_project_manager').id])]) 
            for user_id in user_ids:
                domain = []
                domain.extend([('follow_up_by','=',user_id.id)])
                if record.date_from:
                    domain.append(('planned_date_begin', '>=', record.date_from))
                if record.date_to:
                    domain.append(('planned_date_end','<=',record.date_to))
                if record.task_follow_up:
                    domain.append(('task_follow_up','=', record.task_follow_up))
                if record.task_type:
                    domain.append(('task_type','=',record.task_type))  
                if record.is_bug:
                    domain.append(('is_bug','=',True) if record.is_bug == 'true' else ('is_bug','=',False))
                if record.task_priority:
                    domain.append(('task_priority','=',record.task_priority))
                if record.project_task_type_ids:
                    domain.append(('stage_id','in',record.project_task_type_ids.ids))
                
                task_ids = self.env['project.task'].search(domain)
                for task_id in task_ids:                                                                                
                    if task_id.follow_up_by.display_name not in user_list: 
                        user_list.append(task_id.follow_up_by.display_name)                 
                    task_list.append([task_id.name, str(task_id.planned_date_begin),str(task_id.planned_date_end), task_id.estimated_days, 
                    dict(self.env['project.task']._fields['task_follow_up'].selection).get(task_id.task_follow_up), task_id.follow_up_by.display_name, 
                    task_id.project_id.display_name, task_id.task_progress, task_id.is_bug, 
                    dict(self.env['project.task']._fields['task_type'].selection).get(task_id.task_type), 
                    dict(self.env['project.task']._fields['task_priority'].selection).get(task_id.task_priority)])
            fp = BytesIO()
            workbook = xlsxwriter.Workbook(fp)
            worksheet = False
            for user_name in user_list:
                old_user = []
                if user_name not in old_user:  
                    old_user.append(user_name) 
                worksheet = workbook.add_worksheet(user_name)
                if worksheet:
                    heading_line = ['Task Name', 'Start Date', 'End Date', 'Estimated Days', 'Task Follow Up By', 'Assigned To', 'Project', 'Progress',
                    'Creeping Bug', 'Type', 'Priority']
                    col = row =0
                    for heading_data in heading_line:
                        worksheet.write(row,col,heading_data)
                        worksheet.set_column(row,col, len(heading_data)*2)
                        col+=1
                    for worksheet_line in task_list:
                        row +=1
                        col = 0
                        for worksheet_line_data in worksheet_line:
                            if worksheet_line[5] not in old_user:
                                row = 0
                                break
                            worksheet.write(row,col,worksheet_line_data)
                            col +=1

            workbook.close()
            fp.seek(0)
            data = fp.read()
            fp.close()
            self.file = base64.b64encode(data)
            return{
                'type':'ir.actions.act_url',
                'url':'web/content/?model=kits.task.report.of.users&download=True&field=file&id=%s&filename="Tasks Report".xlsx' % (self.id),
                'target':'new',
            }
