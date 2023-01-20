from odoo import models,fields,api,_

class kits_package_restriction(models.TransientModel):
    _name = 'kits.package.restriction'
    _description = 'Package Restriction'

    restricted_package_ids = fields.Many2many('kits.package.product','kits_package_restriction_package_product_rel','package_restriction_id','package_product_id',string="Unavailable/Restricted Packages")
    package_to_remove = fields.Many2many('kits.package.product','kits_package_to_remove_package_product_rel','package_to_remove_id','package_id',string="Package To Remove")
    order_id = fields.Many2one('sale.order','Sale Order')

    # process with packages
    def action_process_with_package(self):
        self.order_id.with_context({'package_allow':True}).action_confirm()
        return {'type': 'ir.actions.act_window_close'}

    # process removing packages
    def action_process_without_packages(self):
        self.sudo().order_id.package_order_lines.filtered(lambda x: x.product_id in self.package_to_remove).unlink()
        self.order_id.with_context({'package_allow':False}).action_confirm()
        return {'type': 'ir.actions.act_window_close'}
