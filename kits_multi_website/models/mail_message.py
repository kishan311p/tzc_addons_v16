from odoo import api, fields, models, _
import base64
class mail_message(models.Model):
    _inherit = 'mail.message'
    

    def get_mail_message_b2c(self,dictonry_list):
        for dictonry in dictonry_list:
            attachment_ids = self.browse(dictonry.get('id')).attachment_ids
            attachments_list = []
            try:
                for attachment_id in attachment_ids:
                    attachments_list.append({
                        'file': attachment_id.datas.decode('utf-8'),
                        "filename":attachment_id.name,
                        "mimetype":attachment_id.mimetype,
                        
                    })
            except:
                pass
            dictonry['attachments'] = attachments_list
        return dictonry_list