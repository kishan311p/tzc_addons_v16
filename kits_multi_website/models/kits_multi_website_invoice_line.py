from odoo import api, fields, models, _

class kits_multi_website_invoice_line(models.Model):
    _name = 'kits.multi.website.invoice.line'
    _description = "Kits Multi Website Invoice Line"

    product_id = fields.Many2one("product.product", "Product")
    quantity = fields.Float("Quantity",default=1)
    unit_price = fields.Float("Unit Price")
    subtotal = fields.Float("Subtotal",compute="_compute_subtotal")
    power_type_id = fields.Many2one('kits.multi.website.power.type',string="Power Type",domain="[('website_id','=',website_id)]")
    glass_type_id = fields.Many2one("kits.multi.website.glass.type","Glass Type")
    glass_price = fields.Float("Glass Price")
    left_eye_power = fields.Float("Left Eye Power")
    right_eye_power = fields.Float("Right Eye Power")
    discount = fields.Integer("Discount(%)")
    tax_ids = fields.Many2many("account.tax","multi_website_invoice_account_tax_rel","invoice_id","account_tax_id","Taxes")
    discount_amount = fields.Float("Discount Amount")
    tax_amount = fields.Float("Tax Amount")
    invoice_id = fields.Many2one("kits.multi.website.invoice", "Invoice")
    currency_id = fields.Many2one("res.currency", "Currency")
    website_id = fields.Many2one("kits.b2c.website", "Website",related='invoice_id.website_id',store=True)
    is_power_glass = fields.Boolean('Is Power Glass',related='power_type_id.is_power_glass',store=True)

    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_invoice_line, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res
        
    @api.depends('unit_price','quantity','glass_type_id','glass_price','discount','tax_ids')
    def _compute_subtotal(self):
        for record in self:
            record.subtotal = 0
            record.discount_amount = 0
            record.tax_amount = 0
            if record.unit_price or record.quantity or record.glass_type_id:
                record.subtotal = (record.unit_price + record.glass_price) * record.quantity 
            if record.tax_ids:
                fpos_id = self.env['account.fiscal.position']._get_fpos_by_region(country_id=record.invoice_id.customer_id.country_id.id, state_id=record.invoice_id.customer_id.state_id.id, zipcode=False, vat_required=False)
                if fpos_id:
                    fpos_tax = fpos_id.map_tax(record.tax_ids)
                    tax = fpos_tax.compute_all(record.unit_price + record.glass_price, quantity=record.quantity, currency=False, product=False, partner=False)
                    if 'total_included' in tax.keys() and tax.get('total_included'):    
                        record.tax_amount = tax.get('total_included') - record.subtotal
                        record.subtotal = tax.get('total_included')
            if record.discount: 
                discount = (record.discount / 100) * record.subtotal
                record.discount_amount = discount
                record.subtotal -= discount

    @api.onchange('product_id','glass_type_id')
    def _get_product_price(self):
        for record in self:
            record._convert_rates()
            # record.unit_price = record.product_id.list_price
            # record.glass_price = record.glass_type_id.price

    @api.onchange('power_type_id')
    def _onchange_power_type_id(self):
        for record in self:
            glass_type_ids = self.env['kits.multi.website.glass.type'].search([])
            if record.power_type_id:
                glass_type_ids = self.env['kits.multi.website.glass.type'].search([('power_type_id','=',record.power_type_id.id)])
            return{'domain': {'glass_type_id': [('id','in',glass_type_ids.ids)]}}

    def _convert_rates(self):
        for record in self:
            currency_mapping_id = self.env['kits.currency.mapping'].search([('currency_id','=',record.invoice_id.currency_id.id)])
            if currency_mapping_id:
                to_currency = currency_mapping_id.currency_id
                record.unit_price = currency_mapping_id._convert_rates(record.product_id.list_price, to_currency)
                record.glass_price = currency_mapping_id._convert_rates(record.glass_type_id.price, to_currency)
