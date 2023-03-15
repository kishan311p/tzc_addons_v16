import werkzeug.exceptions

from odoo import http
from odoo.http import request


class PublicReport(http.Controller):
    @http.route(['/report/custom/<reportname>/<docid>'], type='http', auth='public', website=True, method=['GET'], csrf=False)
    def custom_public_report(self, reportname=None, docid=False, **data):
        report = request.env.ref(reportname)
        context = dict(request.env.context)
        obj = request.env[report.model].sudo()

        record = obj
        try:
            record = obj.browse(int(docid))
        except:
            pass

        token = data.get('access_token', False)
        if not token or not record.ids or (hasattr(record, 'report_token') and token != record.report_token):
            return werkzeug.exceptions.HTTPException(description='Access Denied !')

        pdf = report.with_context(context)._render_qweb_pdf(
            reportname, int(docid))[0]
        return request.make_response(pdf, headers=[('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))])
