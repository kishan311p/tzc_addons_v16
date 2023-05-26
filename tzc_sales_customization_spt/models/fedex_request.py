from odoo.addons.delivery_fedex.models.fedex_request import FedexRequest
import re

class Kits_Fedex(FedexRequest):
    def customs_value(self, customs_value_currency, customs_value_amount, document_content,picking):

        shipment_purpose = dict(picking._fields['shipment_purpose'].selection).get(picking.shipment_purpose).upper() if picking.shipment_purpose else None
        b13a_filling_option = picking.b13a or "MANUALLY_ATTACHED"
        compilation_statement = picking.exemption or None

        self.RequestedShipment.CustomsClearanceDetail = self.factory.CustomsClearanceDetail()
        self.RequestedShipment.CustomsClearanceDetail.CustomsValue   = self.factory.Money()
        self.RequestedShipment.CustomsClearanceDetail.CustomsValue.Currency = customs_value_currency
        self.RequestedShipment.CustomsClearanceDetail.CustomsValue.Amount = customs_value_amount
        # if self.RequestedShipment.Shipper.Address.CountryCode == "IN" and self.RequestedShipment.Recipient.Address.CountryCode == "IN":
        if not self.RequestedShipment.CustomsClearanceDetail.CommercialInvoice:
            self.RequestedShipment.CustomsClearanceDetail.CommercialInvoice = self.factory.CommercialInvoice()
        else:
            del self.RequestedShipment.CustomsClearanceDetail.CommercialInvoice.TaxesOrMiscellaneousChargeType
        
        if shipment_purpose:
            self.RequestedShipment.CustomsClearanceDetail.CommercialInvoice.Purpose = shipment_purpose
        else:
            self.RequestedShipment.CustomsClearanceDetail.CommercialInvoice.Purpose = 'SOLD'

        # Old keys not requested anymore but still in WSDL; not removing them causes crash
        del self.RequestedShipment.CustomsClearanceDetail['ClearanceBrokerage']
        del self.RequestedShipment.CustomsClearanceDetail['FreightOnValue']

        self.RequestedShipment.CustomsClearanceDetail.DocumentContent = document_content

        # Add Export Details
        if not self.RequestedShipment.CustomsClearanceDetail.ExportDetail:
            ExportDetail = self.factory.ExportDetail()
            amount = self.RequestedShipment.CustomsClearanceDetail.CustomsValue.Amount
            currency = self.RequestedShipment.CustomsClearanceDetail.CustomsValue.Currency

            if currency == 'CAD':
                ExportDetail.B13AFilingOption = 'NOT_REQUIRED' if amount < 2000.00 else "MANUALLY_ATTACHED"
            else:
                cad_amount = round(amount * 1.3 , 2)
                ExportDetail.B13AFilingOption = 'NOT_REQUIRED' if cad_amount < 2000.00 else "MANUALLY_ATTACHED"

            ExportDetail.ExportComplianceStatement = compilation_statement
            ExportDetail.PermitNumber = self.ClientDetail.AccountNumber
            self.RequestedShipment.CustomsClearanceDetail.ExportDetail = ExportDetail

    def shipping_charges_payment(self, shipping_charges_payment_account,picking):
        self.RequestedShipment.ShippingChargesPayment = self.factory.Payment()
        if picking.transportation_to:
            payment_type = dict(picking._fields['transportation_to'].selection).get(picking.transportation_to).upper()
            self.RequestedShipment.ShippingChargesPayment.PaymentType = payment_type
        else:
            self.RequestedShipment.ShippingChargesPayment.PaymentType = 'SENDER'
        Payor = self.factory.Payor()
        Payor.ResponsibleParty = self.factory.Party()
        Payor.ResponsibleParty.AccountNumber = shipping_charges_payment_account
        self.RequestedShipment.ShippingChargesPayment.Payor = Payor

    def commercial_invoice(self, document_stock_type, send_etd=False,shipment_doc_type=None):
        shipping_document = self.factory.ShippingDocumentSpecification()
        doc_type = shipment_doc_type if shipment_doc_type else "COMMERCIAL_INVOICE"
        shipping_document.ShippingDocumentTypes = shipment_doc_type

        commercial_invoice_detail = self.factory.CommercialInvoiceDetail()
        commercial_invoice_detail.Format = self.factory.ShippingDocumentFormat()
        commercial_invoice_detail.Format.ImageType = "PDF"
        commercial_invoice_detail.Format.StockType = document_stock_type
        shipping_document.CommercialInvoiceDetail = commercial_invoice_detail
        self.RequestedShipment.ShippingDocumentSpecification = shipping_document
        if send_etd:
            self.RequestedShipment.SpecialServicesRequested.SpecialServiceTypes.append('ELECTRONIC_TRADE_DOCUMENTS')
            etd_details = self.factory.EtdDetail()
            etd_details.RequestedDocumentCopies.append(doc_type)
            # etd_details.RequestedDocumentCopies.append('COMMERCIAL_INVOICE')
            self.RequestedShipment.SpecialServicesRequested.EtdDetail = etd_details
    
    def _add_package(self, weight_value, package_code=False, package_height=0, package_width=0, package_length=0, sequence_number=False, mode='shipping', po_number=False, dept_number=False, reference=False, insured_value=False, currency=False):
        package = self.factory.RequestedPackageLineItem()
        package_weight = self.factory.Weight()
        package_weight.Value = weight_value
        package_weight.Units = self.RequestedShipment.TotalWeight.Units

        package.PhysicalPackaging = 'BOX'
        if package_code == 'YOUR_PACKAGING':
            package.Dimensions = self.factory.Dimensions()
            package.Dimensions.Height = package_height
            package.Dimensions.Width = package_width
            package.Dimensions.Length = package_length
            # TODO in master, add unit in product packaging and perform unit conversion
            package.Dimensions.Units = "CM"
        if po_number:
            po_reference = self.factory.CustomerReference()
            po_reference.CustomerReferenceType = 'P_O_NUMBER'
            po_reference.Value = po_number
            package.CustomerReferences.append(po_reference)
        if dept_number:
            dept_reference = self.factory.CustomerReference()
            dept_reference.CustomerReferenceType = 'DEPARTMENT_NUMBER'
            dept_reference.Value = dept_number
            package.CustomerReferences.append(dept_reference)
        if reference:
            customer_reference = self.factory.CustomerReference()
            customer_reference.CustomerReferenceType = 'CUSTOMER_REFERENCE'
            customer_reference.Value = reference
            package.CustomerReferences.append(customer_reference)
        if insured_value and currency:
            package.InsuredValue = self.factory.Money()
            package.InsuredValue.Currency = currency
            package.InsuredValue.Amount = insured_value

        package.Weight = package_weight
        if mode == 'rating':
            package.GroupPackageCount = 1
        if sequence_number:
            package.SequenceNumber = sequence_number
        else:
            self.hasOnePackage = True

        if mode == 'rating':
            self.RequestedShipment.RequestedPackageLineItems.append(package)
        else:
            self.RequestedShipment.RequestedPackageLineItems = package
    
    def commodities(self, commodity_currency,commodities):
        self.hasCommodities = True
        commodity = self.factory.Commodity()
        commodity.UnitPrice = self.factory.Money()
        commodity.Description = re.sub(r'[\[\]<>;={}"|]', '', commodities['Description'])
        commodity.Quantity = commodities['Quantity']
        commodity.QuantityUnits = commodities['QuantityUnits']
        customs_value = self.factory.Money()
        customs_value.Currency = commodity_currency
        customs_value.Amount = commodities['Amount']
        commodity.CustomsValue = customs_value
        commodity.CountryOfManufacture = 'CN'

        self.listCommodities.append(commodity)
    
    def ship_commodities(self, commodity_currency, commodity_amount, commodity_number_of_piece, commodity_weight_units,
                commodity_weight_value, commodity_description, commodity_country_of_manufacture, commodity_quantity,
                commodity_quantity_units, commodity_harmonized_code):
        self.hasCommodities = True
        commodity = self.factory.Commodity()
        commodity.UnitPrice = self.factory.Money()
        commodity.UnitPrice.Currency = commodity_currency
        commodity.UnitPrice.Amount = commodity_amount
        commodity.NumberOfPieces = commodity_number_of_piece
        commodity.CountryOfManufacture = commodity_country_of_manufacture

        commodity_weight = self.factory.Weight()
        commodity_weight.Value = commodity_weight_value
        commodity_weight.Units = commodity_weight_units

        commodity.Weight = commodity_weight
        commodity.Description = re.sub(r'[\[\]<>;={}"|]', '', commodity_description)
        commodity.Quantity = commodity_quantity
        commodity.QuantityUnits = commodity_quantity_units
        customs_value = self.factory.Money()
        customs_value.Currency = commodity_currency
        customs_value.Amount = commodity_quantity * commodity_amount
        commodity.CustomsValue = customs_value

        commodity.HarmonizedCode = commodity_harmonized_code

        self.listCommodities.append(commodity)

FedexRequest.customs_value = Kits_Fedex.customs_value
FedexRequest.shipping_charges_payment = Kits_Fedex.shipping_charges_payment
FedexRequest.commercial_invoice = Kits_Fedex.commercial_invoice
FedexRequest._add_package = Kits_Fedex._add_package
FedexRequest.commodities = Kits_Fedex.commodities
FedexRequest.ship_commodities = Kits_Fedex.ship_commodities
