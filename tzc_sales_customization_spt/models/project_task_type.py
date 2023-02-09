from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class project_task_type(models.Model):
    _inherit = 'project.task.type'

    progress_status = fields.Selection([('pending','Pending'),('in_progress','In Progress'),('done','Done')],'Progress Status')

    def unlink(self):
        try:
            res = super(project_task_type,self).unlink()
            return res
        except Exception as e:
            # raise UserError(e)
            raise UserError('This stage cannot be deleted since there might be some data attached to it. You may delete those data and try again.\n\n'+e.pgerror)
