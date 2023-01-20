from curses.ascii import US
from odoo import http,_
from odoo.http import request
import json
from datetime import datetime, timedelta 
import pytz

class multi_website_reset_password(http.Controller):
    
    @http.route('/reset_password', type='json',method='POST',auth='public')
    def reset_password(self, **kwargs):
        url_data = request.httprequest
        try:
            token = url_data.values.get('token') if ('token' in url_data.values.keys() and url_data.values.get('token')) else False   
            if token:
                if request.jsonrequest == {}:
                    return self.throw_error('No data in Body!')
                data = request.jsonrequest
                if 'email' in data.keys() and not data.get('email'):
                    return self.throw_error('Email cannot be empty!')
                if 'new_password' in data.keys() and not data.get('new_password'):
                    return self.throw_error('New Password cannot be empty!')
                customer_id = request.env['kits.multi.website.customer'].search([('token','=',token), ('email','=',data.get('email'))])
                if customer_id:
                    try:
                        if datetime.strptime(datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S'),'%Y-%m-%d %H:%M:%S') > customer_id.url_validity + timedelta(hours=5.5):
                            return self.throw_error('Token Expired!')
                        else: 
                            new_password = request.env['kits.multi.website.customer']._get_encrypted_password(data.get('new_password'))
                            request._cr.execute("UPDATE kits_multi_website_customer SET password = '%s' where email = '%s'"%(new_password,customer_id.email))
                            request._cr.commit()
                            return {'status': 'Password Updated Successfully'}
                    except Exception as e:
                        return e
                else:
                    return self.throw_error('No such customer not found!')
            else:
                return self.throw_error('Token not Generated. Please regenerate it!')
        except Exception as e:
            return self.throw_error(e)
        
    def throw_error(self, error_msg):
        return {'error': error_msg}

    @http.route(['/send_email'], type='json', website=True,methods=['POST'],auth='public',csrf=False)
    def send_email(self, **kwargs):
        data = request.httprequest
        email = request.jsonrequest.get('email') if ('email' in request.jsonrequest.keys() and request.jsonrequest.get('email')) else False
        # mail_template = request.env.ref('kits_multi_website.multi_website_email_template')
        # mail_template.send_mail(self.id,force_send=True)
        try:
            if email:
                result = request.env['kits.multi.website.customer'].send_email(email)
                return result
            else:
                raise {"error": "Invalid Email!"}
        except Exception as e:
            return str(e)
        