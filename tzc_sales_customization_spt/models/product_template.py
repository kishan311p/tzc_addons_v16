from odoo import _, api, fields, models, tools

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # tab_line_ids = fields.One2many('product.tab.line', 'product_id', 'Product Tabs',help="Set the product tabs")
    # label_line_ids = fields.One2many('product.label.line', 'product_tmpl_id', 'Product Labels',help="Set the number of product labels")
    is_shipping_product = fields.Boolean("Is Shipping Product (Flag)")
    is_admin = fields.Boolean("Is Admin Fee (Flag)")
    is_global_discount = fields.Boolean('Is Additional Discount (Flag)')
    # kits_ecom_categ_id = fields.Many2one('product.public.category','Website Product Category')
    is_forcefully_unpublished = fields.Boolean('Forcefully Unpublished')
    product_variant_id = fields.Many2one('product.product', 'Product', compute='_compute_product_variant_id',store=True)

    brand = fields.Many2one('product.brand.spt','Brand')
    model = fields.Many2one('product.model.spt','Model')

    @api.depends('product_variant_ids')
    def _compute_product_variant_id(self):
        for p in self:
            p.product_variant_id = p.product_variant_ids[:1].id

    # @api.constrains('tab_line_ids')
    # def check_tab_lines(self):
    #     if len(self.tab_line_ids) > 4:
    #         raise Warning("You can not create more then 4 tabs!!")

    def open_product_variant_spt(self):
        product_ids = self.env['product.product'].search([('product_tmpl_id','=',self.id)])
        tree_view_id = self.env.ref('product.product_product_tree_view').id
        form_view_id = self.env.ref('product.product_normal_form_view').id
        return {
            'name': _('Product Variants'),
            'view_mode': 'tree,form',
            'view_type':'form',
            'views':[[tree_view_id,'tree'],[form_view_id,'form']],
            'domain': [('id','in',product_ids.ids)],
            'res_model': 'product.product',
            'type': 'ir.actions.act_window',
        }
    

    def action_view_stock_move_lines(self):
        action = super(ProductTemplate,self).action_view_stock_move_lines()
        action['context'] ="{'create': 0}"
        return action

    def _get_possible_variants_sorted(self, parent_combination=None):
        # res = super(ProductTemplate,self)._get_possible_variants_sorted(parent_combination=None)
        # reduce to check combination from template and validation
        # sorted_list = product_varints.sorted(lambda p:(p.product_color_name.name,p.eye_size_compute))
        # similar_products = self.env['product.product'].search([('brand','=',product_varints.brand.name),('model','=',product_varints.model.name),('categ_id','=',product_varints.categ_id.name)])
        product_varints = self.product_variant_ids.filtered(lambda pv:pv.is_published_spt)
        country_id = self.env.user.country_id.ids
        similar_products = self.env['product.product'].search([('is_published_spt','=',True),('geo_restriction','not in',country_id),('brand','=',product_varints.brand.name),('model','=',product_varints.model.name),('categ_id','=',product_varints.categ_id.name)])
        sorted_list = similar_products.sorted(lambda x:(x.color_code.name,int(x.eye_size.name)))
        # sorted_list = similar_products.sorted(lambda x:(x.product_color_name.name,int(x.eye_size.name)))
        return sorted_list

    # temparary replaced methods
    def _is_combination_possible_by_config(self, combination, ignore_no_variant=False):
        """Return whether the given combination is possible according to the config of attributes on the template

        :param combination: the combination to check for possibility
        :type combination: recordset `product.template.attribute.value`

        :param ignore_no_variant: whether no_variant attributes should be ignored
        :type ignore_no_variant: bool

        :return: wether the given combination is possible according to the config of attributes on the template
        :rtype: bool
        """
        self.ensure_one()

        # attribute_lines = self.valid_product_template_attribute_line_ids

        # if ignore_no_variant:
        #     attribute_lines = attribute_lines._without_no_variant_attributes()

        # if len(combination) != len(attribute_lines):
        #     # number of attribute values passed is different than the
        #     # configuration of attributes on the template
        #     return False

        # if attribute_lines != combination.attribute_line_id:
        #     # combination has different attributes than the ones configured on the template
        #     return False

        # if not (attribute_lines.product_template_value_ids._only_active() >= combination):
        #     # combination has different values than the ones configured on the template
        #     return False

        return True
    def _is_combination_possible(self, combination, parent_combination=None, ignore_no_variant=False):
        """
        The combination is possible if it is not excluded by any rule
        coming from the current template, not excluded by any rule from the
        parent_combination (if given), and there should not be any archived
        variant with the exact same combination.

        If the template does not have any dynamic attribute, the combination
        is also not possible if the matching variant has been deleted.

        Moreover the attributes of the combination must excatly match the
        attributes allowed on the template.

        :param combination: the combination to check for possibility
        :type combination: recordset `product.template.attribute.value`

        :param ignore_no_variant: whether no_variant attributes should be ignored
        :type ignore_no_variant: bool

        :param parent_combination: combination from which `self` is an
            optional or accessory product.
        :type parent_combination: recordset `product.template.attribute.value`

        :return: whether the combination is possible
        :rtype: bool
        """
        self.ensure_one()

        if not self._is_combination_possible_by_config(combination, ignore_no_variant):
            return False

        variant = self._get_variant_for_combination(combination)

        if self.has_dynamic_attributes():
            if variant and not variant.active:
                # dynamic and the variant has been archived
                return False
        else:
            # if not variant or not variant.active:
                # not dynamic, the variant has been archived or deleted
            return True

        exclusions = self._get_own_attribute_exclusions()
        if exclusions:
            # exclude if the current value is in an exclusion,
            # and the value excluding it is also in the combination
            for ptav in combination:
                for exclusion in exclusions.get(ptav.id):
                    if exclusion in combination.ids:
                        return False

        parent_exclusions = self._get_parent_attribute_exclusions(parent_combination)
        if parent_exclusions:
            # parent_exclusion are mapped by ptav but here we don't need to know
            # where the exclusion comes from so we loop directly on the dict values
            for exclusions_values in parent_exclusions.values():
                for exclusion in exclusions_values:
                    if exclusion in combination.ids:
                        return False

        return True
