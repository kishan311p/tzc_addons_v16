from email import message
from odoo import _, api, fields, models, tools
from odoo.tools import config,ustr
from odoo.sql_db import TestCursor
from collections import OrderedDict
from odoo.exceptions import UserError
from bs4 import BeautifulSoup
import logging

_logger = logging.getLogger(__name__)


class ir_report_action(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self,report_ref,docids ,res_ids=None, data=None):
        if not data:
            data = {}
        data.setdefault('report_type', 'pdf')

        # In case of test environment without enough workers to perform calls to wkhtmltopdf,
        # fallback to render_html.
        if (tools.config['test_enable'] or tools.config['test_file']) and not self.env.context.get('force_report_rendering'):
            return self._render_qweb_html(res_ids, data=data)

        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.
        context = dict(self.env.context)
        if not config['test_enable']:
            context['commit_assetsbundle'] = True

        # Disable the debug mode in the PDF rendering in order to not split the assets bundle
        # into separated files to load. This is done because of an issue in wkhtmltopdf
        # failing to load the CSS/Javascript resources in time.
        # Without this, the header/footer of the reports randomly disapear
        # because the resources files are not loaded in time.
        # https://github.com/wkhtmltopdf/wkhtmltopdf/issues/2083
        context['debug'] = False

        # The test cursor prevents the use of another environnment while the current
        # transaction is not finished, leading to a deadlock when the report requests
        # an asset bundle during the execution of test scenarios. In this case, return
        # the html version.
        if isinstance(self.env.cr, TestCursor):
            return self.with_context(context)._render_qweb_html(res_ids, data=data)[0]

        save_in_attachment = OrderedDict()
        # Maps the streams in `save_in_attachment` back to the records they came from
        stream_record = dict()
        if res_ids:
            # Dispatch the records by ones having an attachment and ones requesting a call to
            # wkhtmltopdf.
            Model = self.env[self.model]
            record_ids = Model.browse(res_ids)
            wk_record_ids = Model
            if self.attachment:
                for record_id in record_ids:
                    attachment = self.retrieve_attachment(record_id)
                    if attachment:
                        stream = self._retrieve_stream_from_attachment(
                            attachment)
                        save_in_attachment[record_id.id] = stream
                        stream_record[stream] = record_id
                    if not self.attachment_use or not attachment:
                        wk_record_ids += record_id
            else:
                wk_record_ids = record_ids
            res_ids = wk_record_ids.ids

        # A call to wkhtmltopdf is mandatory in 2 cases:
        # - The report is not linked to a record.
        # - The report is not fully present in attachments.
        if save_in_attachment and not res_ids:
            _logger.info('The PDF report has been generated from attachments.')
            self._raise_on_unreadable_pdfs(
                save_in_attachment.values(), stream_record)
            return self._post_pdf(save_in_attachment), 'pdf'

        if self.get_wkhtmltopdf_state() == 'install':
            # wkhtmltopdf is not installed
            # the call should be catched before (cf /report/check_wkhtmltopdf) but
            # if get_pdf is called manually (email template), the check could be
            # bypassed
            raise UserError(
                _("Unable to find Wkhtmltopdf on this system. The PDF can not be created."))

        html = self.with_context(context)._render_qweb_html(
            report_ref,docids,data=data)[0]

        # Ensure the current document is utf-8 encoded.
        html = html.decode('utf-8')

        bodies, html_ids, header, footer, specific_paperformat_args = self.with_context(
            context)._prepare_html(html)

        if self.attachment and set(res_ids) != set(html_ids):
            raise UserError(_("The report's template '%s' is wrong, please contact your administrator. \n\n"
                              "Can not separate file to save as attachment because the report's template does not contains the attributes 'data-oe-model' and 'data-oe-id' on the div with 'article' classname.") % self.name)

        soup = BeautifulSoup(bodies[0].encode("utf-8"), "html.parser")
        tbody_tags = soup.find_all('tbody')
        if tbody_tags:
            tr_tags = tbody_tags[0].find_all('tr')
            for tag in tr_tags:
                if tag.findChildren():
                    for child in tag.findChildren():
                        if child.get('name') == 'td_image' or child.get('name') == 'td_image_secondary':
                            child_data = child(lambda x:x.string and 'teameto' in x.string)
                            if child_data:
                                product_link = child_data[0].string
                                child(lambda x:x.string and 'teameto' in x.string)[0].extract()
                                if self.xml_id in ['tzc_sales_customization_spt.action_catalog_report_pdf','tzc_sales_customization_spt.action_catalog_report_spt','tzc_sales_customization_spt.action_confirm_catalog_report_spt']:
                                    new_tag = soup.new_tag("img", src=product_link,onerror="this.onerror=null;this.src='https://www.teameto.com/web/static/src/img/placeholder.png';", style="max-height:130px; max-width:270px;")
                                elif report_ref == 'tzc_sales_customization_spt.confirm_catalog_report_pdf_template':
                                    new_tag = soup.new_tag("img", src=product_link,onerror="this.onerror=null;this.src='https://www.teameto.com/web/static/src/img/placeholder.png';", style="max-height:130px; max-width:270px;")
                                else:
                                    new_tag = soup.new_tag("img", src=product_link,onerror="this.onerror=null;this.src='https://www.teameto.com/web/static/src/img/placeholder.png';", style="max-height:50px; max-width:120px;")
                                # child.find_all('div')[0].append(new_tag) if child.find_all('div') else None
                                child.append(new_tag)
            bodies = [soup]

        pdf_content = self._run_wkhtmltopdf(
            bodies,
            report_ref=report_ref,
            header=header,
            footer=footer,
            landscape=context.get('landscape'),
            specific_paperformat_args=specific_paperformat_args,
            set_viewport_size=context.get('set_viewport_size'),
        )
        if res_ids:
            _logger.info('The PDF report has been generated for model: %s, records %s.' % (
                self.model, str(res_ids)))
            self._raise_on_unreadable_pdfs(
                save_in_attachment.values(), stream_record)
            return self._post_pdf(save_in_attachment, pdf_content=pdf_content, res_ids=html_ids), 'pdf'
        return pdf_content, 'pdf'


class ir_mail_server(models.Model):
    _inherit = 'ir.mail_server'

    def test_smtp_connection(self):
        for server in self:
            smtp = False
            try:
                smtp = self.connect(mail_server_id=server.id)
                # simulate sending an email from current user's address - without sending it!
                email_from  = self.env.user.email if not self.env.context.get('cron') else self.env.context.get('user_id').email
                email_to = 'noreply@odoo.com'
                if not email_from:
                    raise UserError(_('Please configure an email on the current user to simulate '
                                      'sending an email message via this outgoing server'))
                # Testing the MAIL FROM step should detect sender filter problems
                (code, repl) = smtp.mail(email_from)
                if code != 250:
                    raise UserError(_('The server refused the sender address (%(email_from)s) '
                                      'with error %(repl)s') % locals())
                # Testing the RCPT TO step should detect most relaying problems
                (code, repl) = smtp.rcpt(email_to)
                if code not in (250, 251):
                    raise UserError(_('The server refused the test recipient (%(email_to)s) '
                                      'with error %(repl)s') % locals())
                # Beginning the DATA step should detect some deferred rejections
                # Can't use self.data() as it would actually send the mail!
                smtp.putcmd("data")
                (code, repl) = smtp.getreply()
                if code != 354:
                    raise UserError(_('The server refused the test connection '
                                      'with error %(repl)s') % locals())
            except UserError as e:
                # let UserErrors (messages) bubble up
                raise e
            except Exception as e:
                raise UserError(_("Connection Test Failed! Here is what we got instead:\n %s") % ustr(e))
            finally:
                try:
                    if smtp:
                        smtp.close()
                except Exception:
                    # ignored, just a consequence of the previous exception
                    pass

        title = _("Connection Test Succeeded!")
        message = _("Everything seems properly set up!")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'sticky': False,
            }
        }

    def outgoing_mailserver_cred_validation(self):
        mail_server_ids = self.search([('active','=',True)])
        user_ids = self.env.ref('base.group_system').users
        if mail_server_ids and user_ids:
            for server in mail_server_ids:
                for user in user_ids:
                    try:
                        server.with_context(cron=True,user_id=user).test_smtp_connection()
                    except:
                        notification = []
                        body = {
                                        'type': 'simple_notification', 
                                        'title': 'Mail server failed', 
                                        'message': 'Outgoing mail server "%s" is not working.'%server.name, 
                                        'sticky': True, 
                                        'warning': True
                                    }
                        notification.append([(self._cr.dbname, 'res.partner', user.partner_id.id),body])
                        self.env['bus.bus'].sendmany(notification)
