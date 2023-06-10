from odoo import models, fields,tools, api, _
from odoo.tools.translate import _
from odoo.exceptions import Warning

class python_script_runner(models.Model):
    _name = "python.script.runner"
    _description = 'Python Script Runner'
    
    name=fields.Char(string='Name',size=1024,required=True)
    code=fields.Text(string='Python Code',required=True)
    result=fields.Text(string='Result' ,readonly=True)
        
    
    def execute_script(self):
        localdict = {'self':self,'user_obj':self.env.user}
        for obj in self:
            try :
                exec(obj.code, localdict)
                if localdict.get('result', False):
                    self.write({'result':localdict['result']})
                else : 
                    self.write({'result':''})
            except Exception as e:
                raise Warning('Python code is not able to run ! message : %s' %(e))
                
        return True
#     def execute_script(self):
# brand_ids = self.env['product.brand.spt'].search(['|',('active','=',True),('active','=',False)])
# for brand in brand_ids:
#     custom_message = ''
#     if brand.product_ids:
#         custom_message = brand.product_ids.mapped(lambda x:x.custom_message)
#         custom_message = custom_message[0]
#     brand.description = custom_message

    # def execute_script(self):
    #     color_code_obj = self.env['kits.product.color.code']
    #     model_obj = self.env['product.model.spt']
    #     bridge_size_obj = self.env['product.bridge.size.spt']
    #     temple_size_obj = self.env['product.temple.size.spt']
    #     eye_size_obj = self.env['product.size.spt']
        
    #     product_ids = self.env['product.product'].search([])
        
    #     for product in product_ids:
    #         model_id = model_obj.search([('brand_id','=',product.brand.id),('name','=',product.model.name)])
    #         if not model_id:
    #             model_id = model_obj.create({
    #                 'name' : product.model.name,
    #             })
    #         model_id.brand_id =  product.brand.id
    #         product.model = model_id.id
            
    #         color_code = color_code_obj.search([('color','=',product.color_code.color),('model_id','=',product.model.id),('name','=',product.color_code.name)])
    #         if not color_code:
    #             color_code = color_code_obj.create({
    #                 'name' : product.color_code.name,
    #                 'color' : product.color_code.color,
    #             })
    #         product.color_code = color_code.id
    #         color_code.model_id = model_id.id
            
    #         bridge_size = bridge_size_obj.search([('name','=',product.bridge_size.name),('bridgesize_id','=',product.color_code.id)])
    #         if not bridge_size:
    #             bridge_size = bridge_size_obj.create({
    #                 'name' : product.bridge_size.name,
    #                 'bridgesize_id' : product.color_code.id
    #             })
    #         bridge_size.bridgesize_id = color_code.id
    #         product.bridge_size = bridge_size.id

    #         temple_size = temple_size_obj.search([('name','=',product.temple_size.name),('templesize_id','=',product.color_code.id)])
    #         if not temple_size:
    #             temple_size = temple_size_obj.create({
    #                 'name' : product.temple_size.name,
    #                 'templesize_id' : product.color_code.id
    #             })
    #         product.temple_size = temple_size.id
    #         temple_size.templesize_id = color_code.id
            
    #         eye_size = eye_size_obj.search([('name','=',product.eye_size.name),('eyesize_id','=',product.color_code.id)])
    #         if not eye_size:
    #             eye_size = eye_size_obj.create({
    #                 'name' : product.eye_size.name,
    #                 'eyesize_id' : product.color_code.id
    #             })
    #         product.eye_size = eye_size.id
    #         eye_size.eyesize_id = color_code.id

    # def execute_script(self):
    #     for rec in self.env['res.partner'].search([]):
    #         if rec.email:
    #             if rec.mailgun_verification:
    #                 rec.mailgun_verification_status = 'approved'
    #             else:
    #                 rec.mailgun_verification_status = 'rejected'
    #         else:
    #             rec.mailgun_verification_status = False

    # Apply special discount after expire sale
    # def execute_script(self):
    #     order_id = 3052
    #     inflation_id = 2
    #     special_discount_id = 2

    #     inflation_id = self.env['kits.inflation'].browse(inflation_id)
    #     special_discount_id = self.env['tzc.fest.discount'].browse(special_discount_id)

    #     for rec in self.env['sale.order'].browse(order_id):
    #         for line in rec.order_line:
    #             if inflation_id:
    #                 inflation_rule_ids = self.env['kits.inflation.rule'].search([('country_id','in',self.env.user.country_id.ids),('brand_ids','in',line.product_id.brand.ids),('inflation_id','=',inflation_id.id)])
    #                 inflation_rule = inflation_rule_ids[-1] if inflation_rule_ids else False
    #                 line.price_unit = round(line.price_unit+(line.price_unit*inflation_rule.inflation_rate /100),2)
    #                 line.unit_discount_price = round(line.unit_discount_price+(line.unit_discount_price*inflation_rule.inflation_rate /100),2)
    #             if special_discount_id:
    #                 special_disocunt_line_id = self.env['kits.special.discount'].search([('country_id','in',self.env.user.partner_id.country_id.ids),('brand_ids','in',line.product_id.brand.ids),('tzc_fest_id','=',special_discount_id.id)])
    #                 price_rule_id = special_disocunt_line_id[-1] if special_disocunt_line_id else False
    #                 line.unit_discount_price = round((line.unit_discount_price - line.unit_discount_price * price_rule_id.discount / 100),2)
    #                 line.fix_discount_price_spt = round(line.price_unit - line.unit_discount_price,2)
                
    #             line._onchange_unit_discounted_price_spt()
    #             line._onchange_fix_discount_price_spt()
    #             line._onchange_discount_spt()



#     def execute_script(self):
# order_id = [2880]
# for ord in order_id:
#     order = self.env['sale.order'].browse(ord)
#     if order:
#         for line in order.order_line:
#             product_price = 0.0
#             our_price = 0.0
#             if order.partner_id.property_product_pricelist.currency_id.name == 'CAD':
#                 product_price = line.product_id.lst_price
#                 if line.product_id.sale_type:
#                     if line.product_id.sale_type == 'clearance':
#                         our_price = line.product_id.clearance_cad
#                     elif line.product_id.sale_type == 'on_sale':
#                         our_price = line.product_id.on_sale_cad
#                 else:
#                     our_price = line.product_id.lst_price
#             else:
#                 product_price = line.product_id.lst_price_usd
#                 if line.product_id.sale_type:
#                     if line.product_id.sale_type == 'clearance':
#                         our_price = line.product_id.clearance_usd
#                     elif line.product_id.sale_type == 'on_sale':
#                         our_price = line.product_id.on_sale_usd
#                 else:
#                     our_price = line.product_id.lst_price_usd

#             line.price_unit = product_price
#             line.unit_discount_price = our_price
#             line._onchange_unit_discounted_price_spt()
#             line._onchange_fix_discount_price_spt()
#             line._onchange_discount_spt()

    #     picking_ids = self.env['stock.picking'].search([('sale_id','=',False),('state','!=','cancel')])
    #     print(picking_ids.mapped('name'))

    # order_ids = self.env['sale.order'].browse([2721,2715,2708,2719,2718,2714])
    # for order_id in order_ids:
    #     for line in order_id.order_line.filtered(lambda x:not x.product_id.is_shipping_product and not x.product_id.is_admin and not x.product_id.is_global_discount):
    #         pricelist_price = order_id.partner_id.property_product_pricelist.get_product_price(line.product_id,line.product_uom_qty,order_id.partner_id)
    #         if line.product_id.sale_type:
    #             if line.product_id.sale_type == 'on_sale':
    #                 if order_id.partner_id.property_product_pricelist.currency_id.name == 'CAD':
    #                     pricelist_price = line.product_id.on_sale_cad
    #                 else:
    #                     pricelist_price = line.product_id.on_sale_usd

    #             if line.product_id.sale_type == 'clearance':
    #                 if order_id.partner_id.property_product_pricelist.currency_id.name == 'CAD':
    #                     pricelist_price = line.product_id.clearance_cad
    #                 else:
    #                     pricelist_price = line.product_id.clearance_usd
                
    #             if order_id.currency_id:
    #                 if order_id.currency_id.name.lower() == 'usd':
    #                     sale_price = line.product_id.lst_price_usd
    #                 if order_id.currency_id.name.lower() == 'cad':
    #                     sale_price = line.product_id.lst_price

    #             line.price_unit = round(sale_price, 2)
    #             line.unit_discount_price = round(pricelist_price, 2)
    #             line.discount = round(100 - (pricelist_price / sale_price) * 100, 2)
    #             line.fix_discount_price = round((sale_price * line.discount)/100, 2)
    #             line._onchange_discount_spt()
    #             line._onchange_fix_discount_price_spt()
    #             line._onchange_unit_discounted_price_spt()
    #             line.product_uom_change()

    #         else:
    #             if order_id.currency_id:
    #                 if order_id.currency_id.name.lower() == 'usd':
    #                     sale_price = line.product_id.lst_price_usd
    #                 if order_id.currency_id.name.lower() == 'cad':
    #                     sale_price = line.product_id.lst_price

    #             line.price_unit = round(sale_price, 2)
    #             line.unit_discount_price = round(pricelist_price, 2)
    #             line.discount = round(100 - (pricelist_price / sale_price) * 100, 2)
    #             line.fix_discount_price = round((sale_price * line.discount)/100, 2)
    #             line._onchange_discount_spt()
    #             line._onchange_fix_discount_price_spt()
    #             line._onchange_unit_discounted_price_spt()
    #             line.product_uom_change()

            # for inv_line in line.invoice_lines:
            #     inv_line.price_unit = line.price_unit
            #     inv_line.discount_unit_price = line.unit_discount_price
            #     inv_line.discount = line.discount
            #     inv_line.unit_discount_price = line.fix_discount_price

    # def execute_script(self):
    #     order_id = self.env['sale.order'].search([('state','=','sent')])
    #     for order in order_id:
    #         if order.website_id and not order.catalog_id:
    #             order.write({'state':'draft'})
    
    # def execute_script(self):
    #     from datetime import datetime,timedelta
    #     new_date = datetime.now() - timedelta(days=100)
    #     product_ids = self.env['product.product'].search([('last_qty_update','=',False)])
    #     for product in product_ids:
    #         product.last_qty_update = new_date

# task_ids = self.env['project.task'].search([('task_priority','=',False)]).write({'task_priority':'3'})

    # def execute_script(self):
    #     order_ids = self.env['sale.order'].search([('state','not in',['draft','sent','received','cancel','merged'])])
    #     payment_obj = self.env['order.payment']
    #     for order in order_ids.filtered(lambda x:x.is_paid and x.paid_amount):
    #         payment_id = payment_obj.create({'order_id':order.id,'amount':float(order.paid_amount),'state':'approve'})
    #         self._cr.execute(''' UPDATE order_payment SET create_date = Null where id = %s '''%(payment_id.id))
    #         order._get_amount_paid()
    #         order._compute_amount_due()
    #         order._compute_payment_status()

# =============================================
# Set Partner Name

# partner_ids = self.env['res.partner'].search([])
# for partner in partner_ids:
#   partner._compute_display_name()
#   self._cr.commit()


    # def execute_script(self):
    #     sale_order_ids = self.env['sale.order'].search([('state','in',['sale','in_scanning','scanned','scan','shipped'])])
    #     wrong_order_list = []
    #     for order in sale_order_ids:
    #         picking_id = order.picking_ids.filtered(lambda x:x.state != 'cancel')
    #         if order.state == 'sale':
    #             if picking_id and picking_id.state != 'confirmed':
    #                 wrong_order_list.append(order.name)
    #         elif order.state == 'in_scanning':
    #             if picking_id and picking_id.state != 'in_scanning':
    #                 wrong_order_list.append(order.name)
    #         elif order.state == 'scanned':
    #             if picking_id and picking_id.state != 'scanned':
    #                 wrong_order_list.append(order.name)
    #         elif order.state == 'scan':
    #             if picking_id and picking_id.state != 'assigned':
    #                 wrong_order_list.append(order.name)
    #         elif order.state == 'shipped':
    #             if picking_id and picking_id.state != 'done':
    #                 wrong_order_list.append(order.name)

# ========================================= Auto Backup =============================================
    # def execute_script(self):
    #     host = 'localhost'
    #     port = '8069'
    #     backup_type = 'zip'
    #     folder = '/home/keypress-02/workspace/custom'

    #     path_to_write_to = '/home/sneptech-02/Test_dir'
    #     ip_host = '192.168.0.106'
    #     port_host = '22'
    #     sftp_host = '192.168.0.106'
    #     sftp_user = 'sneptech-02'
    #     sftp_password = 'testing'
    #     email_to_notify = False
    #     sftp_write = True

    #     try:
    #         if not os.path.isdir(folder):
    #             os.makedirs(folder)
    #     except:
    #         raise

    #     bkp_file = '%s_%s.%s' % (time.strftime('%Y_%m_%d_%H_%M_%S'), self._cr.dbname, backup_type)
    #     file_path = os.path.join(folder, bkp_file)
    #     fp = open(file_path, 'wb')
    #     try:
    #         fp = open(file_path, 'wb')
    #         self._take_dump(self._cr.dbname, fp, 'db.backup', backup_type)
    #         fp.close()
    #     except Exception as error:
    #         _logger.debug(
    #             "Couldn't backup database %s. Bad database administrator password for server running at "
    #             "http://%s:%s" % (self._cr.dbname, host, port))
    #         _logger.debug("Exact error from the exception: " + str(error))
        
    #     if sftp_write:
    #         try:
                
    #             _logger.debug('sftp remote path: %s' % path_to_write_to)

    #             try:
    #                 s = paramiko.SSHClient()
    #                 s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #                 s.connect(ip_host, port_host, sftp_user, sftp_password, timeout=20)
    #                 sftp = s.open_sftp()
    #             except Exception as error:
    #                 _logger.critical('Error connecting to remote server! Error: ' + str(error))

    #             try:
    #                 sftp.chdir(path_to_write_to)
    #             except IOError:
    #                 current_directory = ''
    #                 for dirElement in path_to_write_to.split('/'):
    #                     current_directory += dirElement + '/'
    #                     try:
    #                         sftp.chdir(current_directory)
    #                     except:
    #                         _logger.info('(Part of the) path didn\'t exist. Creating it now at ' + current_directory)
    #                         sftp.mkdir(current_directory, 777)
    #                         sftp.chdir(current_directory)
    #                         pass
    #             sftp.chdir(path_to_write_to)
    #             for f in os.listdir(folder):
    #                 if self._cr.dbname in f:
    #                     fullpath = os.path.join(folder, f)
    #                     if os.path.isfile(fullpath):
    #                         try:
    #                             sftp.stat(os.path.join(path_to_write_to, f))
    #                             _logger.debug(
    #                                 'File %s already exists on the remote FTP Server ------ skipped' % fullpath)
    #                         except IOError:
    #                             try:
    #                                 sftp.put(fullpath, os.path.join(path_to_write_to, f))
    #                                 _logger.info('Copying File % s------ success' % fullpath)
    #                             except Exception as err:
    #                                 _logger.critical(
    #                                     'We couldn\'t write the file to the remote server. Error: ' + str(err))

    #             sftp.chdir(path_to_write_to)

    #             _logger.debug("Checking expired files")
    #             for file in sftp.listdir(path_to_write_to):
    #                 if self._cr.dbname in file:
    #                     fullpath = os.path.join(path_to_write_to, file)
    #                     timestamp = sftp.stat(fullpath).st_mtime
    #                     createtime = datetime.datetime.fromtimestamp(timestamp)
    #                     now = datetime.datetime.now()
    #                     delta = now - createtime
    #                     # if delta.days >= rec.days_to_keep_sftp:
    #                     #     # Only delete files, no directories!
    #                     #     if (".dump" in file or '.' + backup_type in file):
    #                     #         _logger.info("Delete too old file from SFTP servers: " + file)
    #                     #         sftp.unlink(file)
    #             sftp.close()
    #             s.close()
    #         except Exception as e:
    #             try:
    #                 sftp.close()
    #                 s.close()
    #             except:
    #                 pass
    #             _logger.error('Exception! We couldn\'t back up to the FTP server. Here is what we got back instead: %s' % str(e))
    #             try:
    #                 ir_mail_server = self.env['ir.mail_server'].search([], order='sequence asc', limit=1)
    #                 message = "Dear,\n\nThe backup for the server " + host + " (IP: " + sftp_host + \
    #                             ") failed. Please check the following details:\n\nIP address SFTP server: " + \
    #                             sftp_host + "\nUsername: " + sftp_user + \
    #                             "\n\nError details: " + tools.ustr(e) + \
    #                             "\n\nWith kind regards"
    #                 catch_all_domain = self.env["ir.config_parameter"].sudo().get_param("mail.catchall_email.domain")
    #                 response_mail = "auto_backup@%s" % catch_all_domain if catch_all_domain else self.env.user.partner_id.email
    #                 msg = ir_mail_server.build_email(response_mail, [email_to_notify],
    #                                                     "Backup from " + host + "(" + sftp_host +
    #                                                     ") failed",
    #                                                     message)
    #                 ir_mail_server.send_email(msg)
    #             except Exception:
    #                 pass

    # def _take_dump(self, db_name, stream, model, backup_format='zip'):

    #     _logger.info('DUMP DB: %s format %s', self._cr.dbname, backup_format)

    #     cmd = ['pg_dump', '--no-owner']
    #     cmd.append(self._cr.dbname)
    #     if backup_format == 'zip':
    #         with odoo.tools.osutil.tempdir() as dump_dir:
    #             filestore = odoo.tools.config.filestore(self._cr.dbname)
    #             if os.path.exists(filestore):
    #                 shutil.copytree(filestore, os.path.join(dump_dir, 'filestore'))
    #             with open(os.path.join(dump_dir, 'manifest.json'), 'w') as fh:
    #                 db = odoo.sql_db.db_connect(self._cr.dbname)
    #                 with db.cursor() as cr:
    #                     json.dump(self._dump_db_manifest(cr), fh, indent=4)
    #             cmd.insert(-1, '--file=' + os.path.join(dump_dir, 'dump.sql'))
    #             odoo.tools.exec_pg_command(*cmd)
    #             if stream:
    #                 odoo.tools.osutil.zip_dir(dump_dir, stream, include_dir=False, fnct_sort=lambda file_name: file_name != 'dump.sql')
    #             else:
    #                 t=tempfile.TemporaryFile()
    #                 odoo.tools.osutil.zip_dir(dump_dir, t, include_dir=False, fnct_sort=lambda file_name: file_name != 'dump.sql')
    #                 t.seek(0)
    #                 return t
    #     else:
    #         cmd.insert(-1, '--format=c')
    #         stdin, stdout = odoo.tools.exec_pg_command_pipe(*cmd)
    #         if stream:
    #             shutil.copyfileobj(stdout, stream)
    #         else:
    #             return stdout 
        
    # def _dump_db_manifest(self, cr):
    #     pg_version = "%d.%d" % divmod(cr._obj.connection.server_version / 100, 100)
    #     cr.execute("SELECT name, latest_version FROM ir_module_module WHERE state = 'installed'")
    #     modules = dict(cr.fetchall())
    #     manifest = {
    #         'odoo_dump': '1',
    #         'db_name': cr.dbname,
    #         'version': odoo.release.version,
    #         'version_info': odoo.release.version_info,
    #         'major_version': odoo.release.major_version,
    #         'pg_version': pg_version,
    #         'modules': modules,
    #     }
    #     return manifest


# ==========================================================================================

    # def execute_script(self):
    #     import os

    #     self.env.cr.execute("""SELECT id,store_fname From ir_attachment""")
    #     attachment_ids = self._cr.fetchall()
    #     file_path = '/home/keypress-02/workspace/odoo_data/13.0/filestore/tzc_pro_db_with_filestore/'
    #     for id,path in attachment_ids:
    #         print(path)
    #         if path is not None:
    #             attachment_path = file_path + path
    #             file = os.path.isfile(attachment_path)
    #             if not file:
    #                 self.env.cr.execute("""DELETE FROM ir_attachment WHERE id = %s"""%id)
    #                 self._cr.commit()

    # def execute_script(self):
        # from urllib.request import urlopen

        # product_ids = [111356,101457,106989,111381]
        # for pro_id in product_ids:
        #     id = self.env['product.product'].search([('id','=',pro_id)])
        #     if id:
        #         try:
        #             urlopen(id.image_url)
        #             urlopen(id.image_secondary_url)
        #             id.is_image_missing = False
        #         except:
        #             id.is_image_missing = True

    # def execute_script(self):
    # from urllib.request import urlopen
    # import json
    # import os

    # data = '{"product_ids":[]}'
    # if not os.path.exists('data_json.json'):
    #     file = open('data_json.json','a+')
    #     json_data = json.dump(json.loads(data),file)
    #     file.close()

    # with open('data_json.json','r+') as open_file:
    #     data = json.load(open_file)
    #     product_ids = self.env['product.product'].search([('is_image_missing','=',False),'|',('active','=',True),('active','=',False)])
    #     for product in product_ids:
    #         if product.id not in data.get('product_ids',[]):
    #             try:
    #                 img_primary = urlopen(product.image_url)
    #                 image_secondary = urlopen(product.image_secondary_url)
    #                 product.is_image_missing = False
    #             except:
    #                 product.is_image_missing = True
    #             self._cr.commit()
    
    #             data['product_ids'].append(product.id)
    #     f = open('data_json.json','w')
    #     json.dump(data,f)
    #     f.close()

    # def execute_script(self):
    #     import os
    #     root_path = '/odoo/odoo_data/filestore/eto_production/'
    #     self.env.cr.execute("""select store_fname from ir_attachment""")
    #     attachment = self._cr.fetchall()
    #     db_attachment_list = []
    #     for file_name in attachment:
    #         if type(file_name[0]) == str:
    #             db_attachment_list.append(list(file_name)[0])
    #     system_attachment = []
    #     for path, subdirs, files in os.walk(root_path):
    #         for name in files:
    #             f_path = path+'/'+name
    #             system_attachment.append(f_path.split(root_path)[1])
                
    #     need_to_remove = [sys_attachment for sys_attachment in system_attachment if sys_attachment not in db_attachment_list]
    #     for remove in need_to_remove:
    #         attachment_path = root_path + remove
    #         file = os.path.isfile(attachment_path)
    #         if file:
    #             os.remove(attachment_path)
            
    #     result = len(need_to_remove)

    # def execute_script(self):
        # import os

        # self.env.cr.execute("""select id,store_fname from ir_attachment where res_model in ('product.product','product.template')""")
        # attachment_ids = self._cr.fetchall()
        # file_path = '/home/keypress-02/workspace/odoo_data/13.0/filestore/tzc_14_04_db/'
        # for id,path in attachment_ids:
        #     attachment_path = file_path + path
        #     file = os.path.isfile(attachment_path)
        #     if file:
        #         os.remove(attachment_path)
        #     self.env.cr.execute("""DELETE FROM ir_attachment WHERE id = %s"""%id)
        #     self._cr.commit() 

    # def execute_script(self):
    #     result = []
    #     product_ids = self.env['product.product'].search(['|',('active','=',True),('active','=',False)])
    #     for product in product_ids:
    #         product.write({
    #             'image_1024' : False,
    #             'image_128' : False,
    #             'image_1920' : False,
    #             'image_256' : False,
    #             'image_512' : False,
    #             'image_secondary' : False,
    #             'image_secondary_1024' : False,
    #             'image_secondary_128' : False,
    #             'image_secondary_1920' : False,
    #             'image_secondary_256' : False,
    #             'image_secondary_512' : False,
    #             'image_variant_1024' : False,
    #             'image_variant_128' : False,
    #             'image_variant_1920' : False,
    #             'image_variant_256' : False,
    #             'image_variant_512' : False,
    #         })
    #         result.append(product)
    #     result = len(result),result

    # def execute_script(self):
    #     product_ids = self.env['product.product'].search([])
    #     data_dict = {}
    #     for product in product_ids:
    #         data_dict[product.id]=[]
    #         for line in product.stock_move_line_ids:
    #             data_dict.get(product.id).append(line.origin or 'Null')

    # def execute_script(self):
    #     archived_product_ids = self.env['product.product'].search([('active','=',False)])
    #     archived_keyword = '_NotUsed'
    #     product_data = []
    #     for product in archived_product_ids:
    #         same_sku_product = self.env['product.product'].search([('default_code','=',product.default_code),('active','=',False)])
    #         product.default_code = product.default_code + archived_keyword * len(same_sku_product) if product.default_code else None
    #         product.variant_name = product.variant_name + archived_keyword if product.variant_name else None
    #         product.barcode = product.barcode + archived_keyword if product.barcode else None
    #         product.product_seo_keyword = product.product_seo_keyword + archived_keyword if product.product_seo_keyword else None
    #         product_data.append((product.variant_name,product.default_code,product.barcode,product.product_seo_keyword))
    #     print(product_data)

    # def execute_script(self):
    #     from bs4 import BeautifulSoup
    #     picking_id = self.env['stock.picking'].search([('id','=',748)])
    #     result = [str(('SKU','Qty'))]
    #     for message in picking_id.message_ids:
    #         if 'The initial demand has been updated.' in message.body:
    #             soup = BeautifulSoup(message.body, 'html.parser')
    #             body = soup.find_all('li')
    #             for txt in body:
    #                 if not 'Quantity' in txt.text:
    #                     product_name = txt.text.replace('\n','').replace(':','').strip()
    #                     product_sku = self.env['product.product'].search([('variant_name','=',product_name)],limit=1).default_code or ''
    #                 if 'Quantity' in txt.text:
    #                     qty = txt.text.split('>')[1].replace('\n','').strip()
    #             name = '('+ product_sku +','+ qty+')'
    #             result.append(name)
    #     result = '\n'.join(result)

    # def execute_script(self):
    #     from bs4 import BeautifulSoup
    #     picking_id = self.env['stock.picking'].search([('id','=',748)])
    #     result = [str(('Date','Product Name','Qty'))]
    #     for message in picking_id.message_ids:
    #         if 'The initial demand has been updated.' in message.body:
    #             soup = BeautifulSoup(message.body, 'html.parser')
    #             body = soup.find_all('li')
    #             date = message.date.strftime('%d-%m-%Y %H-%M-%S')
    #             for txt in body:
    #                 if not 'Quantity' in txt.text:
    #                     product_name = txt.text.replace('\n','').replace(':','').strip()
    #                 if 'Quantity' in txt.text:
    #                     qty = txt.text.split('>')[1].replace('\n','').strip()
    #             name = '('+date +','+ product_name +','+ qty+')'
    #             result.append(name)
    #     result = '\n'.join(result)

    # def execute_script(self):
    #     order_id = self.env['sale.order'].search([('id','=',1922)])
    #     backup_order = self.env['sale.order.backup.spt'].search([('order_id','=',order_id.id)],limit=1)
    #     result = []
    #     if backup_order:
    #         for line in backup_order.line_ids:
    #             product_sku = line.product_id.default_code
    #             demand_qty = line.product_uom_qty
    #             result.append(str((product_sku,demand_qty)))
    #     result = '\n'.join(result)

    # def execute_script(self):
    #     product_ids = self.env['product.product'].search([('sale_type','in',['on_sale','clearance'])])
    #     for product in product_ids:
    #         if product.sale_type == 'on_sale':
    #             product.on_sale_cad = round(product.on_sale_usd * 1.1,2)
    #             product.on_sale_cad_in_percentage = round((1 -(product.on_sale_cad/product.lst_price))*100,2)
    #         elif product.sale_type == 'clearance':
    #             product.clearance_cad = round(product.clearance_usd * 1.1,2)
    #             product.clearance_cad_in_percentage = round((1 -(product.clearance_cad/product.lst_price))*100,2)

    # def execute_script(self):
    #     # self.env['stock.picking'].search([('shipping_id.name','like','UPS')]).write({'is_ups':True})
    #     pass

    # def execute_script(self):
    #     sale_order_ids = self.env['sale.order'].search([('id','=',2185)])
    #     order_ids = []
    #     for order in sale_order_ids:
    #         for line in order.order_line:
    #             dicount_per = 100 * (line.price_unit - line.unit_discount_price) / line.price_unit
    #             order_ids.append(order.name) if dicount_per != line.discount else None

    #  100 * (original_price - discounted_price) / original_price


    # def execute_script(self):
    #     sale_order_ids = self.env['sale.order'].search([])
    #     order_ids = []
    #     for order in sale_order_ids:
    #         for line in order.order_line.filtered(lambda x: not x.product_id.is_shipping_product or not x.product_id.is_admin or x.product_id.is_global_discount):
    #             dicount_per = 100 * (line.price_unit - line.unit_discount_price) / line.price_unit if line.price_unit else None
    #             if dicount_per and round(dicount_per,2) != round(line.discount,2):
    #                 if order.name not in order_ids:
    #                     order_ids.append(order.name) 
    #     print(order_ids)

    # def execute_script(self):
    #     order_list = ['S01777', 'S01772', 'S01680', 'S01621', 'S00309', 'S00159', 'S00146', 'S00199', 'S00185', 'S00099', 'S00033']
    #     for order in order_list:
    #         order_id = self.env['sale.order'].search([('name','=',order)])
    #         for line in order_id.order_line:
    #             line._onchange_discount_spt()
    #             line._onchange_fix_discount_price_spt()
    #             line._onchange_unit_discounted_price_spt()

    # def execute_script(self):
    #     E_product_ids = self.env['product.product'].search([('categ_id','=',12)])
    #     E_product_ids.write({'categ_id':7})
    #     S_product_ids = self.env['product.product'].search([('categ_id','=',13)])
    #     S_product_ids.write({'categ_id':6})

    # def execute_script(self):
    #     color_code_ids = self.env['kits.product.color.code'].search([]).ids
    #     product_ids = self.env['product.product'].search([('is_shipping_product','=',False),('is_admin','=',False),('is_global_discount','=',False)])
    #     for product in product_ids:
    #         random_id = random.choice(color_code_ids)
    #         product.color_code = random_id

    # def execute_script(self):
    #     orders = []
    #     sale_order_ids = self.env['sale.order'].search([('state','not in',['draft','sent','received','cancel','merged'])])
    #     for order in sale_order_ids:
    #         if order.picking_ids:
    #             picking_id = order.picking_ids.filtered(lambda x:x.state != 'cancel')
    #             if picking_id and order.picked_qty != picking_id.delivered_qty:
    #                 result.append(order.name)

    #     result = orders
                
    # def execute_script(self):
    #     sale_order_ids = self.env['sale.order'].search([('state','not in',['draft','sent','received','cancel','merged'])])
    #     for order in sale_order_ids:
    #         if order.picking_ids:
    #             picking_id = order.picking_ids.filtered(lambda x:x.state != 'cancel')
    #             if picking_id and order.picked_qty != picking_id.delivered_qty:
    #                 self._cr.execute("""update sale_order set picked_qty = %s where id = %s"""%(picking_id.delivered_qty,order.id))
