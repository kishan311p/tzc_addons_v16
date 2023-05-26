from odoo import _, api, fields, models, tools
import logging
from odoo.exceptions import UserError
from odoo.addons.delivery_fedex.models.fedex_request import FedexRequest
from odoo.tools import pdf
from zeep.helpers import serialize_object
import base64
from base64 import b64decode

_logger = logging.getLogger(__name__)


FEDEX_CURR_MATCH = {
    u'UYU': u'UYP',
    u'XCD': u'ECD',
    u'MXN': u'NMP',
    u'KYD': u'CID',
    u'CHF': u'SFR',
    u'GBP': u'UKL',
    u'IDR': u'RPA',
    u'DOP': u'RDD',
    u'JPY': u'JYE',
    u'KRW': u'WON',
    u'SGD': u'SID',
    u'CLP': u'CHP',
    u'JMD': u'JAD',
    u'KWD': u'KUD',
    u'AED': u'DHS',
    u'TWD': u'NTD',
    u'ARS': u'ARN',
    u'LVL': u'EURO',
}


class delivery_carrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_product_id = fields.Many2one('product.product','Delivery Product ')
    is_default = fields.Boolean()
    is_published = fields.Boolean()
    is_freight = fields.Boolean()

    def write(self,vals):
        res = super(delivery_carrier,self).write(vals)
        if vals.get('integration_level'):
            vals['integration_level'] = 'rate'
        return res

    @api.model
    def create(self,vals):
        res = super(delivery_carrier,self).create(vals)
        if vals.get('integration_level'):
            vals['integration_level'] = 'rate'
        return res

    def fedex_send_shipping(self, pickings):
        res = []
        category_dict = {
            'E' : "Eyeglasses",
            'S' : "Sunglasses",
            'Case' : "Cases"
        }
        for picking in pickings:
            total_pkg_qty = sum(picking.delivery_package_line_ids.mapped('qty'))
            avg_price = 0
            if total_pkg_qty:
                avg_price = picking.sale_id.picked_qty_order_total / total_pkg_qty
            for package in picking.delivery_package_line_ids:

                srm = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
                superself = self.sudo()
                srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
                srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

                srm.transaction_detail(picking.id)

                # For custom packaging we are setting package type to YOUR_PACKAGING. Mentioned in fedex api documentation
                package_type = "YOUR_PACKAGING"
                srm.shipment_request(picking.carrier_id.fedex_droppoff_type, picking.carrier_id.fedex_service_type, package_type, picking.carrier_id.fedex_weight_unit, picking.carrier_id.fedex_saturday_delivery)
                srm.set_currency(_convert_curr_iso_fdx(picking.company_id.currency_id.name))
                srm.set_shipper(picking.company_id.partner_id, picking.picking_type_id.warehouse_id.partner_id)
                srm.set_recipient(picking.recipient_id)

                # srm.shipping_charges_payment(superself.fedex_account_number)
                srm.shipping_charges_payment(superself.fedex_account_number,picking)

                srm.shipment_label('COMMON2D', self.fedex_label_file_type, self.fedex_label_stock_type, 'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')

                order = picking.sale_id
                company = order.company_id or picking.company_id or self.env.company
                order_currency = picking.sale_id.b2b_currency_id or picking.company_id.currency_id
                # order_currency = picking.sale_id.currency_id or picking.company_id.currency_id

                net_weight = self._fedex_convert_weight(package.weight, dict(picking._fields['weight_unit'].selection).get(picking.weight_unit))

                if 'INTERNATIONAL' in self.fedex_service_type   or (picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN'):
                    commodity_currency = order_currency
                    total_commodities_amount = 0.0
                    commodity_country_of_manufacture = picking.picking_type_id.warehouse_id.partner_id.country_id.code
                    shipment_doc_type = picking.commercial_invoice
                    avg_qty = 0
                    avg_weight = 0
                    if len(package.commodity_ids):
                        avg_qty = package.qty / len(package.commodity_ids) 
                        avg_weight = package.weight / len(package.commodity_ids)
                    for commodity in package.commodity_ids:
                        commodity_amount = avg_price
                        total_commodities_amount += commodity_amount * avg_qty
                        commodity_description = category_dict.get(commodity.name)
                        commodity_number_of_piece = '1'
                        commodity_weight_units = self.fedex_weight_unit
                        commodity_weight_value = self._fedex_convert_weight(avg_weight, self.fedex_weight_unit)
                        commodity_quantity = avg_qty
                        commodity_quantity_units = 'EA'
                        commodity_harmonized_code =  ''
                        srm.ship_commodities(_convert_curr_iso_fdx(commodity_currency.name), commodity_amount, commodity_number_of_piece, commodity_weight_units, commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity, commodity_quantity_units, commodity_harmonized_code)
                    srm.customs_value(_convert_curr_iso_fdx(commodity_currency.name), total_commodities_amount, "NON_DOCUMENTS",picking)
                    fedex_duty_payment = dict(picking._fields['transportation_to'].selection).get(picking.transportation_to).upper()
                    srm.duties_payment(picking.picking_type_id.warehouse_id.partner_id, superself.fedex_account_number, fedex_duty_payment)
                    send_etd = superself.env['ir.config_parameter'].get_param("delivery_fedex.send_etd")
                    srm.commercial_invoice(self.fedex_document_stock_type, send_etd,shipment_doc_type)
                    srm.RequestedShipment.CustomsClearanceDetail.Commodities = srm.listCommodities

                # Custom as we are iterating through packages so we get only one package at a time.
                package_count = 1

                # For india picking courier is not accepted without this details in label.
                po_number = order.display_name or False
                dept_number = False
                if picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN':
                    po_number = 'B2B' if picking.partner_id.commercial_partner_id.is_company else 'B2C'
                    dept_number = 'BILL D/T: SENDER'

                # TODO RIM master: factorize the following crap

                ################
                # Multipackage #
                ################
                if package_count > 1:

                    # Note: Fedex has a complex multi-piece shipping interface
                    # - Each package has to be sent in a separate request
                    # - First package is called "master" package and holds shipping-
                    #   related information, including addresses, customs...
                    # - Last package responses contains shipping price and code
                    # - If a problem happens with a package, every previous package
                    #   of the shipping has to be cancelled separately
                    # (Why doing it in a simple way when the complex way exists??)

                    master_tracking_id = False
                    package_labels = []
                    carrier_tracking_ref = ""

                    for sequence in range(1,int(package_count) + 1):


                        package_weight = self._fedex_convert_weight(picking.weight, dict(picking._fields['weight_unit'].selection).get(picking.weight_unit))
                        
                        packaging = picking.package_type_id  # Add "FEDEX_YOUR_PACKAGE" from shipping detail
                        srm._add_package(
                            package_weight,
                            package_code=packaging.shipper_package_code, # Add "YOUR_PACKAGE" from shipping detail
                            package_height=picking.height,
                            package_width=picking.width,
                            package_length=picking.kits_length,
                            sequence_number=sequence,
                            po_number=po_number,
                            dept_number=dept_number,
                            reference=picking.display_name, 
                            insured_value=picking.carriage_value,
                            currency=picking.currency_id.name,
                        )
                        srm.set_master_package(net_weight, package_count, master_tracking_id=master_tracking_id)
                        request = srm.process_shipment()
                        package_name = str(sequence)

                        warnings = request.get('warnings_message')
                        if warnings:
                            _logger.info(warnings)

                        # First package
                        if sequence == 1:
                            if not request.get('errors_message'):
                                master_tracking_id = request['master_tracking_id']
                                package_labels.append((package_name, srm.get_label()))
                                carrier_tracking_ref = request['tracking_number']
                            else:
                                raise UserError(request['errors_message'])

                        # Intermediary packages
                        elif sequence > 1 and sequence < package_count:
                            if not request.get('errors_message'):
                                package_labels.append((package_name, srm.get_label()))
                                carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']
                            else:
                                raise UserError(request['errors_message'])

                        # Last package
                        elif sequence == package_count:
                            # recuperer le label pdf
                            if not request.get('errors_message'):
                                package_labels.append((package_name, srm.get_label()))
                                # package_labels.append((package_name, srm.get_label()))

                                carrier_price = self._get_request_price(request['price'], order, order_currency)

                                carrier_tracking_ref = carrier_tracking_ref + "," + request['tracking_number']

                                logmessage = _("Shipment created into Fedex<br/>"
                                            "<b>Tracking Numbers:</b> %s<br/>"
                                            "<b>Packages:</b> %s") % (carrier_tracking_ref, ','.join([pl[0] for pl in package_labels]))
                                if self.fedex_label_file_type != 'PDF':
                                    attachments = [('LabelFedex-%s.%s' % (pl[0], self.fedex_label_file_type), pl[1]) for pl in package_labels]
                                if self.fedex_label_file_type == 'PDF':
                                    attachments = [('LabelFedex.pdf', pdf.merge_pdf([pl[1] for pl in package_labels]))]
                                picking.message_post(body=logmessage, attachments=attachments)
                                shipping_data = {'exact_price': carrier_price,
                                                'tracking_number': carrier_tracking_ref}
                                res = res + [shipping_data]
                            else:
                                raise UserError(request['errors_message'])

                # TODO RIM handle if a package is not accepted (others should be deleted)

                ###############
                # One package #
                ###############
                elif package_count == 1:

                    srm._add_package(
                        # str(package.weight),
                        net_weight,
                        package_code='YOUR_PACKAGING',
                        package_height=int(package.height),
                        package_width=int(package.width),
                        package_length=int(package.length),
                        po_number=po_number,
                        dept_number=dept_number,
                        reference=picking.display_name,
                    )
                    srm.set_master_package(net_weight, 1)

                    # Appending commodities to customclearance
                    # Ask the shipping to fedex
                    request = serialize_object(dict(WebAuthenticationDetail=srm.WebAuthenticationDetail,
                                    ClientDetail=srm.ClientDetail,
                                    TransactionDetail=srm.TransactionDetail,
                                    VersionId=srm.VersionId,
                                    RequestedShipment=srm.RequestedShipment))
                    self._fedex_add_extra_data_to_request(request, 'ship')
                    request = srm.process_shipment(request)

                    warnings = request.get('warnings_message')
                    if warnings:
                        _logger.info(warnings)

                    if not request.get('errors_message'):

                        if _convert_curr_iso_fdx(order_currency.name) in request['price']:
                            carrier_price = request['price'][_convert_curr_iso_fdx(order_currency.name)]
                        else:
                            _logger.info("Preferred currency has not been found in FedEx response")
                            company_currency = picking.company_id.currency_id
                            if _convert_curr_iso_fdx(company_currency.name) in request['price']:
                                amount = request['price'][_convert_curr_iso_fdx(company_currency.name)]
                                carrier_price = company_currency._convert(
                                    amount, order_currency, company, order.date_order or fields.Date.today())
                            else:
                                amount = request['price']['USD']
                                carrier_price = company_currency._convert(
                                    amount, order_currency, company, order.date_order or fields.Date.today())

                        carrier_tracking_ref = request['tracking_number']
                        logmessage = (_("Shipment created into Fedex <br/> <b>Tracking Number : </b>%s") % (carrier_tracking_ref))

                        fedex_labels = [('LabelFedex-%s-%s.%s' % (carrier_tracking_ref, index, self.fedex_label_file_type), label)
                                        for index, label in enumerate(srm._get_labels(self.fedex_label_file_type))]
                        picking.message_post(body=logmessage, attachments=fedex_labels)
                        shipping_data = {'exact_price': carrier_price,
                                        'tracking_number': carrier_tracking_ref,
                                        'fedex_label':fedex_labels[0],}
                        package.tracking_number = carrier_tracking_ref
                        label=fedex_labels[0][1]
                        base64_data = base64.b64encode(label)
                        byte_data = b64decode(base64_data,validate=True)
                        if byte_data[0:4] != b'%PDF':
                            raise ValueError('Missing the PDF file signature')
                        else:
                            package.file_name = "LabelFedex-" + carrier_tracking_ref
                            package.package_label = base64.b64encode(byte_data)
                        res = res + [shipping_data]
                    else:
                        raise UserError(request['errors_message'])

                ##############
                # No package #
                ##############
                else:
                    raise UserError(_('No packages for this picking'))
                if self.return_label_on_delivery:
                    self.get_return_label(picking, tracking_number=request['tracking_number'], origin_date=request['date'])
                commercial_invoice = srm.get_document()
                if commercial_invoice:
                    fedex_documents = [('DocumentFedex.pdf', commercial_invoice)]
                    picking.message_post(body='Fedex Documents', attachments=fedex_documents)
        return res

    
    # def shipping_charges_payment(self, shipping_charges_payment_account,picking):
    #     self.RequestedShipment.ShippingChargesPayment = self.factory.Payment()
    #     if picking.transportation_to:
    #         payment_type = dict(picking._fields['transportation_to'].selection).get(picking.transportation_to).upper()
    #         self.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type
    #     else:
    #         self.RequestedShipment.ShippingChargesPayment.PaymentType = 'SENDER'
    #     Payor = self.factory.Payor()
    #     Payor.ResponsibleParty = self.factory.Party()
    #     Payor.ResponsibleParty.AccountNumber = shipping_charges_payment_account
    #     self.RequestedShipment.ShippingChargesPayment.Payor = Payor


    def fedex_get_return_label(self, picking, tracking_number=None, origin_date=None):
        srm = FedexRequest(self.log_xml, request_type="shipping", prod_environment=self.prod_environment)
        superself = self.sudo()
        srm.web_authentication_detail(superself.fedex_developer_key, superself.fedex_developer_password)
        srm.client_detail(superself.fedex_account_number, superself.fedex_meter_number)

        srm.transaction_detail(picking.id)

        package_type = picking.package_ids and picking.package_ids[0].package_type_id.shipper_package_code or self.fedex_default_package_type_id.shipper_package_code
        srm.shipment_request(self.fedex_droppoff_type, self.fedex_service_type, package_type, self.fedex_weight_unit, self.fedex_saturday_delivery)
        srm.set_currency(_convert_curr_iso_fdx(picking.company_id.currency_id.name))
        srm.set_shipper(picking.partner_id, picking.partner_id)
        srm.set_recipient(picking.company_id.partner_id)

        srm.shipping_charges_payment(superself.fedex_account_number,picking)

        srm.shipment_label('COMMON2D', self.fedex_label_file_type, self.fedex_label_stock_type, 'TOP_EDGE_OF_TEXT_FIRST', 'SHIPPING_LABEL_FIRST')
        if picking.is_return_picking:
            net_weight = self._fedex_convert_weight(picking._get_estimated_weight(), self.fedex_weight_unit)
        else:
            net_weight = self._fedex_convert_weight(picking.shipping_weight, self.fedex_weight_unit)
        package_type = picking.package_ids[:1].package_type_id or picking.carrier_id.fedex_default_package_type_id
        order = picking.sale_id
        po_number = order.display_name or False
        dept_number = False
        packages = self._get_packages_from_picking(picking, self.fedex_default_package_type_id)
        for pkg in packages:
            srm.add_package(self, pkg, _convert_curr_iso_fdx(pkg.company_id.currency_id.name), reference=picking.display_name, po_number=po_number, dept_number=dept_number)
        srm.set_master_package(net_weight, 1)
        if 'INTERNATIONAL' in self.fedex_service_type  or (picking.partner_id.country_id.code == 'IN' and picking.picking_type_id.warehouse_id.partner_id.country_id.code == 'IN'):

            order_currency = picking.sale_id.currency_id or picking.company_id.currency_id

            for commodity in packages.commodities:
                srm.commodities(self, commodity, _convert_curr_iso_fdx(order_currency.name))

            total_commodities_amount = sum(c.monetary_value * c.qty for c in packages.commodities)
            srm.customs_value(_convert_curr_iso_fdx(order_currency.name), total_commodities_amount, "NON_DOCUMENTS")
            srm.duties_payment(order.warehouse_id.partner_id, superself.fedex_account_number, superself.fedex_duty_payment)

            srm.customs_value(_convert_curr_iso_fdx(order_currency.name), total_commodities_amount, "NON_DOCUMENTS")
            # We consider that returns are always paid by the company creating the label
            srm.duties_payment(picking.picking_type_id.warehouse_id.partner_id, superself.fedex_account_number, 'SENDER')
        srm.return_label(tracking_number, origin_date)

        # Prepare the request
        self._fedex_update_srm(srm, 'return', picking=picking)
        request = serialize_object(dict(WebAuthenticationDetail=srm.WebAuthenticationDetail,
                                        ClientDetail=srm.ClientDetail,
                                        TransactionDetail=srm.TransactionDetail,
                                        VersionId=srm.VersionId,
                                        RequestedShipment=srm.RequestedShipment))
        self._fedex_add_extra_data_to_request(request, 'return')
        response = srm.process_shipment(request)
        if not response.get('errors_message'):
            fedex_labels = [('%s-%s-%s.%s' % (self.get_return_label_prefix(), response['tracking_number'], index, self.fedex_label_file_type), label)
                            for index, label in enumerate(srm._get_labels(self.fedex_label_file_type))]
            picking.message_post(body='Return Label', attachments=fedex_labels)
        else:
            raise UserError(response['errors_message'])



def _convert_curr_iso_fdx(code):
    return FEDEX_CURR_MATCH.get(code, code)
