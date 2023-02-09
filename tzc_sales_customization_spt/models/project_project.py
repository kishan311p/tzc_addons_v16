from odoo import api, fields, models, _
from odoo.exceptions import UserError

class project_project(models.Model):
    _inherit = "project.project"

    def unlink(self):
        try:
            res = super(project_project,self).unlink()
            return res
        except Exception as e:
            raise UserError('This project cannot be deleted since there might be some data attached to it. You may delete those data and try again.\n\n'+e.pgerror)
            # raise UserError(e)
