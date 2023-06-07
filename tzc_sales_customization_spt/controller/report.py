import base64
import werkzeug.exceptions

from odoo import http
from odoo.http import request, content_disposition


class PublicReport(http.Controller):
    @http.route(['/report/custom/<reportname>/<int:docid>'], type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def custom_public_report(self, reportname=None, docid=False, **data):
        report = request.env.ref(reportname).sudo()
        context = dict(request.env.context)
        obj = request.env[report.model].sudo()

        record = obj
        try:
            record = obj.browse(docid)
        except:
            pass

        token = data.get('access_token', False)
        if not token or not record.ids or (hasattr(record, 'report_token') and token != record.report_token):
            return werkzeug.exceptions.HTTPException(description='Access Denied !')

        pdf = request.env['ir.actions.report'].with_context(context).sudo()._render_qweb_pdf(
            reportname, docid)[0]
        return request.make_response(pdf, headers=[('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))])

    @http.route(['/report/excel/<modalname>/<int:docid>'], type='http', auth='public', website=True, methods=['GET'], csrf=False)
    def custom_excel_report(self, modalname=None, docid=None, **data):
        token = data.get('access_token', False)
        if modalname == 'sale.order':
            order_obj = request.env['sale.order'].sudo()
            order = order_obj.browse(docid) if docid else order_obj
            # order = order.with_user(1)
            if order and (hasattr(order, 'report_token') and order.report_token != token):
                return werkzeug.exceptions.HTTPException(description='Access Denied !')

            vals = {'with_img': True, 'order_id': docid}
            wiz = request.env['order.report.with.image.wizard'].sudo().create(
                vals)
            wiz.action_process_report()
            # file_ext = '.xlsx' if not order.download_image_sent else '.xlsm'
            return request.make_response(
                base64.b64decode(wiz.sudo().report_file),
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition',
                     content_disposition('%s.xlsm' % (order.sudo().display_name)))
                ]
            )
        elif modalname == 'sale.catalog':
            catalog_id = request.env['sale.catalog'].sudo().browse(docid)
            if catalog_id and hasattr(catalog_id, 'report_token') and catalog_id.report_token != token:
                return werkzeug.exceptions.HTTPException(description='Access Denied !')

            cid = False
            try:
                cid = int(data.get('cid', False))
            except:
                pass

            wizard_id = request.env['kits.wizard.download.catalog.excel'].sudo().create({
                'catalog_id': docid,
                'partner_id': cid,
            })
            wizard_id.action_download_report()

            return request.make_response(
                base64.b64decode(wizard_id.file),
                headers=[
                    ('Content-Type', 'application/vnd.ms-excel'),
                    ('Content-Disposition',
                        content_disposition(catalog_id.sudo().display_name + '.xlsm'))
                ])
