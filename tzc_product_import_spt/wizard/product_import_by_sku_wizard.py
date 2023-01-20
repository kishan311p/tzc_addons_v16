from odoo import _, api, fields, models, tools

class product_import_by_sku_wizard(models.TransientModel):
    _name = "product.import.by.sku.wizard"
    _description = 'Product Import By SKU Wizard'

    product_sku = fields.Char("Product SKU\'s")

    def action_search(self):
        product_internal_ref = self.product_sku.split(',') if self.product_sku else ''
        import_ids = self.env['product.import.spt']
        tree_view = self.env.ref('tzc_product_import_spt.product_import_tree_view_spt')
        form_view = self.env.ref('tzc_product_import_spt.product_import_form_view_spt')
    
        for product_code in product_internal_ref:
            import_ids |= self.env['product.import.line.spt'].search([('default_code','=',product_code.strip()),'|',('active','=',True),('active','=',False)]).mapped('import_id')

        return {
        'name' : _('Product import by SKU'),
        'domain' : [('id','in',import_ids.ids)],
        'res_model' : 'product.import.spt',
        'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
        'type' : 'ir.actions.act_window',
        'target' : 'current',
        }
