from odoo import api, fields, models, _
from odoo.exceptions import UserError

class kits_multi_website_refund_option(models.TransientModel):
    _name = "kits.multi.website.refund.option"
    _description = "Kits Multi Website Refund Option"

    return_request_id = fields.Many2one("kits.multi.website.return.request","Return Request")
    refund_option = fields.Selection([('wallet','Wallet'), ('bank','Bank Account')])
    amount = fields.Float(" Amount ")

    def action_process_refund(self):
        for record in self:
            if record.amount > self._context.get('default_amount',0):
                raise UserError(f"Amount should be less than ordered total as you can refund upto {record.return_request_id.sale_order_id.currency_id.symbol if record.return_request_id.sale_order_id.currency_id else ''}{round(self._context.get('default_amount',0),2)}")

            record.return_request_id.write({
                'state' : 'refund'
                })
            record.return_request_id.return_request_line_ids.write({
                'refunded_date': fields.datetime.now(),
                'is_refund': True
            })
            record.return_request_id.return_request_line_ids.mapped('sale_order_line_id').write({
                'return_refunded_date': fields.datetime.now(),
            })
        
            if record.refund_option == "wallet":
                wallet_transaction_vals = {
                    'return_request_id' : record.return_request_id.id, 
                    'sale_order_id' : record.return_request_id.sale_order_id.id, 
                    'amount': record.amount,
                    'customer_id': record.return_request_id.customer_id.id,
                    'refund_date': fields.datetime.now(),
                    'description' : self._context.get('default_description')
                }
                self.env['kits.multi.website.wallet.transaction'].create(wallet_transaction_vals) 

            product_list = []
            for line in record.return_request_id.return_request_line_ids:
                product_list.append((0,0,{
                    'product_id': line.sale_order_line_id.product_id.id,
                    'unit_price': line.sale_order_line_id.unit_price,
                    'quantity': line.quantity,
                    'power_type_id': line.sale_order_line_id.power_type_id.id,
                    'glass_type_id': line.sale_order_line_id.glass_type_id.id,
                    'glass_price': line.sale_order_line_id.glass_price,
                    'left_eye_power': line.sale_order_line_id.left_eye_power,
                    'right_eye_power': line.sale_order_line_id.right_eye_power,
                    'discount': line.sale_order_line_id.discount,
                    'tax_ids': [(6,0,line.sale_order_line_id.tax_ids.ids)],
                    'tax_amount': line.sale_order_line_id.tax_amount,
                    'discount_amount': line.sale_order_line_id.discount_amount,
                }))
            return record.return_request_id.sale_order_id.with_context(invoice_type="refund",refund_amount=record.amount,product_list=product_list).action_create_invoice()
