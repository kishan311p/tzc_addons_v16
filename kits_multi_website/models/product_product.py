from odoo import api, fields, models, _
import json

class product_product(models.Model):
    _inherit = 'product.product'

    website_ids = fields.Many2many("kits.b2c.website","product_product_b2c_website_rel","product_id","website_id","Websites")
    slider_category_ids = fields.Many2many("kits.multi.website.product.slider.category","product_product_slider_category_rel","product_id","product_slider_category_id","Slider Categories")

    b2c_order_line_ids = fields.One2many('kits.multi.website.sale.order.line', 'product_id', 'B2C Order Lines')
    sold_qty = fields.Float('Sold Qty', compute="_compute_sold_qty", store=True, compute_sudo=True)

    @api.depends('b2c_order_line_ids','b2c_order_line_ids.state','b2c_order_line_ids.quantity','b2c_order_line_ids.sale_order_id')
    def _compute_sold_qty(self):
        for record in self:
            record.sold_qty = sum(record.b2c_order_line_ids.filtered(lambda line: line.sale_order_id.state not in ('quotation','cancel') and line.quantity > 0).mapped('quantity'))

    @api.model
    def default_get(self, fields):
        res = super(product_product, self).default_get(fields)
        if self._context.get('kits_website_name'):
            website_id = self.env['kits.b2c.website'].search([('website_name','=',self._context.get('kits_website_name'))])
            res['website_ids'] =  [(4,website_id.id)] if website_id else False
        return res

    def action_set_products(self):
        form_view_id = self.env.ref("kits_multi_website.kits_multi_website_set_product_form_view")
        return{
            'name': ('Set Product To Websites'),
            'res_model': 'kits.multi.website.set.product',
            'type': 'ir.actions.act_window',
            'views': [(form_view_id.id, 'form')],
            'context': {'default_product_ids': [(6,0,self.ids)]},
            'target': 'new',
        }
    
    @api.model
    def fields_view_get(self, view_id=None, view_type='tree', toolbar=False, submenu=False):
        res = super(product_product, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        if self._context.get('kits_multi_website') != 1:
            if 'toolbar' in res.keys():
                actions = res.get('toolbar').get('action')
                for action_dict in actions:
                    if action_dict['xml_id'] == 'kits_multi_website.action_set_products':
                        actions.remove(action_dict)
        return res

    def action_set_slider_category_to_products(self):
        form_view_id = self.env.ref("kits_multi_website.kits_multi_website_set_slider_category_form_view")
        return{
            'name': ('Set Slider Category to Product'),
            'res_model': 'kits.multi.website.set.slider.category',
            'type': 'ir.actions.act_window',
            'views': [(form_view_id.id, 'form')],
            'context': {'default_product_ids': [(6,0,self.ids)]},
            'target': 'new',
        }

    def check_qty_available_qty(self,req_list):
        product_obj = self.env['product.product']
        website = self.env['website'].get_current_website()
        line_product_dict = {}
        new_dict = {}
        for data in req_list:
            msg = 'null'
            msg2 = 'null'
            line_remove = False
            product_id = product_obj.browse(data.get('product_id'))
            product_id._compute_sold_qty()
            if line_product_dict.get(product_id.id):
                line_product_dict[product_id.id] = line_product_dict[product_id.id]+data.get('qty',0)
            else:
                line_product_dict[product_id.id] = data.get('qty',0)

            available_qty_spt = product_id.with_context(warehouse=website.warehouse_id.id).available_qty_spt
            minimum_qty_spt = product_id.with_context(warehouse=website.warehouse_id.id).minimum_qty
            if product_id.with_context(warehouse=website.warehouse_id.id).on_consignment:
                available_qty_spt = available_qty_spt - minimum_qty_spt
            if available_qty_spt < line_product_dict.get(product_id,1):
                # msg= "Some products have sold out and your cart has been updated. Please don't delay processing your order."
                msg = "The product is sold out, please remove from cart/Product will remove when the order is placed."
                line_remove = True
            else:
                total_line_qty = len([rec.get('product_id') for rec in req_list if product_id.id == rec.get('product_id') and rec.get('qty')!=0])
                if minimum_qty_spt >= line_product_dict.get(product_id,1):
                    msg = 'Only %s pcs are available now.'%(available_qty_spt-line_product_dict.get(product_id.id))
                if total_line_qty >1: 
                    msg = 'You already added %s units in your cart.'%(total_line_qty)
                if (available_qty_spt-line_product_dict.get(product_id.id))> 0 :
                    if 'pcs are available now.' not in msg:            
                        msg2 = 'There are only %s units available'%(available_qty_spt-line_product_dict.get(product_id.id))
                else:
                    msg = "The product is sold out, please remove from cart/Product will remove when the order is placed."
                    line_remove = True

            new_dict[str(data['id'])]= [msg,msg2,line_remove]
        return new_dict
