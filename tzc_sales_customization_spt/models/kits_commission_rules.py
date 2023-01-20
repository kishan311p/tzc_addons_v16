from odoo import _, api, fields, models, tools
from odoo.exceptions import UserError

class kits_commission_rules(models.Model):
    _name = "kits.commission.rules"
    _description = 'Kits Commission Rules'

    type = fields.Selection([('list_price', 'Fixed percentage commission on discounted price'),('on_item', 'Conditional percentage commission on discounted price'),('fixed_list_price', 'Fixed percentage commission on list price'),('condition_list_price', 'Conditional percentage commission on list price'),('lower_commission_rule','Lower Commission')],default="list_price",string='Commission Type')
    commission_for = fields.Selection([('sales_person', 'Salesperson'),('sales_manager', 'Sales Manager'),('both','Both (Salesperson and Sales Manager)')],default="sales_person")
    over_commission_per = fields.Float(default=0.0)
    over_product_price = fields.Float(default=0.0)
    less_commission_per = fields.Float(default=0.0)
    less_product_price = fields.Float(default=0.0)
    on_list_price = fields.Float(default=0.0)
    name = fields.Char("Commission Name")
    description = fields.Html('Help',compute="_compute_type_description")

    _sql_constraints = [
        ('kits_commission_rule_name','unique(name)',_('Commission Rule Name should be unique.')),
    ]

    commission_type_description = {
        'list_price':"""The commission percentage given will be applied on discounted subtotal of Sale order.""",
        'on_item':"""The commission percentage will be applied based on the discounted price of product.""",
        'fixed_list_price':"""The commission will be applied on the subtotal of sale order.""",
        'condition_list_price':"""The commission will be applied based on the price of product.""",
        'lower_commission_rule':"""<b>'Commission Percentage'</b> will be applied on the price of products,<br/>then discount will be deducted from counted commission amount,<br/>If discount is higher than applied <b>'Commission Percentage'</b> then minimum commission will apply,which is:lower of <b>'Lower Commission Percentage'</b> or  <b>'Lower Commission'</b> per item, calculated on net sale amount.""",
    }
    
    @api.depends('type')
    def _compute_type_description(self):
        for rec in self:
            rec.description = rec.commission_type_description.get(rec.type)

    def get_commission(self,invoice):
        self.ensure_one()
        commission = 0
        if self.id and invoice and invoice.id:
            if self.type == 'list_price':
                # count fixed commission on discounted price
                commission = round((invoice.amount_without_discount - invoice.amount_discount) * self.on_list_price * 0.01,2)
            elif self.type == 'on_item':
                # count conditional commission on discounted price
                line_commission = 0
                for line in invoice.invoice_line_ids.filtered(lambda x: not x.product_id.is_shipping_product and not x.product_id.is_admin and not x.product_id.is_global_discount):
                    # allow product only
                    comm = 0
                    unit_discount_price = round(line.discount_unit_price,2)
                    if unit_discount_price > self.over_product_price:
                        comm = round(unit_discount_price * line.quantity * self.over_commission_per * 0.01,2)
                    if unit_discount_price < self.less_product_price:
                        comm = round(unit_discount_price * line.quantity * self.less_commission_per * 0.01,2)
                    line_commission += comm
                commission = line_commission

            elif self.type == 'fixed_list_price':
                # count fix commission on list price
                commission = round(invoice.amount_without_discount * self.on_list_price * 0.01,2)
            elif self.type == 'condition_list_price':
                # count conditional commission on list price
                line_commission = 0
                for line in invoice.invoice_line_ids.filtered(lambda x: not x.product_id.is_shipping_product and not x.product_id.is_admin and not x.product_id.is_global_discount):
                    comm = 0
                    if line.price_unit > self.over_product_price:
                        comm = round(line.price_unit * line.quantity * self.over_commission_per * 0.01,2)
                    if line.price_unit < self.less_product_price:
                        comm = round(line.price_unit * line.quantity * self.less_commission_per * 0.01,2)
                    line_commission += comm
                commission = line_commission
            elif self.type == 'lower_commission_rule':
                order = self.env['sale.order'].search([('invoice_ids','in',invoice.ids)]).filtered(lambda x: x.state in ('open_inv','paid'))
                final_commission = 0
                if order:
                    # find commission on lines
                    for line in invoice.invoice_line_ids.filtered(lambda x: not x.product_id.is_shipping_product and not x.product_id.is_admin and not x.product_id.is_global_discount):
                        l_commission = round(line.price_unit * self.less_commission_per * 0.01,2)
                        # fix-discount-price not in move_lines
                        after_discount = round(l_commission - line.unit_discount_price,2)
                        # discount = 0.0
                        # try:
                        #     discount = round(((line.price_unit - line.unit_discount_price )*100)/line.price_unit,2)
                        # except:
                        #     pass
                        # if discount > self.less_commission_per:
                        if after_discount > 0:
                            # final_commission += ( min([self.on_list_price,round((line.unit_discount_price*self.less_product_price)/100,2)])) * line.qty_invoiced
                            final_commission += round(after_discount * line.quantity,2)
                        else:
                            final_commission += round(min([self.on_list_price,round((line.discount_unit_price*self.less_product_price)/100,2)]) * line.quantity,2)
                commission = final_commission
            else:
                raise UserError(_('Unexpected Commission rule found.'))
        return round(commission,2)
