from odoo import _, api, fields, models, tools
from datetime import datetime


class mail_tracking_value(models.Model):
    _inherit = "mail.tracking.value"

    @api.model
    def create_tracking_values(self, initial_value, new_value, col_name, col_info, tracking_sequence,model_name):
        tracked = True
        field = self.env['ir.model.fields']._get(model_name, col_name)
        values = {'field': field.id, 'field_desc': col_info['string'], 'field_type': col_info['type'], 'tracking_sequence': tracking_sequence}

        if col_info['type'] in ['integer', 'float', 'char', 'text', 'datetime', 'monetary']:
            values.update({
                'old_value_%s' % col_info['type']: initial_value,
                'new_value_%s' % col_info['type']: new_value
            })
        elif col_info['type'] == 'date':
            values.update({
                'old_value_datetime': initial_value and fields.Datetime.to_string(datetime.combine(fields.Date.from_string(initial_value), datetime.min.time())) or False,
                'new_value_datetime': new_value and fields.Datetime.to_string(datetime.combine(fields.Date.from_string(new_value), datetime.min.time())) or False,
            })
        elif col_info['type'] == 'boolean':
            values.update({
                'old_value_integer': initial_value,
                'new_value_integer': new_value
            })
        elif col_info['type'] == 'selection':
            values.update({
                'old_value_char': initial_value and dict(col_info['selection'])[initial_value] or '',
                'new_value_char': new_value and dict(col_info['selection'])[new_value] or ''
            })
        elif col_info['type'] == 'many2one':
            values.update({
                'old_value_integer': initial_value and initial_value.id or 0,
                'new_value_integer': new_value and new_value.id or 0,
                'old_value_char': initial_value and initial_value.sudo().name_get()[0][1] or '',
                'new_value_char': new_value and new_value.sudo().name_get()[0][1] or ''
            })
        elif col_info['type'] == 'many2many' and (col_name == 'contact_allowed_countries' or col_name == 'country_ids'):
            values.update({
                'old_value_char': ', '.join(initial_value.mapped('name')) or '',
                'new_value_char': ', '.join(new_value.mapped('name')) or ''
            })
        else:
            tracked = False

        if tracked:
            return values
        return {}
