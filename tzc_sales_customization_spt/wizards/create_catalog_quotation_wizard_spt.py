from odoo import models,fields,api,_
from odoo.exceptions import UserError
class create_catalog_quotation_wizard_spt(models.TransientModel):
    _name = "create.catalog.quotation.wizard.spt"
    _description = 'Create Catalog Quotation Wizard'

    catalog_id = fields.Many2one('sale.catalog','catalog')
    domain_parnter_ids = fields.Many2many('res.partner','create_catalog_with_partner_real_for_domain','wizard_id','partner_id','Customers ')
    partner_ids = fields.Many2many('res.partner','create_catalog_with_partner_real','wizard_id','partner_id','Customers')


    def btn_process(self):
        error_list = []
        sale_order_obj = self.env['sale.order']
        sale_order_line_obj = self.env['sale.order.line']
        sale_catalog_line_obj = self.env['sale.catalog.line']
        for record in self:
            for customer_id in record.partner_ids:
                try:
                    fiscal_position_id = self.env['account.fiscal.position'].sudo()._get_fiscal_position(customer_id)
                    so_id = sale_order_obj.create({
                        'partner_id': customer_id.id,
                        'catalog_id': record.catalog_id.id,
                        'user_id':record.catalog_id.user_id.id,
                        'fiscal_position_id':fiscal_position_id.id if fiscal_position_id else False,
                        'source_spt' : 'Catalog',
                    })
                    self._cr.commit()
                    for line_id in record.catalog_id.line_ids.filtered(lambda x:x.product_qty != 0):
                        if customer_id.property_product_pricelist.currency_id.name == 'USD':
                            price_unit = line_id.product_pro_id.lst_price_usd
                        elif customer_id.property_product_pricelist.currency_id.name == 'CAD':
                            price_unit = line_id.product_pro_id.lst_price
                        else:
                            price_unit = line_id.product_price
                            # price_unit = self.env.user.partner_id.property_product_pricelist.get_product_price(line_id.product_pro_id,line_id.product_qty,self.env.user.partner_id)
                            
                        product_price = price_unit
                        if line_id.sale_type == 'on_sale' and so_id.partner_id and so_id.partner_id.property_product_pricelist :
                            # if so_id.partner_id.property_product_pricelist.currency_id.name == 'CAD':
                            #     price_unit = line_id.product_pro_id.on_sale_cad
                            # else:
                            price_unit = line_id.product_pro_id.on_sale_usd
                        
                        if line_id.sale_type == 'clearance' and so_id.partner_id and so_id.partner_id.property_product_pricelist :
                            # if so_id.partner_id.property_product_pricelist.currency_id.name == 'CAD':
                            #     price_unit = line_id.product_pro_id.clearance_cad
                            # else:
                                price_unit = line_id.product_pro_id.clearance_usd

                        unit_discount_price = price_unit
                        if line_id.discount:
                            unit_discount_price = round(product_price - (product_price *(line_id.discount * 0.01)),2)

                        order_line_id = sale_order_line_obj.create({
                            'order_id': so_id.id,
                            'name' : line_id.product_pro_id.display_name,
                            'product_id': line_id.product_pro_id.id,
                            'discount': line_id.discount or 0.0,
                            'product_uom_qty': line_id.product_qty,
                            'product_uom': line_id.product_pro_id.uom_id.id,
                            'sale_type' : line_id.sale_type,
                            'price_unit' : product_price,
                            'unit_discount_price': unit_discount_price,
                        })
                        self._cr.commit()
                        if order_line_id:
                            order_line_id.product_id_change()
                            # order_line_id._onchange_discount_spt()

                    # record.sale_order_id = so_id.id
                    so_id.action_quotation_sent()
                    # verified = so_id.partner_verification()
                    # quotation_template_id = self.env.ref('tzc_sales_customization_spt.tzc_email_template_catalog_quotation_spt') if verified else None
                    # quotation_template_id.send_mail(so_id.id,force_send=True) if verified else None
                    # confirmation_template_id = self.env.ref('tzc_sales_customization_spt.tzc_email_template_saleperson_quotation_spt')
                    # confirmation_template_id.send_mail(so_id.id,email_values={'email_to': so_id.user_id.partner_id.email},force_send=True)
                except Exception as error:
                    error_list.append(error.name)
        if error_list:
            raise UserError(_('\n'.join(error_list)))
