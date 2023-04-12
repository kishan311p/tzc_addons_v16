from odoo import fields, models, api, _


class res_partner(models.Model):
    _inherit = 'res.partner'

    # b2b_pricelist_id = fields.Many2one(comodel_name='product.pricelist',string="Pricelist")
    preferred_currency= fields.Many2one(comodel_name='res.currency',string="Preferred Currency" ,index=True)
    b2b_wishlist_count = fields.Integer('Wishlist Count',compute='_compute_b2b_wishlist_count')
    b2b_recent_view_count = fields.Integer('Recent View Count',compute='_compute_b2b_wishlist_count')    
    
    def _compute_b2b_wishlist_count(self):
        for record in self:
            record.b2b_wishlist_count = len(self.env['kits.b2b.product.wishlist'].search([('partner_id','=',record.id)]))
            record.b2b_recent_view_count = len(self.env['kits.b2b.recent.view'].search([('partner_id','=',record.id)]))

    @api.model
    def create(self, vals):
        res = super(res_partner, self).create(vals)
        for record in res:    
            record.b2b_pricelist_id = record.property_product_pricelist.id
        return res
    
    def get_image(self):
        image_128 = self.user_id.partner_id.image_128
        return {'image': image_128}

    def action_open_wishlist(self):
        self.ensure_one()
        return {
            'name': _('Wishlist'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'kits.b2b.product.wishlist',
            'view_id': self.env.ref('kits_b2b_website.kits_b2b_product_wishlist_view_tree').id,
            'domain' : [('id','in',self.env['kits.b2b.product.wishlist'].search([('partner_id','=',self.id)]).ids)]
        }

    def action_open_recent_view(self):
        self.ensure_one()
        return {
            'name': _('Recent View'),
            'type': 'ir.actions.act_window',
            'view_mode': 'tree',
            'res_model': 'kits.b2b.recent.view',
            'view_id': self.env.ref('kits_b2b_website.kits_b2b_recent_view_tree').id,
            'domain' : [('id','in',self.env['kits.b2b.recent.view'].search([('partner_id','=',self.id)]).ids)]
        }
