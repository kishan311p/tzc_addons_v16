from odoo import models,fields,api,_

class catalog_process_error_wizard_spt(models.TransientModel):
    _name="catalog.process.error.wizard.spt"
    _description = 'Catalog Process Error Wizard'

    catalog_id = fields.Many2one('sale.catalog')
    zero_qty_products = fields.Many2many("sale.catalog.line","catalog_process_error_wizard_zero_product_sale_catalog_line",'catalog_process_error_wizard_id','catalog_line_id',"Zero Qty Products")
    managed_qty_products = fields.Many2many("sale.catalog.line","catalog_process_error_wizard_managed_product_sale_catalog_line","catalog_process_wizard_id",'catalog_lien_id',"Managed Qty Products")

    def btn_process(self):
        self.ensure_one()
        if self.zero_qty_products:
            self.zero_qty_products.unlink()
        for line in self.managed_qty_products:
            catalog_line = self.catalog_id.line_ids.filtered(lambda x: x.id == line.id)
            if catalog_line:
                catalog_line.write({"product_qty":line.product_qty_available if self.catalog_id.base_on_qty == 'total_qty' else line.qty_available_spt })
        return self.catalog_id.send_catalogs_to_customers_spt()
