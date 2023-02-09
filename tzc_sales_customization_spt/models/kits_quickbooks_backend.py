from base64 import b64encode
from odoo import api, fields, models, _
import requests
import json
from odoo.exceptions import UserError
from requests_oauthlib import OAuth1Session, OAuth2Session
from base64 import b64encode

class kits_quickbooks_backend(models.Model):
    _name = "kits.quickbooks.backend"
    _rec_name = "name"

    name = fields.Char("Name")
    base_url = fields.Char("Base URL")
    request_url = fields.Char("Request URL")
    access_token = fields.Char("Access Token")
    company_id = fields.Char("Company Id(Realm Id)")
    state = fields.Selection([('draft','Draft'), ('confirm','Confirm')],default="draft",string="State")
    client_key = fields.Char("Client Key")
    client_secret = fields.Char("Client Secret")
    refresh_token = fields.Char("Refresh Token")

    @api.model
    def create(self, vals):
        res = super(kits_quickbooks_backend, self).create(vals)
        res.name = self.env['ir.sequence'].next_by_code('unique.quickbooks.backend.sequence')
        return res

    def action_test_connection(self):
        try:
            response = {}
            self = self.env.context.get("backend_id") if "backend_id" in self.env.context.keys() else self
            url = self.base_url + '/v3/company/' + self.company_id + '/customer/1'
            headers = {
                'Accept': 'application/json',
                'Authorization': 'Bearer '+ self.access_token,
                'Content-Type': 'application/json',
                }
            response = requests.request("GET", url, headers=headers)
            response.raise_for_status()
            if response.status_code == 200:
                self.state = "confirm"
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': "Connection Test Succeeded!",
                        'message': "Everything seems properly set up!",
                        'sticky': False,
                    }
                }
            else:   
                return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': { 
                            'title': "Connection Test Failed!",
                            'message': "Something is Wrong!",
                            'sticky': False,
                        }
                    }
        except Exception as e:
            message_dict = json.loads(response.text).get('fault').get('error')[0] if response != {} and json.loads(response.text).get('fault').get('error') != [] else {}
            if message_dict:
                if 'AuthenticationFailed' in message_dict.get('message') and 'Token expired' in message_dict.get('detail'):
                    keys = self.get_access_token(self)
                    access_token = keys.get('access_token')
                    refresh_token = keys.get('refresh_token')
                    self.write({'access_token' : access_token, 'refresh_token':refresh_token})
                    self.action_test_connection()
                else:
                    raise UserError(_(f"Something went wrong beacuse of {str(e)}"))
            else:
                raise UserError(_("Test Connection Failed!"))

    def get_access_token(self, backend_id):
        try:
            self = backend_id
            headeroauth = OAuth2Session(self.client_key)

            client_cred = (self.client_key + ":" + self.client_secret).encode('utf-8')
            b = bytes(client_cred)
            auth = "Basic " + b64encode(b).decode('utf-8')

            api_method = 'https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer'

            headers = {
                'authorization': auth,
                'accept': 'application/json',
                'content-type': 'application/x-www-form-urlencoded',
            }
            body = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
            }
            fetch_token = headeroauth.post(api_method, data=body, headers=headers)
            fetch_token.raise_for_status()
            keys = {}
            if fetch_token.status_code == 200:
                keys = fetch_token.json()
            return keys
        except Exception as e:
            raise UserError(_(e))

    def export_customer_action(self):
        partner_ids = self.env['res.partner'].browse(self._context.get('active_ids')) if ('active_ids' in self._context.keys() and self._context.get('active_ids')) else self.env['res.partner'].search([])
        self = self._context.get('backend_id') if ('backend_id' in self._context.keys() and self._context.get('backend_id')) else self
        try:
            self.action_test_connection()
        except Exception as e:
            raise UserError(_(str(e)))
        for record in self:
            try:
                res = {}
                account_obj = self.env['account.move']  
                for partner_id in partner_ids:
                    customer_name = account_obj.format_name(partner_id.display_name)
                    if customer_name[-1] == ' ':
                        customer_name = customer_name[:-1] 
                    query = "Select * from Customer where FullyQualifiedName='%s'" % (customer_name)
                    customer_url = record.base_url + '/v3/company/' + record.company_id + '/query?query=' + query
                    headers = {
                    'Accept': 'application/json',
                    'Authorization': 'Bearer '+ record.access_token,
                    'Content-Type': 'application/json'  
                    }
                    res = requests.request("GET", customer_url, headers=headers)
                    res_dict = json.loads(res.text)
                    if 'fault' in res_dict.keys():
                        message_dict = res_dict.get('fault').get('error')[0] if res_dict.get('fault').get('error') != [] else {}
                        if 'AuthenticationFailed' in message_dict.get('message') and 'Token expired' in message_dict.get('detail'):
                            self.with_context(backend_id=self).export_customer_action()
                    res.raise_for_status()
                    if "QueryResponse" in res_dict.keys() and res_dict.get("QueryResponse") == {}:
                        try:
                            response = {}
                            url = self.base_url + "/v3/company/" + self.company_id + "/customer"
                            payload = account_obj.customer_payload(partner_id)
                            response = requests.request("POST", url, headers=headers, data=json.dumps(payload)) 
                            response.raise_for_status()
                        except Exception as e:
                            error_msg = json.loads(response.text).get('Fault').get("Error")[0].get("Detail") if (response != {} and "Fault" in json.loads(response.text).keys() and json.loads(response.text).get('Fault')) else e
                            raise UserError(_(f"{error_msg}"))
            except Exception as e:
                error_msg = res_dict.get('Fault').get("Error")[0].get("Detail") if (res != {} and "Fault" in res_dict.keys() and res_dict.get('Fault')) else e
                raise UserError(_(f"{error_msg}"))
            
    
    def export_product_action(self):
        # product_ids = self._context.get('product_ids') if ('product_ids' in self._context.keys() and self._context.get('product_ids')) else self.env['product.product'].search([])
        product_ids = self.env['product.product'].browse(self._context.get('active_ids')) if ('active_ids' in self._context.keys() and self._context.get('active_ids')) else self.env['product.product'].search([])
        self = self._context.get('backend_id') if ('backend_id' in self._context.keys() and self._context.get('backend_id')) else self
        try:
            self.action_test_connection()
        except Exception as e:
            raise UserError(_(str(e)))
        for record in self:
            try:
                res = {}
                account_obj = self.env['account.move']
                for product_id in product_ids:
                    product_name = account_obj.format_name(product_id.display_name)
                    if product_name[-1] == ' ':
                        product_name = product_name[:-1]
                    query = "Select * from Item where Name='%s'" % (product_name)
                    product_url = record.base_url + '/v3/company/' + record.company_id + '/query?query=' + query
                    headers = {
                    'Accept': 'application/json', 
                    'Authorization': 'Bearer '+  record.access_token,
                    'Content-Type': 'application/json',
                    }
                    res = requests.request("GET", product_url, headers=headers)
                    res_dict = json.loads(res.text)
                    if 'fault' in res_dict.keys():
                        message_dict = res_dict.get('fault').get('error')[0] if res_dict.get('fault').get('error') != [] else {}
                        if 'AuthenticationFailed' in message_dict.get('message') and 'Token expired' in message_dict.get('detail'):
                            # self.action_test_connection()
                            self.with_context(backend_id=self).export_product_action()
                    res.raise_for_status()
                    if "QueryResponse" in res_dict.keys() and res_dict.get("QueryResponse") == {}:
                        try:
                            response = {}
                            url = self.base_url + "/v3/company/" + self.company_id + "/item"
                            payload = account_obj.product_payload(product_id)
                            response = requests.request("POST", url, headers=headers, data=payload)
                            response.raise_for_status()
                        except Exception as e:
                            error_msg = json.loads(response.text).get('Fault').get("Error")[0].get("Detail") if (response != {} and "Fault" in json.loads(response.text).keys() and json.loads(response.text).get('Fault')) else e
                            raise UserError(_(f"{error_msg}"))
                    else:
                        return res
            except Exception as e:
                error_msg = res_dict.get('Fault').get("Error")[0].get("Detail") if (res != {} and "Fault" in res_dict.keys() and res_dict.get('Fault')) else e
                raise UserError(_(f"{error_msg}"))


