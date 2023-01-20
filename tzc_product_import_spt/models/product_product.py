from odoo import _, api, fields, models, tools

class product_product(models.Model):
    _inherit = "product.product"

    #last_import_file_name = fields.Char("Last Import File name",compute="_get_last_update_file_name")

    # def _get_last_update_file_name(self):
    #     for rec in self:
    #         rec.last_import_file_name = False
    #         import_rec = self.env['product.import.line.spt'].search([('default_code','=',rec.default_code),'|',('active','=',True),('active','=',False)])
    #         if import_rec:
    #             last_update_date = max(import_rec.mapped('write_date'))
    #             last_product_import_line = import_rec.filtered(lambda x:x.write_date == last_update_date)
    #             rec.last_import_file_name = last_product_import_line.import_id.last_import_file_by_warehouse or ''

    def product_import_product_published(self):
        material_ids = self.env['product.material.spt'].search([('name','ilike','other')])
        shape_ids = self.env['product.shape.spt'].search([('name','ilike','other')])
        rim_type_ids = self.env['product.rim.type.spt'].search([('name','ilike','other')])
        color_ids = self.env['product.color.spt'].search([('name','ilike','other')])
        for record in self:
            if record.active and record.available_qty_spt >0 and not record.is_forcefully_unpublished and record.eye_size_compute > 0 and not record.is_image_missing:
                if record.sale_type:
                    record.brand.write({'sale_avl_brand':True})
                    record.product_color_name.write({'sale_avl_colour':True})
                    record.secondary_color_name.write({'sale_avl_colour':True})
                    record.shape_id.write({'sale_avl_shape':True})
                    record.rim_type.write({'sale_avl_rim_type':True})
                    record.material_id.write({'sale_avl_material':True})
                if record.new_arrivals:
                    record.brand.write({'new_arrival_avl_brand':True})
                    record.product_color_name.write({'new_arrival_avl_colour':True})
                    record.secondary_color_name.write({'new_arrival_avl_colour':True})
                    record.shape_id.write({'new_arrival_avl_shape':True})
                    record.rim_type.write({'new_arrival_avl_rim_type':True})
                    record.material_id.write({'new_arrival_avl_material':True})
                if record.categ_id.name.lower() in ['sunglass','s','sunglasses']:
                    record.brand.write({'sunglass_avl_brand':True})
                    record.product_color_name.write({'sunglass_avl_colour':True})
                    record.secondary_color_name.write({'sunglass_avl_colour':True})
                    record.shape_id.write({'sunglass_avl_shape':True})
                    record.rim_type.write({'sunglass_avl_rim_type':True})
                    record.material_id.write({'sunglass_avl_material':True})
                
                if record.categ_id.name.lower() in ['eyeglass','e','eyeglasses']:
                    record.brand.write({'eyeglass_avl_brand':True})
                    record.product_color_name.write({'eyeglass_avl_colour':True})
                    record.secondary_color_name.write({'eyeglass_avl_colour':True})
                    record.shape_id.write({'eyeglass_avl_shape':True})
                    record.rim_type.write({'eyeglass_avl_rim_type':True})
                    record.material_id.write({'eyeglass_avl_material':True})
                # record.brand.write({'website_published':True})
                # record.product_color_name.write({'is_published':True})
                # record.secondary_color_name.write({'is_published':True})
                # record.shape_id.write({'is_published':True})
                # record.rim_type.write({'is_published':True})
                # record.material_id.write({'is_published':True})
                record.is_published_spt =True

            else:
                record.is_published_spt =False
                if record.sale_type:
                    record.brand.write({'sale_avl_brand':False})
                    record.product_color_name.write({'sale_avl_colour':False})
                    record.secondary_color_name.write({'sale_avl_colour':False})
                    record.shape_id.write({'sale_avl_shape':False})
                    record.rim_type.write({'sale_avl_rim_type':False})
                    record.material_id.write({'sale_avl_material':False})
                if record.new_arrivals:
                    record.brand.write({'new_arrival_avl_brand':False})
                    record.product_color_name.write({'new_arrival_avl_colour':False})
                    record.secondary_color_name.write({'new_arrival_avl_colour':False})
                    record.shape_id.write({'new_arrival_avl_shape':False})
                    record.rim_type.write({'new_arrival_avl_rim_type':False})
                    record.material_id.write({'new_arrival_avl_material':False})
                if record.categ_id.name.lower() in ['sunglass','s','sunglasses']:
                    record.brand.write({'sunglass_avl_brand':False})
                    record.product_color_name.write({'sunglass_avl_colour':False})
                    record.secondary_color_name.write({'sunglass_avl_colour':False})
                    record.shape_id.write({'sunglass_avl_shape':False})
                    record.rim_type.write({'sunglass_avl_rim_type':False})
                    record.material_id.write({'sunglass_avl_material':False})
                
                if record.categ_id.name.lower() in ['eyeglass','e','eyeglasses']:
                    record.brand.write({'eyeglass_avl_brand':False})
                    record.product_color_name.write({'eyeglass_avl_colour':False})
                    record.secondary_color_name.write({'eyeglass_avl_colour':False})
                    record.shape_id.write({'eyeglass_avl_shape':False})
                    record.rim_type.write({'eyeglass_avl_rim_type':False})
                    record.material_id.write({'eyeglass_avl_material':False})
                # record.brand.write({'website_published':False})
                # record.product_color_name.write({'is_published':False})
                # record.secondary_color_name.write({'is_published':False})
                # record.shape_id.write({'is_published':False})
                # record.rim_type.write({'is_published':False})
                # record.material_id.write({'is_published':False})

            if record.brand.name.lower() == 'other':
                record.brand.write({
                    # 'website_published':False,
                    'eyeglass_avl_brand':False,'sunglass_avl_brand':False,'new_arrival_avl_brand':False,'sale_avl_brand':False})
                record.is_published_spt =False
            
            for material in  record.material_id:
                if material.id in material_ids.ids:
                    material.write({# 'is_published':False,
                        'eyeglass_avl_material':False,'sunglass_avl_material':False,'new_arrival_avl_material':False,'sale_avl_material':False})
                    record.is_published_spt =False

            for shape in  record.shape_id:
                if shape.id in shape_ids.ids:
                    shape.write({# 'is_published':False,
                        'eyeglass_avl_shape':False,'sunglass_avl_shape':False,'new_arrival_avl_shape':False,'sale_avl_shape':False})
                    record.is_published_spt =False
            
            if  record.rim_type and  record.rim_type.name.lower() == 'other':
                record.rim_type.write({#'is_published':False,
                    'eyeglass_avl_rim_type':False,'sunglass_avl_rim_type':False,'new_arrival_avl_rim_type':False,'sale_avl_rim_type':False})
                record.is_published_spt =False
            
            if record.product_color_name and record.product_color_name.name.lower() == 'other':
                record.product_color_name.write({# 'is_published':False,
                    'eyeglass_avl_colour':False,'sunglass_avl_colour':False,'new_arrival_avl_colour':False,'sale_avl_colour':False})
                record.is_published_spt =False
            
            if record.product_color_name and record.product_color_name.name.lower() == 'other':
                record.product_color_name.write({#'is_published':False,
                'eyeglass_avl_colour':False,'sunglass_avl_colour':False,'new_arrival_avl_colour':False,'sale_avl_colour':False})
                record.is_published_spt =False
    
