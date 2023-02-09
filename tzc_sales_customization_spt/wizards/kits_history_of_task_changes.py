import openpyxl
from odoo import api, fields, models, _
from io import BytesIO
import pandas as pd
import base64
from openpyxl import Workbook
import xlsxwriter

class kits_history_of_task_changes(models.TransientModel):
    _name = "kits.history.of.task.changes"
    _description = "Kits History Of Task Changes"

    date_to = fields.Date("Date To")
    date_from = fields.Date("Date From")
    task_ids = fields.Many2many("project.task", "task_history_project_task_rel", "task_history_id", "project_task_id", "Tasks")
    file = fields.Binary("File")

    def action_excel_report(self):
        for record in self:
            task_name_list = []
            task_list = []
            task_ids = record.task_ids if record.task_ids else self.env['project.task'].search([])
            for task_id in task_ids:
                domain = []
                task_changed_values = [] 
                task_name_list.append(task_id.display_name)
                domain.extend([('model','=','project.task'), ('res_id','=',task_id.id)])
                if record.date_from:
                    domain.append(('date','>=',record.date_from))
                if record.date_to:
                    domain.append(('date','<=',record.date_to))
                mail_message_ids = self.env['mail.message'].search(domain)
                for mail_message in mail_message_ids:
                    for value in mail_message.tracking_value_ids: 
                        if value.field_type == 'date' or value.field_type == 'datetime':
                            task_changed_values.append([str(mail_message.date), mail_message.author_id.display_name, task_id.name, value.field_desc, str(value.old_value_datetime), str(value.new_value_datetime)])
                        elif value.field_type == 'float':
                            task_changed_values.append([str(mail_message.date), mail_message.author_id.display_name, task_id.name, value.field_desc, value.old_value_float, value.new_value_float])
                        elif value.field_type == 'int':
                            task_changed_values.append([str(mail_message.date), mail_message.author_id.display_name, task_id.name, value.field_desc, value.old_value_integer, value.new_value_integer])
                        elif value.field_type == 'char':
                            task_changed_values.append([str(mail_message.date), mail_message.author_id.display_name, task_id.name, value.field_desc, value.old_value_char, value.new_value_char])
                        elif value.field_type == 'text':
                            task_changed_values.append([str(mail_message.date), mail_message.author_id.display_name, task_id.name, value.field_desc, value.old_value_text, value.new_value_text])
                task_list.extend(task_changed_values)
            fp = BytesIO()
            wb = xlsxwriter.Workbook(fp)
            for task in task_name_list:
                old_task = []
                if task not in old_task:  
                    old_task.append(task)
                    sheet = wb.add_worksheet(task)
                heading_line = ['DateTime', 'Author', 'Task Name', 'Field', 'Old Value', 'New Value']
                col = row = 0
                for heading_data in heading_line:
                    sheet.write(row,col,heading_data)
                    sheet.set_column(row,col, len(heading_data)*3)
                    col+=1
                for worksheet_line in task_list:
                    col = 0
                    row +=1
                    for worksheet_line_data in worksheet_line:
                        if worksheet_line[2] not in old_task:
                            row = 0
                            break
                        sheet.write(row,col,worksheet_line_data)
                        col +=1
            wb.close()
            fp.seek(0)
            data = fp.read()
            fp.close()
            self.file = base64.b64encode(data)
            return{
                'type':'ir.actions.act_url',
                'url':'web/content/?model=kits.history.of.task.changes&download=True&field=file&id=%s&filename=%s.xlsx' % (self.id, "Task Reports"),
                'target':'new',
            }        
                    
