from odoo import _, api, fields, models, tools
import ast

class delivery_recovery_selection_wizard(models.TransientModel):
    _name = "delivery.recovery.selection.wizard"
    _description = "Delivery Recovery Selection Wizard"

    picking_id = fields.Many2one('stock.picking','Delivery Order')
    sale_id = fields.Many2one('sale.order','Order')

    def action_update_delivery(self):
        if self.picking_id and self.sale_id and self.picking_id.delivery_data:
            new_picking_id = self.sale_id.picking_ids.filtered(lambda x:x.state != 'cancel')
            data = ast.literal_eval(self.picking_id.delivery_data) or ''
            if data and data.get(self.picking_id.id):
                cancel_picking_data = data.get(self.picking_id.id)
                for delivery_data in cancel_picking_data:
                    product_id = self.env['product.product'].browse([delivery_data])
                    line_id = new_picking_id.move_ids_without_package.filtered(lambda x:x.product_id.id == product_id.id)
                    is_fedex = True if self.picking_id.shipping_id.provider == 'fedex' else False
                    is_ups = True if self.picking_id.shipping_id.provider == 'ups' else False 
                    new_picking_id.write({'shipping_id':self.picking_id.shipping_id.id,
                                          'carrier_id' : self.picking_id.carrier_id.id,
                                          'shipping_weight':self.picking_id.shipping_weight,
                                          'weight_of_cases':self.picking_id.weight_of_cases,
                                          'weight_total_kg':self.picking_id.weight_total_kg,
                                          'actual_weight':self.picking_id.actual_weight,
                                          'calulate_shipping_cost':self.picking_id.calulate_shipping_cost,
                                          'tracking_number_spt':self.picking_id.tracking_number_spt,
                                          'recipient_id':self.picking_id.recipient_id.id,
                                          'country_id':self.picking_id.country_id.id,
                                          'street':self.picking_id.street,
                                          'street_2':self.picking_id.street_2,
                                          'zip_code':self.picking_id.zip_code,
                                          'state_id':self.picking_id.state_id,
                                          'city':self.picking_id.city,
                                          'phone':self.picking_id.phone,
                                          'phone_ext':self.picking_id.phone_ext,
                                          'tax':self.picking_id.tax,
                                          'company_name':self.picking_id.company_name,
                                          'currecnt_sender_name':self.picking_id.currecnt_sender_name,
                                          'kits_street':self.picking_id.kits_street,
                                          'kits_street_1':self.picking_id.kits_street_1,
                                          'kits_country_id':self.picking_id.kits_country_id.id,
                                          'kits_state_id':self.picking_id.kits_state_id.id,
                                          'kits_zip_code':self.picking_id.kits_zip_code,
                                          'kits_city':self.picking_id.kits_city,
                                          'transportation_to':self.picking_id.transportation_to,
                                          'package_type_id':self.picking_id.package_type_id.id,
                                          'height':self.picking_id.height,
                                          'width':self.picking_id.width,
                                          'kits_length':self.picking_id.kits_length,
                                          'ship_date':self.picking_id.ship_date,
                                          'package_contain':self.picking_id.package_contain,
                                          'total_box':self.picking_id.total_box,
                                          'weight':self.picking_id.weight,
                                          'weight_unit':self.picking_id.weight_unit,
                                          'duties_taxes':self.picking_id.duties_taxes,
                                          'notes':self.picking_id.notes,
                                          'customer_ref':self.picking_id.customer_ref,
                                          'shipment':self.picking_id.shipment,
                                          'shipment_purpose':self.picking_id.shipment_purpose,
                                          'commercial_invoice':self.picking_id.commercial_invoice,
                                          'export_export':self.picking_id.export_export,
                                          'b13a':self.picking_id.b13a,
                                          'exemption':self.picking_id.exemption,
                                          'shipping_label':self.picking_id.shipping_label,
                                          'is_fedex':is_fedex,
                                          'is_ups':is_ups,
                                        })
                    if line_id:
                        line_id.quantity_done = cancel_picking_data.get(delivery_data).get('done')
                    else:
                        price_unit = self.sale_id.pricelist_id._get_product_price(product_id, cancel_picking_data.get(delivery_data).get('demand'), product_id.uom_id)
                        
                        if product_id.sale_type == 'on_sale' and self.sale_id and self.sale_id.pricelist_id and self.sale_id.pricelist_id.currency_id:
                            # if self.sale_id.pricelist_id.currency_id.name == 'CAD':
                            #     price_unit = product_id.on_sale_cad
                            # if self.sale_id.pricelist_id.currency_id.name == 'USD':
                            price_unit = product_id.on_sale_usd
                        
                        if product_id.sale_type == 'clearance' and self.sale_id and self.sale_id.pricelist_id and self.sale_id.pricelist_id.currency_id:
                            # if self.sale_id.pricelist_id.currency_id.name == 'CAD':
                            #     price_unit = product_id.clearance_cad
                            # if self.sale_id.pricelist_id.currency_id.name == 'USD':
                            price_unit = product_id.clearance_usd

                        product_uom_qty = 0.0
                        if cancel_picking_data.get(delivery_data).get('done') != 0.0 and cancel_picking_data.get(delivery_data).get('demand') != 0.0:
                            product_uom_qty = cancel_picking_data.get(delivery_data).get('done')
                        elif cancel_picking_data.get(delivery_data).get('done') == 0.0 and cancel_picking_data.get(delivery_data).get('demand') != 0.0:
                            product_uom_qty = cancel_picking_data.get(delivery_data).get('demand')
                        elif cancel_picking_data.get(delivery_data).get('demand') == 0.0 and cancel_picking_data.get(delivery_data).get('done') != 0.0:
                            product_uom_qty = cancel_picking_data.get(delivery_data).get('done')

                        new_picking_id.sale_id.write({
                            'order_line':[(0,0,{'product_id':product_id.id,
                                                'name':product_id.name,
                                                'product_uom_qty':product_uom_qty,
                                                'unit_discount_price':price_unit,
                                                'price_unit': price_unit,
                                                'picked_qty':cancel_picking_data.get(delivery_data).get('done')})]
                        })
                        new_picking_id.sale_id.order_line.move_ids.filtered(lambda x:x.state != 'cancel' and x.product_id.id == product_id.id).quantity_done = cancel_picking_data.get(delivery_data).get('done')
                
                new_picking_id.state = 'in_scanning'
                self.sale_id.state = 'in_scanning'
