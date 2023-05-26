from odoo import models, fields, api, _

class update_partner_in_order_wizard_spt(models.TransientModel):
    _name = 'update.partner.in.order.wizard.spt'
    _description = 'Update partner in sale order'
    
    partner_id = fields.Many2one('res.partner','Customers')
    sale_id = fields.Many2one('sale.order','Order')
    delivery_address_id = fields.Many2one('res.partner','Delivery Address')
    disc_options = fields.Selection(string='Discount Options', selection=[('keep_discount', 'Keep Discount'),('change_discount', 'Remove Discount & apply current price')],default="keep_discount")
    
    def action_process(self):
        for record in self.sudo():
            if record.sale_id and record.sale_id.partner_id:
                record.sale_id.partner_id = record.partner_id.id
                record.sale_id.partner_invoice_id = record.partner_id.id
                record.sale_id.onchange_partner_id()
                if record.delivery_address_id:
                    record.sale_id.partner_shipping_id = record.delivery_address_id.id
                record.sale_id.onchange_partner_shipping_id_kits()
                if record.sale_id.pricelist_id.id != record.sale_id.partner_id.id :
                    for line in record.sale_id.order_line:
                        discount = line.discount
                        line.discount = 0.0
                        line.product_id_change()
                        line._onchange_discount_spt()
                        line._onchange_fix_discount_price_spt()
                        line._onchange_unit_discounted_price_spt()
                        if not line.product_id.is_shipping_product and not line.product_id.is_admin and not line.product_id.is_global_discount:
                            if self.disc_options =='keep_discount':
                                if discount:
                                    line.discount = discount
                                    line._onchange_discount_spt()
                    
                for picking in record.sale_id.picking_ids:
                    if picking.state != 'cancel':
                        if record.delivery_address_id:
                            picking.partner_id = record.delivery_address_id.id
                        else:
                            delivery_address_id = self.env['res.partner'].search([('type','=','delivery'),('parent_id','=',record.partner_id.id)],limit=1)
                            picking.partner_id = delivery_address_id.id if delivery_address_id else record.partner_id.id
                        # picking.partner_id = record.partner_id.id
                        # picking.onchange_picking_type()
                    picking._get_recipent_address()
