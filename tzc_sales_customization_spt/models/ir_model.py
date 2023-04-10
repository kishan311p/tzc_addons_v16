import secrets
from odoo import _, api, fields, models, tools


class ir_model(models.Model):
    _inherit = "ir.model"

    def _updated_data_validation(self, fields, data, model):
        updated_fields = []
        update = False
        for value in data.keys():
            if value in fields:
                if model == 'sale.order' and not self._context.get('cron') and not self._context.get('on_consign_wizard') or self._context.get('active_model') == 'sale.barcode.order.spt':
                    updated_fields.append(value)
                if model == 'stock.picking' and not self._context.get('custom'):
                    updated_fields.append(value)
                if model == 'account.move' or model == 'res.partner':
                    updated_fields.append(value)
            elif self._context.get('params') and self._context.get('params').get('model') == 'sale.order' and self._context.get('active_model') == 'sale.barcode.order.spt':
                updated_fields.append(value)

        if updated_fields:
            update = True

        return update

    def generate_report_access_link(self, model_name, rec_id, report_name, partner_id, report_type='pdf'):
        """
        Method check access rights of records for partner_id
        model_name : Model name
        rec_id: Record id
        report_name: External id of report
        partner_id: Customer id
        """
        result = {
            'success': False,
            'error': '',
            'url': ''
        }
        try:
            assert isinstance(rec_id, int), 'Record id must be integer.'
            if report_type == 'pdf':
                assert self.env.ref(report_name),\
                    "Specified report is not available!"

            # Object of model_name
            model = self.env[model_name].sudo()
            user_ids = self.env['res.partner'].sudo().browse(
                partner_id).user_ids
            if len(user_ids) > 1:
                user_ids = user_ids[0]

            model_record = model.browse(rec_id)
            if hasattr(model_record, 'report_token'):
                if model_record:
                    model_record.with_user(
                        user_ids).check_access_rights('read')
                    model_record.with_user(
                        user_ids).check_access_rule('read')

                    # Create Access Token and Set in Record.
                    token = model_record.report_token
                    if not token:
                        token = secrets.token_hex(16)
                        model_record.report_token = token
                    url = model_record.get_base_url()+'/report/%(report_type)s/%(report_name)s/%(record_id)s?access_token=%(token)s' % ({
                        'report_type': 'excel' if report_type == 'excel' else 'custom',
                        'report_name': model_name if report_type == 'excel' else report_name,
                        'record_id': rec_id,
                        'token': token,
                    })
                    if report_type == 'excel':
                        url += '&cid={}'.format(partner_id)
                result.update({
                    'success': True,
                    'url': url
                })
        except Exception as e:
            result.update({
                'error': str(e),
                'success': False
            })
        return result
