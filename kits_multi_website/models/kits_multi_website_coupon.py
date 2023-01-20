from odoo import api, fields, models, _
from odoo.exceptions import UserError
from lxml import etree
from odoo.tools.safe_eval import safe_eval


class kits_multi_website_coupon(models.Model):
    _name = "kits.multi.website.coupon"
    _description = "Kits Multi Website Coupon"

    name = fields.Char("Coupon Name")
    min_qty = fields.Integer("Minimum Order Quantity")
    min_purchase = fields.Float("Minimum Purhcase")
    promo_code = fields.Char("Promo Code")
    discount_amount = fields.Float("Amount") 
    website_id = fields.Many2one("kits.b2c.website","Website")
    start_date = fields.Date("Start Date")
    end_date = fields.Date("End Date")
    coupon_customer_domain = fields.Char("Based On Customers")
    coupon_product_domain = fields.Char("Based On Products")
    can_be_used = fields.Integer("#Can Be Used")
    coupon_customer_line_ids = fields.One2many("kits.multi.website.coupon.customer.line", "coupon_id", "Coupon Customer Lines")
    coupon_customer_line_count = fields.Integer("Coupon Customer Line Count", compute="_compute_coupon_customer_line_count")
    coupon_image = fields.Char("Coupon Image",compute="_compute_coupon_image",store=True)
    coupon_image_public_url = fields.Char("Coupon Image Public URL")
    terms_and_conditions = fields.One2many(comodel_name='kits.multi.website.coupon.terms.conditions', inverse_name='coupon_id', string='Terms And Conditions')
    apply_on = fields.Selection([('percentage','Percentage'),('fixed_amount','Fixed Amount')],string='Apply On')
    coupon_image2 = fields.Char("Add To Cart Coupon Image",compute="_compute_coupon_image",store=True)
    coupon_image_public_url2 = fields.Char("Add To Cart Coupon Image Public URL")
    header_text = fields.Char('Header Text')
    product_details_text = fields.Char('Product Details Text')
    
    @api.depends('coupon_image_public_url','coupon_image_public_url2')
    def _compute_coupon_image(self):
        for record in self:
            record.coupon_image = record.coupon_image_public_url 
            record.coupon_image2 = record.coupon_image_public_url2 

    def _compute_coupon_customer_line_count(self):
        for record in self:
            record.coupon_customer_line_count = len(record.coupon_customer_line_ids)

    def action_open_coupon_customer_lines(self):
        tree_view_id = self.env.ref("kits_multi_website.kits_multi_website_coupon_customer_line_tree_view")
        return{
            'name': ('Customer Coupon Count'),
            'res_model': 'kits.multi.website.coupon.customer.line',
            'type': 'ir.actions.act_window',
            'views': [(tree_view_id.id, 'tree')],
            'domain': [('coupon_id','=',self.id)],
            'context': {'create':0},
            'target': 'current',
        }       

    @api.constrains('promo_code', 'start_date', 'end_date')
    def _check_promo_code(self):
        for record in self:
            if record.start_date and record.end_date:
                if record.end_date < record.start_date:
                    raise UserError("End Date cannot be smaller than Start Date!")
            if record.promo_code:
                coupon_ids = self.env['kits.multi.website.coupon'].search([('promo_code','=',record.promo_code), ('id','!=', record.id), ('website_id','=',record.website_id.id)])
                for coupon in coupon_ids:
                    if (record.start_date and record.end_date):
                        if coupon.start_date and coupon.end_date:
                            if ((coupon.start_date <= record.start_date <= coupon.end_date) and (coupon.start_date <= record.end_date <= coupon.end_date)):
                                raise UserError(f"Coupon {coupon.name} with promo code {coupon.promo_code} is already active! Please choose another Promo Code")
                            elif ((record.start_date <= coupon.start_date and (record.end_date <= coupon.end_date and record.end_date >= coupon.start_date)) or (record.start_date >= coupon.start_date and record.start_date <= coupon.end_date)):
                                raise UserError(f"Coupon {coupon.name} with promo code {coupon.promo_code} is already active! Please choose another Promo Code")
                        elif coupon.start_date and not coupon.end_date:
                            if (record.start_date <= coupon.start_date <= record.end_date) or (record.start_date >= coupon.start_date):
                                raise UserError(f"Coupon {coupon.name} with promo code {coupon.promo_code} is already active! Please choose another Promo Code")
                        elif not coupon.start_date and coupon.end_date:
                            if (record.start_date <= coupon.end_date <= record.end_date) or (record.end_date <= coupon.end_date):
                                raise UserError(f"Coupon {coupon.name} with promo code {coupon.promo_code} is already active! Please choose another Promo Code")
                    elif (record.start_date and not record.end_date):
                        if coupon.start_date and coupon.end_date:
                            if (coupon.start_date <= record.start_date <= coupon.end_date) or (record.start_date <= coupon.start_date):
                                raise UserError(f"Coupon {coupon.name} with promo code {coupon.promo_code} is already active! Please choose another Promo Code")
                        elif coupon.start_date and not coupon.end_date:
                            if record.start_date >= coupon.start_date: 
                                raise UserError(f"Coupon {coupon.name} with promo code {coupon.promo_code} is already active! Please choose another Promo Code")
                        elif not coupon.start_date and coupon.end_date:
                            if record.start_date <= coupon.end_date:
                                raise UserError(f"Coupon {coupon.name} with promo code {coupon.promo_code} is already active! Please choose another Promo Code")
                    elif (not record.start_date and record.end_date):
                        if coupon.start_date and coupon.end_date:
                            if (coupon.start_date >= record.end_date >= coupon.end_date) or (record.end_date >= coupon.end_date):
                                raise UserError(f"Coupon {coupon.name} with promo code {coupon.promo_code} is already active! Please choose another Promo Code")
                        elif coupon.start_date and not coupon.end_date:
                            if record.start_date >= coupon.start_date:
                                raise UserError(f"Coupon {coupon.name} with promo code {coupon.promo_code} is already active! Please choose another Promo Code")
                        elif not coupon.start_date and coupon.end_date:
                            if record.end_date <= coupon.end_date:
                                raise UserError(f"Coupon {coupon.name} with promo code {coupon.promo_code} is already active! Please choose another Promo Code")
                    else:
                        raise UserError(f"Coupon {coupon.name} with promo code {coupon.promo_code} is already active! Please choose another Promo Code")


    @api.model
    def default_get(self, fields):
        res = super(kits_multi_website_coupon, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_id'] =  website_id.id if website_id else False
        return res


    def add_website_id(self):
        return {
                'name': 'Add Website',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'kits.add.remove.website.wizard',
                'views': [(self.env.ref('kits_multi_website.kits_add_remove_website_wizard_form_view').id, 'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'context':{'default_is_add': True,'default_res_model': self._name,'default_res_id' : self.ids}
            }   
    
    def remove_website_id(self):
            return {
                'name': 'Remove Website',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'kits.add.remove.website.wizard',
                'views': [(self.env.ref('kits_multi_website.kits_add_remove_website_wizard_form_view').id, 'form')],
                'type': 'ir.actions.act_window',
                'target':'new',
                'context':{'default_is_add': False,'default_res_model': self._name,'default_res_id' : self.ids}
            }   


    
    def get_coupon_datas(self,customer_id):
        coupon_data_list = []
        for record in self.search([]):
            domain = record.coupon_customer_domain or '[]'
            if customer_id:
                customer_ids = self.env['kits.multi.website.customer'].search(safe_eval(domain)).ids
                if customer_id in customer_ids:
                    line_list = []
                    for line in record.terms_and_conditions:
                        line_list.append({
                            'id': line.id, 
                            'name': line.name, 
                            'sequence': line.sequence, 
                        })
                    coupon_data_list.append({
                        'terms_and_conditions': line_list,
                        'add_to_cart_image_url': record.coupon_image_public_url2,
                        'coupon_image_url': record.coupon_image_public_url,
                        'id': record.id,
                        'name': record.name,
                        'promo_code': record.promo_code,
                    })                
        return coupon_data_list
                
    def get_all_coupon_datas(self):
        coupon_data_list = []
        for record in self.search([]):
            domain = record.coupon_customer_domain or '[]'
            if domain =='[]':
                line_list = []
                for line in record.terms_and_conditions:
                    line_list.append({
                        'id': line.id, 
                        'name': line.name, 
                        'sequence': line.sequence, 
                    })
                coupon_data_list.append({
                    'terms_and_conditions': line_list,
                    'add_to_cart_image_url': record.coupon_image_public_url2,
                    'coupon_image_url': record.coupon_image_public_url,
                    'id': record.id,
                    'name': record.name,
                    'promo_code': record.promo_code,
                })
        return coupon_data_list
                
    def kits_get_coupon(self,customer_id=False,header=False,product_details=False):
        coupon_data_list = []
        product_details = int(product_details)
        for record in self.search([]):
            domain = record.coupon_customer_domain or '[]'
            if record.coupon_product_domain == '[]':
                product_ids = [product_details]
            else:
                product_ids = self.env['product.product'].search(safe_eval(record.coupon_product_domain or '[]')).ids
            if customer_id:
                customer_ids = self.env['kits.multi.website.customer'].search(safe_eval(domain)).ids
                if customer_id in customer_ids:
                    coupon_data_list.append({
                        'name': record.header_text if header else record.product_details_text if product_details and  product_details in product_ids  else record.name,
                    })
            else:
                if domain == '[]':
                    coupon_data_list.append({
                        'name': record.header_text if header else record.product_details_text if product_details and  product_details in product_ids  else record.name,
                    })
                
        return coupon_data_list
