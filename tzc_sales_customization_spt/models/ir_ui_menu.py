from odoo import api,models,_,fields,tools
from collections import defaultdict

class ir_ui_menu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        """ Return the ids of the menu items visible to the user. """
        # retrieve all menus, and determine which ones are visible
        context = {'ir.ui.menu.full_list': True}
        menus = self.with_context(context).search([]).sudo()

        groups = self.env.user.groups_id
        if not debug:
            groups = groups - self.env.ref('base.group_no_one')
        # first discard all menus with groups the user does not have
        menus = menus.filtered(
            lambda menu: not menu.groups_id or menu.groups_id & groups)

        # Add case product menu for warehouse user 
        if self.env.user.is_warehouse:
            case_id = self.env.ref("tzc_sales_customization_spt.menu_case_product_tree")
            if case_id not in menus:
                menus = menus+case_id

        # take apart menus that have an action
        actions_by_model = defaultdict(set)
        for action in menus.mapped('action'):
            if action:
                actions_by_model[action._name].add(action.id)
        existing_actions = {
            action
            for model_name, action_ids in actions_by_model.items()
            for action in self.env[model_name].browse(action_ids).exists()
        }
        action_menus = menus.filtered(lambda m: m.action and m.action in existing_actions)
        folder_menus = menus - action_menus
        visible = self.browse()

        # process action menus, check whether their action is allowed
        access = self.env['ir.model.access']
        MODEL_BY_TYPE = {
            'ir.actions.act_window': 'res_model',
            'ir.actions.report': 'model',
            'ir.actions.server': 'model_name',
        }

        # performance trick: determine the ids to prefetch by type
        prefetch_ids = defaultdict(list)
        for action in action_menus.mapped('action'):
            prefetch_ids[action._name].append(action.id)

        for menu in action_menus:
            action = menu.action
            action = action.with_prefetch(prefetch_ids[action._name])
            model_name = action._name in MODEL_BY_TYPE and action[MODEL_BY_TYPE[action._name]]
            if not model_name or access.check(model_name, 'read', False):
                # make menu visible, and its folder ancestors, too
                visible += menu
                menu = menu.parent_id
                while menu and menu in folder_menus and menu not in visible:
                    visible += menu
                    menu = menu.parent_id

        return set(visible.ids)
