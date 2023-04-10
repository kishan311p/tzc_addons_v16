from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class add_admin_fee_wizard(models.TransientModel):
    _name = "add.admin.fee.wizard"
    _description = "Admin Fee Wizard"

    admin_fee_price = fields.Float("Admin Fee")
    kits_so_id = fields.Many2one('sale.order','Sale Order')

    def add_admin_fee(self):
        product_id = self.env['product.product'].search([('is_admin','=',True)],limit=1)
        admin_fee_line = self.kits_so_id.order_line.filtered(lambda x: x.product_id == product_id)
        if product_id:
            if not admin_fee_line:
                order_line = [(0,0,{
                    'product_id':product_id.id,
                    'name':product_id.name,
                    'product_uom_qty':1.0,
                    'price_unit':self.admin_fee_price,
                    'unit_discount_price':self.admin_fee_price,
                    'is_admin':True,
                })]
                self.kits_so_id.write({'order_line':order_line})
            else:
                admin_fee_line.write({'price_unit':self.admin_fee_price,'unit_discount_price':self.admin_fee_price,'is_admin':True,'price_subtotal':self.admin_fee_price})
            self.kits_so_id._amount_all()
        else:
            raise UserError(_('Admin Fee Product not found.'))
