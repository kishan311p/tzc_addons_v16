from odoo import api, fields, models, _
from lxml import etree

class kits_multi_website_invoice(models.Model):
    _name = "kits.multi.website.invoice"
    _description = "Kits Multi Website Invoice"

    name = fields.Char("Name")
    customer_id = fields.Many2one("kits.multi.website.customer", "Customer")
    invoice_date = fields.Date("Invoice Date")
    invoice_line_ids = fields.One2many("kits.multi.website.invoice.line","invoice_id","Invoice Lines")
    total = fields.Float("Total",compute="_compute_total")
    state = fields.Selection([('draft','Draft'), ('paid','Paid'), ('cancel','Cancel')], default="draft", string="State")
    sale_order_id = fields.Many2one("kits.multi.website.sale.order", "Sale Order")
    amount_without_discount = fields.Float("Subtotal",compute="_compute_all")
    amount_discount = fields.Float("Discount",compute="_compute_all")
    amount_tax = fields.Float("Tax",compute="_compute_all")
    fiscal_position_id = fields.Many2one("account.fiscal.position", "Fiscal Position")
    promo_code_discount = fields.Float("Promo Code Discount")
    discounted_shipping_cost = fields.Float("Discounted Shipping Cost")
    currency_id = fields.Many2one("res.currency", "Currency",related="customer_id.currency_id")
    amount_paid = fields.Float(" Amount ")
    journal_id = fields.Many2one("account.journal",domain=[('type','in',['bank', 'cash'])])
    payment_date = fields.Date("Payment Date")
    shipping_discount = fields.Float("Shipping Discount")
    website_id = fields.Many2one("kits.b2c.website", "Website")
    invoice_type = fields.Selection([('invoice','Invoice'), ('refund','Refund Invoice')])
    refund_amount = fields.Float("Refund Amount")
    refund_amount_deducted = fields.Float("Refund Deduction")


    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_invoice, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res

    @api.onchange('currency_id')
    def _set_currency_to_invoice_lines(self):
        for record in self:
            if record.invoice_line_ids:
                record.invoice_line_ids.write({
                    'currency_id': record.currency_id.id,
                })
                record.invoice_line_ids._convert_rates()


    @api.onchange('invoice_line_ids')
    def _onchange_invoice_line(self):
        for record in self:
            record.invoice_line_ids.currency_id = record.currency_id

    @api.model
    def create(self, vals):
        res = super(kits_multi_website_invoice, self).create(vals)
        if 'refund_amount' in self.env.context and self.env.context.get('refund_amount'):
            res.write({
                'refund_amount_deducted': -abs(res.total - self.env.context.get('refund_amount')),
                'refund_amount': self.env.context.get('refund_amount'),
            })
            res.name = self.env['ir.sequence'].next_by_code('unique.multi.website.refund.invoice.sequence')
        else:
            res.name = self.env['ir.sequence'].next_by_code('unique.multi.website.invoice.sequence')
        if not res.invoice_date:
            res.invoice_date = fields.date.today()
        return res

    @api.depends('invoice_line_ids.subtotal','discounted_shipping_cost')
    def _compute_total(self):
        for record in self:
            record.total = 0
            if record.invoice_line_ids:
                record.total = sum(record.invoice_line_ids.mapped('subtotal')) + record.discounted_shipping_cost if record.discounted_shipping_cost else sum(record.invoice_line_ids.mapped('subtotal'))

    def action_open_order(self):
        form_view_id = self.env.ref("kits_multi_website.kits_multi_website_sale_order_form_view")
        return{
            'name': ('Invoices'),
            'res_model': 'kits.multi.website.sale.order',
            'type': 'ir.actions.act_window',
            'views': [(form_view_id.id, 'form')],
            'res_id': self.sale_order_id.id,
            'target': 'current',
        }

    def action_register_payment(self):
        form_view_id = self.env.ref('kits_multi_website.kits_multi_website_register_payment_wiz_form_view')
        return{
            'name': ('Register Payment'),
            'res_model': 'kits.multi.website.register.payment.wiz',
            'type': 'ir.actions.act_window',
            'views': [(form_view_id.id, 'form')],
            'context': {'default_amount':self.refund_amount if self.refund_amount != 0 else self.total, 'default_invoice_id': self.id},
            'target': 'new',
        }

    def action_cancel(self):
        for record in self:
            record.write({
                'state': 'cancel',
                'amount_paid': False,
                'journal_id': False,
                'payment_date': False,
            })
        
    def action_reset_to_draft(self):
        for record in self:
            record.write({
                "state": 'draft',
            })

    @api.depends('invoice_line_ids.discount_amount','invoice_line_ids.tax_amount', 'promo_code_discount')
    def _compute_all(self):
        for record in self:
            record.amount_discount = False
            record.amount_tax = False
            record.amount_without_discount = False
            if record.invoice_line_ids:
                record.amount_discount = sum(record.invoice_line_ids.mapped('discount_amount'))
                record.amount_tax = sum(record.invoice_line_ids.mapped('tax_amount'))
                record.amount_without_discount = sum(record.invoice_line_ids.mapped("subtotal")) + record.amount_discount - record.amount_tax 
            record.amount_discount += record.promo_code_discount + record.shipping_discount if record.shipping_discount else record.promo_code_discount  
            record.total -= record.promo_code_discount
    
    
    @api.onchange('customer_id')
    def _onchange_customer(self):
        for record in self:
            record.invoice_line_ids._compute_subtotal()
            record._compute_all()
            fpos_id = self.env['account.fiscal.position']._get_fpos_by_region(country_id=record.customer_id.country_id.id, state_id=record.customer_id.state_id.id, zipcode=False, vat_required=False)
            if fpos_id:
                record.fiscal_position_id = fpos_id
