from odoo import fields, models, api, _

class kits_b2b_product_wishlist(models.Model):
    _name = 'kits.b2b.product.wishlist'
    _description = "Wishlist"
    _order = "write_date desc"
    
    product_id = fields.Many2one('product.product', string='Product')
    partner_id = fields.Many2one('res.partner', string='Customer')
    website_id = fields.Many2one('kits.b2b.website','Website')


    def name_get(self):
        result = []
        for record in self:
            name = []
            if record.product_id:
                name.append(record.product_id.variant_name)
            if record.partner_id:
                name.append(record.partner_id.display_name)
            result.append((record.id,', '.join(name)))
        return result