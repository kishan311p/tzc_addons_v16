from odoo import api, fields, models, _

class kits_multi_website_coupon_customer_line(models.Model):
    _name = "kits.multi.website.coupon.customer.line"
    _description = "Kits Multi Website Coupon Customer Line"

    customer_id = fields.Many2one("kits.multi.website.customer", "Customer")
    coupon_used_count = fields.Integer("Coupon Used Count")
    coupon_id = fields.Many2one("kits.multi.website.coupon", "Coupon")
