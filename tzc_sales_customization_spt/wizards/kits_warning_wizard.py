from odoo import models,fields,api,_
from odoo.exceptions import UserError

class kits_warning_wizard(models.TransientModel):
    _name = 'kits.warning.wizard'
    _description = 'Warning Wizard'

    message = fields.Text('Message')
    # package create
    package_name = fields.Char('Package Name')
    pacakge_seo_name = fields.Char('Package SEO Name')
    allowed_products = fields.Many2many('product.product','kits_warning_wiz_allowed_products_rel','kits_warning_wizard_id','allowed_product_id','Allowed Products')
    out_of_stock_products = fields.Many2many('product.product','kits_warning_wiz_out_of_stock_product_rel','kits_warning_wizard_id','out_of_stock_product_id','Out Of Stock Products')
    unpublished_products = fields.Many2many('product.product','kits_warning_wiz_product_product_rel','kits_warning_wiz_id','unpublished_product_id','Unpublished Products')

    def action_process(self):
        combo_prod_obj = self.env['kits.package.product']
        combo_prod_line_obj = self.env['kits.package.product.lines']
        if len(self.allowed_products):
            package_id = combo_prod_obj.search([('name','=',self.package_name)])
            if package_id:
                raise UserError(_('Package name is taken.'))
            package_id = combo_prod_obj.create({'name':self.package_name,'package_seo_name':self.pacakge_seo_name})
            for rec in self.allowed_products:
                product_price = rec.lst_price_usd
                if rec.sale_type:
                    if rec.sale_type == 'on_sale':
                        product_price = rec.on_sale_usd
                    if rec.sale_type == 'clearance':
                        product_price = rec.clearance_usd

                package = combo_prod_line_obj.create({
                    'combo_product_id':package_id.id,
                    'product_id':rec.id,
                    'product_price':rec.lst_price_usd,
                    'usd_price':product_price,
                    'qty':1
                })
                package._onchange_usd_price()
            return {
                'name':_('Package Product'),
                'view_mode':'form',
                'res_id':package_id.id,
                'res_model':'kits.package.product',
                'type':'ir.actions.act_window',
            }
        else:
            raise UserError(_('There are no products allowed to create Package.'))
