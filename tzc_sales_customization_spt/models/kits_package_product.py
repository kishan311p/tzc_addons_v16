from odoo import models,fields,api,_
from odoo.exceptions import UserError

class kits_package_product(models.Model):
    _name = 'kits.package.product'
    _description = 'To create Package of multiple products.'

    name = fields.Char('Name',required=True,default='New')
    pack_description = fields.Html('Description  ')
    package_seo_name = fields.Char('Seo Name') 
    pack_seo_split_name = fields.Char('Seo Name Split')
    pack_product_image_url = fields.Char('Product Image ')
    pack_product_image = fields.Binary('Product Image') 
    is_published = fields.Boolean('Is Published')
    pack_product_url = fields.Char('Package Product Url',compute="_compute_pack_url",store=True,compute_sudo=True)
    product_line_ids = fields.One2many('kits.package.product.lines','combo_product_id',string='Package Product Lines')
     
    # sale_price_cad = fields.Float('Sale Price CAD')
    sale_price_usd = fields.Float('Sale Price',compute="_calc_sale_price_usd",store=True,compute_sudo=True)
    discounted_price_usd = fields.Float('Discounted Price',compute="_calc_discounted_price_usd",store=True,compute_sudo=True)
    # discounted_price_cad = fields.Float('Discounted Price CAD')
    # website_size_x = fields.Integer('Size X', default=1)
    # website_size_y = fields.Integer('Size Y', default=1)
    # website_style_ids = fields.Many2many('product.style', string='Styles')

    # for promotion
    start_date = fields.Date('Package Start Date')
    end_date = fields.Date('Package End Date')
    # promo_code = fields.Char('Promocode')
    # is_promotion_required = fields.Boolean('Promo Code Requied ?')
    partner_ids = fields.Many2many('res.partner','package_product_partner_id_rel','package_product_id','partner_id', string='Customers',copy=True)

    select_all = fields.Boolean('Select All')
    is_global = fields.Boolean('Is Public')

    _sql_constraints = [
        ('kits_package_seo_name','unique(package_seo_name)',_('Package SEO Name should be unique.'))
        # ,('kits_promo_code','unique(promo_code)',_('Package Promo Code should be unique.')),
    ]
    
    @api.depends('product_line_ids','product_line_ids.product_price','product_line_ids.qty')
    def _calc_sale_price_usd(self):
        for rec in self:
            # cad_rate  = float(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.on_sale_cad_spt', default=0))
            sale_price_usd = 0.0
            for line in rec.product_line_ids:
                sale_price_usd += round(line.product_price * line.qty,2)
            rec.sale_price_usd = sale_price_usd
            # rec.sale_price_cad = round(sale_price_usd * cad_rate,2)
    
    @api.onchange('product_line_ids')
    def on_change_product_lines(self):
        for rec in self:
            rec._calc_sale_price_usd()
            rec._calc_discounted_price_usd()
    
    # def _calc_discounted_price_cad(self):
    #     cad_rate  = float(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.on_sale_cad_spt', default=0))
    #     for rec in self:
    #         discounted_price_cad = 0.0
    #         if rec.discounted_price_usd:
    #             discounted_price_cad = round(rec.discounted_price_usd * cad_rate,2)
    #         rec.discounted_price_cad = discounted_price_cad

    @api.depends('product_line_ids','product_line_ids.subtotal')
    def _calc_discounted_price_usd(self):
        # cad_rate  = float(self.env['ir.config_parameter'].sudo().get_param('tzc_sales_customization_spt.on_sale_cad_spt', default=0))
        for rec in self:
            discounted_price_usd = 0.0
            # discounted_price_cad = 0.0
            for line in rec.product_line_ids:
                discounted_price_usd += line.subtotal
            rec.discounted_price_usd = discounted_price_usd
            # rec.discounted_price_cad = round(discounted_price_usd * cad_rate,2)
            
    @api.depends('package_seo_name')
    def _compute_pack_url(self):
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        pack_product_url = ''
        for rec in self:
            seo_name = rec.package_seo_name
            pack_seo_split_name = ''
            if seo_name:
                pack_seo_split_name = '-'.join(seo_name.split()) + '-' +str(rec.id) 
                rec.pack_seo_split_name = pack_seo_split_name
            if pack_seo_split_name:
                pack_product_url = base_url + '/package-product/' + pack_seo_split_name
            rec.pack_product_url = pack_product_url
            
    def product_is_publish(self):
        self.write({'is_published':True})
    
    def product_is_unpublish(self):
        self.write({'is_published':False})
    
    def action_bulk_price_change(self):
        return {
            'name':_('Bulk Product Discount'),
            'type' :'ir.actions.act_window',
            'res_model':'kits.bulk.discount.on.package.products',
            'view_mode':'form',
            'context':{'default_pack_product_id':self.id},
            'target':'new'
        }

    @api.onchange('select_all')
    def _onchange_select_all(self):
        for record in self:
            if record.select_all:
                record.partner_ids = [(6,0,self.env['res.partner']._search([]))]
            else:
                record.partner_ids = False

    def get_package_validation(self):
        vals = {}
        user = self.env.user
        partner = user.partner_id
        product_products = self.product_line_ids.product_id       
        unpublished_ids = product_products.filtered(lambda product: not product.is_published_spt or product.available_qty_spt <= 0)
        filtered_products = product_products - unpublished_ids
        restricted_ids = filtered_products.filtered(lambda product:user.country_id.id in product.geo_restriction.ids )
        # public user
        if user._is_public():
            vals.update({
                'is_public':True,
                'warning_message':False
            })
        elif not user._is_public():
            # verification is in process.
            if partner.customer_type == 'b2c':
                vals.update({
                    "is_public":False,
                    "warning_message":"Hey, we're so sorry. Your account is not yet verified. Please contact your salesperson for more help."
                })

            # line not found
            elif partner.customer_type == 'b2b_regular' and not self.product_line_ids:
                vals.update({
                    "is_public":False,
                    "warning_message":"You can't add this package in your cart, because package doesn't contains any items."
                })

            # customer not added in package
            elif partner.customer_type == 'b2b_regular' and self.product_line_ids and partner.id not in self.partner_ids.ids:
                vals.update({
                    "is_public":False,
                    "warning_message":"Hey, we're so sorry. You can't add this package to your cart because you are not eligible for this package. Please contact your salesperson for more help."
                })
            
            # out of stock and georistrictions
            elif partner.customer_type == 'b2b_regular' and self.product_line_ids and partner.id in self.partner_ids.ids and unpublished_ids and restricted_ids:
                vals.update({
                    "is_public":False,
                    "warning_message":"Hey, we're so sorry. You can't add this package to your cart because it is either out of stock or there is a restriction for your area. Please contact your salesperson for more help."
                })

            # georistrictions
            elif partner.customer_type == 'b2b_regular' and self.product_line_ids and partner.id in self.partner_ids.ids and not unpublished_ids and restricted_ids:
                vals.update({
                    "is_public":False,
                    "warning_message":"Hey, we're so sorry. You can't add this package to your cart because it is a restriction for your area. Please contact your salesperson for more help."
                })

            # out of stock
            elif partner.customer_type == 'b2b_regular' and self.product_line_ids and partner.id in self.partner_ids.ids and unpublished_ids and not restricted_ids:
                vals.update({
                    "is_public":False,
                    "warning_message":"Hey, we're so sorry. You can't add this package to your cart because it is out of stock. Please contact your salesperson for more help."
                })
        else:
            vals.update({
                "is_public":False,
                "warning_message":False
            })
        return vals

        
    @api.constrains('product_line_ids')
    def _constarains_product_line_ids(self):
        for record in self:
            restricted = self.env['product.product'].search([('id','in',record.product_line_ids.mapped('product_id').ids),('geo_restriction','in',self.env.user.partner_id.country_id.ids)])
            for line in record.product_line_ids:
                error = ''
                if not line.product_id.is_published_spt:
                    error = 'not published.'
                if  line.product_id.available_qty_spt < 1 or (line.qty*line.product_id.available_qty_spt) < 1:
                    error = 'not available'
                if line.product_id in restricted:
                    error = 'restricted'
                if len(record.product_line_ids.filtered(lambda x: x.product_id == line.product_id)) > 1:
                    raise UserError(_('Product {} found multiple times in package.'.format(line.product_id.variant_name)))
                if error:
                    raise UserError(_('You can not add product {}. It is {}'.format(line.product_id.variant_name,error)))

    def check_product_stock(self):
        user_country = self.env.user.country_id.id
        geo_ristricted = True if user_country in self.product_line_ids.mapped('product_id.geo_restriction').ids else False
        out_of_stock = False
        for product in self.product_line_ids.product_id:
            if product.on_consignment and product.actual_stock <= 0.0:
                out_of_stock = True
            elif product.available_qty_spt <= 0.0:
                out_of_stock = True
        return out_of_stock,geo_ristricted
