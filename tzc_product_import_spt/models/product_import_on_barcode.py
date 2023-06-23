from odoo import _, api, fields, models
import json
from odoo.exceptions import UserError
class product_import_on_barcode(models.Model):
    _name = 'product.import.on.barcode'
    _description = 'Product Import On Barcode'
    
    name = fields.Char('Name')
    state = fields.Selection([
        ('draft','Draft'),
        ('in_process','In Process'),
        ('scanned','Rady To Process'),
        ('done','Done'),
    ], string='State', default='draft')
    line_ids = fields.One2many('product.import.on.barcode.line', 'import_id', string='Line')
    link = fields.Char('Link')
    
    def action_in_process(self):
        self.ensure_one()
        link = self.env['ir.config_parameter'].sudo().get_param('tzc_product_import_spt.import_url', '')+'?uid='+str(self.env.uid)+'&import_id='+str(self.id)+"&name="+self.name        
        self.write({'state': 'in_process','link': link})
        return {
            'type': 'ir.actions.act_url',
            'name': "New Prodict Import",
            'target': 'new',
            'url': self.link,
        }
    def action_ready_to_process(self):
        self.ensure_one()
        self.state = 'scanned'
    
    def action_process(self):
        product_obj = self.env['product.product']
        quant_obj = self.env['stock.quant']
        create_product_list = []
        for record in self:
            for line in self.line_ids:
                product_id = product_obj.with_context(pending_price =True).search([('barcode','=',line.barcode)],order='id desc',limit=1)
                product_dict ={
                    'categ_id' : line.categ_id.id,
                    'brand' : line.brand_id.id,
                    'model' : line.model_id.id,
                    'color_code' : line.mcc_id.id,
                    'bridge_size' : line.bridge_size_id.id,
                    'temple_size' : line.temple_size_id.id,
                    'eye_size' : line.eye_size_id.id,
                    'case_product_id' : line.case_product_id.id,
                    'product_color_name' : line.product_color_id.id,
                    'secondary_color_name' : line.secondary_color_id.id,
                    'lense_color_name' : line.lense_color_id.id,
                    'material_id' : line.material_id.id,
                    'shape_id' : line.shape_id.id,
                    'rim_type' : line.rim_type.id,
                    'gender' : line.gender,
                    'country_of_origin' : line.country_of_origin_id.id,
                    'barcode' : line.barcode,
                    'variant_name' : line.name,
                    'default_code' : line.internal_reference,
                    'product_seo_keyword' : line.seo_keyword,
                    'case_image_url' : line.case_image_url,
                    "image_url" : line.image_url,
                    "image_secondary_url" : line.image_secondary_url,
                    "gender" : line.gender
                }
                line.case_product_id.image_url = line.case_image_url
                if line.opration == 'create':
                    self._cr.execute("""
                        call create_product_template(%s,%s,%s,%s,%s,null);
                                     """,params=[line.internal_reference,json.dumps({"name" : line.name.replace("'","\'")}),True,line.categ_id.id,self.env.uid])
                    product_id = (self._cr.fetchone() or ([{}],))[0][0].get('currval',product_obj)
                    if product_id:
                        product_id = product_obj.browse(product_id)
                    self._cr.commit()
                if product_id and line.quantity:
                    warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)], limit=1)
                    if warehouse and warehouse.lot_stock_id:
                        product_qty = line.quantity + product_id.qty_available  if line.quantity and line.add_up_quantity else line.quantity
                        quant_obj.with_context(inventory_mode=True,inventory_name=self.name).create({
                                    'location_id': warehouse.lot_stock_id.id,
                                    'product_id': product_id.id,
                                    'inventory_quantity': product_qty
                                }).with_context(default_product_import_id=self.id).action_apply_inventory()
                    else:
                        raise UserError(_('Location not found.'))
                product_id.with_context(pending_price=True).write(product_dict)
                line.product_id = product_id.id
            record.state = 'done'
    
    @api.model_create_multi
    def create(self, vals):
        res= super(product_import_on_barcode,self).create(vals)
        for record in res:
            if record.name == '':
                record.name =  self.env['ir.sequence'].next_by_code('product.import.on.barcode')
        return res
    
