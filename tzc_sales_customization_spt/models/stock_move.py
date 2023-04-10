from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare, float_is_zero, float_round
from odoo.tools.misc import clean_context, OrderedSet, groupby
from collections import defaultdict
import base64
import requests
import json

class stock_move(models.Model):
    _inherit = 'stock.move'

    package_id = fields.Many2one('kits.package.product',compute="_compute_package_id",store=True,compute_sudo=True)
    qty_available = fields.Float('Total Qty',related='product_id.qty_available')
    pro_primary_image_url = fields.Char("Primary Image URL",related='product_id.primary_image_url')

    @api.depends('sale_line_id','sale_line_id.package_id')
    def _compute_package_id(self):
        for record in self:
            if record.sale_line_id and record.sale_line_id.is_pack_order_line:
                record.package_id = record.sale_line_id.package_id.id

    def stock_quant_update_spt(self):
        context={}
        for move in self:
            if move.product_id.type == "product":
                for line in move.move_line_ids:
                    if line.picking_id.state in ['done','cancel']:
                        line.qty_done = 0
                        qty = line.product_uom_id._compute_quantity(line.qty_done, line.product_id.uom_id)
                        self.env['stock.quant']._update_available_quantity(line.product_id, line.location_id, qty)
                        self.env['stock.quant']._update_available_quantity(line.product_id, line.location_dest_id, qty * -1)
            move.write({
                'quantity_done' : 0,
                'state' : 'cancel'
            })
            context.update(self._context)
            context.update({'stock_quant_update_spt':True})
            move.with_context(context)._action_cancel()
        return True

    @api.depends('picking_id', 'name')
    def _compute_reference(self):
        for move in self:
            move_reference = False
            if move.picking_id:
                move_reference = move.picking_id.name
            if move_reference and move.sale_line_id:
                move.reference = '%s (%s)'%(move.sale_line_id.order_id.name,move_reference)
            else:
                move.reference = ''

    def _action_done(self, cancel_backorder=False):
        moves = self.filtered(lambda move: move.state == 'draft')._action_confirm()  # MRP allows scrapping draft moves
        moves = (self | moves).exists().filtered(lambda x: x.state not in ('done', 'cancel'))
        moves_ids_todo = OrderedSet()

        # Cancel moves where necessary ; we should do it before creating the extra moves because
        # this operation could trigger a merge of moves.
        for move in moves:
            if move.quantity_done <= 0 and not move.is_inventory:
                if float_compare(move.product_uom_qty, 0.0, precision_rounding=move.product_uom.rounding) == 0 or cancel_backorder:
                    move._action_cancel()

        # Create extra moves where necessary
        for move in moves:
            if move.state == 'cancel' or (move.quantity_done <= 0 and not move.is_inventory):
                continue

            moves_ids_todo |= move._create_extra_move().ids

        moves_todo = self.browse(moves_ids_todo)
        moves_todo._check_company()
        # Split moves where necessary and move quants
        backorder_moves_vals = []
        for move in moves_todo:
            # To know whether we need to create a backorder or not, round to the general product's
            # decimal precision and not the product's UOM.
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            if float_compare(move.quantity_done, move.product_uom_qty, precision_digits=rounding) < 0:
                # Need to do some kind of conversion here
                qty_split = move.product_uom._compute_quantity(move.product_uom_qty - move.quantity_done, move.product_id.uom_id, rounding_method='HALF-UP')
                new_move_vals = move._split(qty_split)
                backorder_moves_vals += new_move_vals
        backorder_moves = self.env['stock.move'].create(backorder_moves_vals)
        # The backorder moves are not yet in their own picking. We do not want to check entire packs for those
        # ones as it could messed up the result_package_id of the moves being currently validated
        backorder_moves.with_context(bypass_entire_pack=True)._action_confirm(merge=False)
        if cancel_backorder:
            backorder_moves.with_context(moves_todo=moves_todo)._action_cancel()
        moves_todo.mapped('move_line_ids').sorted()._action_done()
        # Check the consistency of the result packages; there should be an unique location across
        # the contained quants.
        for result_package in moves_todo\
                .mapped('move_line_ids.result_package_id')\
                .filtered(lambda p: p.quant_ids and len(p.quant_ids) > 1):
            if len(result_package.quant_ids.filtered(lambda q: not float_is_zero(abs(q.quantity) + abs(q.reserved_quantity), precision_rounding=q.product_uom_id.rounding)).mapped('location_id')) > 1:
                raise UserError(_('You cannot move the same package content more than once in the same transfer or split the same package into two location.'))
        picking = moves_todo.mapped('picking_id')
        moves_todo.write({'state': 'done', 'date': fields.Datetime.now()})

        new_push_moves = moves_todo.filtered(lambda m: m.picking_id.immediate_transfer)._push_apply()
        if new_push_moves:
            new_push_moves._action_confirm()
        move_dests_per_company = defaultdict(lambda: self.env['stock.move'])
        for move_dest in moves_todo.move_dest_ids:
            move_dests_per_company[move_dest.company_id.id] |= move_dest
        for company_id, move_dests in move_dests_per_company.items():
            move_dests.sudo().with_company(company_id)._action_assign()

        # We don't want to create back order for scrap moves
        # Replace by a kwarg in master
        if self.env.context.get('is_scrap'):
            return moves_todo

        if picking and not cancel_backorder and not self._context.get('skip_backorder'):
            backorder = picking._create_backorder()
            if any([m.state == 'assigned' for m in backorder.move_ids]):
               backorder._check_entire_pack()
        return moves_todo

    def _action_assign(self, force_qty=False):
        """ Reserve stock moves by creating their stock move lines. A stock move is
        considered reserved once the sum of `reserved_qty` for all its move lines is
        equal to its `product_qty`. If it is less, the stock move is considered
        partially available.
        """
        StockMove = self.env['stock.move']
        assigned_moves_ids = OrderedSet()
        partially_available_moves_ids = OrderedSet()
        # Read the `reserved_availability` field of the moves out of the loop to prevent unwanted
        # cache invalidation when actually reserving the move.
        reserved_availability = {move: move.reserved_availability for move in self}
        roundings = {move: move.product_id.uom_id.rounding for move in self}
        move_line_vals_list = []
        # Once the quantities are assigned, we want to find a better destination location thanks
        # to the putaway rules. This redirection will be applied on moves of `moves_to_redirect`.
        moves_to_redirect = OrderedSet()
        moves_to_assign = self
        if not force_qty:
            moves_to_assign = self.filtered(lambda m: m.state in ['confirmed', 'waiting', 'partially_available'])
        for move in moves_to_assign:
            rounding = roundings[move]
            if not force_qty:
                missing_reserved_uom_quantity = move.product_uom_qty
            else:
                missing_reserved_uom_quantity = force_qty
            missing_reserved_uom_quantity -= reserved_availability[move]
            missing_reserved_quantity = move.product_uom._compute_quantity(missing_reserved_uom_quantity, move.product_id.uom_id, rounding_method='HALF-UP')
            if move._should_bypass_reservation():
                # create the move line(s) but do not impact quants
                if move.move_orig_ids:
                    available_move_lines = move._get_available_move_lines(assigned_moves_ids, partially_available_moves_ids)
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        qty_added = min(missing_reserved_quantity, quantity)
                        move_line_vals = move._prepare_move_line_vals(qty_added)
                        move_line_vals.update({
                            'location_id': location_id.id,
                            'lot_id': lot_id.id,
                            'lot_name': lot_id.name,
                            'owner_id': owner_id.id,
                        })
                        move_line_vals_list.append(move_line_vals)
                        missing_reserved_quantity -= qty_added
                        if float_is_zero(missing_reserved_quantity, precision_rounding=move.product_id.uom_id.rounding):
                            break

                if missing_reserved_quantity and move.product_id.tracking == 'serial' and (move.picking_type_id.use_create_lots or move.picking_type_id.use_existing_lots):
                    for i in range(0, int(missing_reserved_quantity)):
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=1))
                elif missing_reserved_quantity:
                    to_update = move.move_line_ids.filtered(lambda ml: ml.product_uom_id == move.product_uom and
                                                            ml.location_id == move.location_id and
                                                            ml.location_dest_id == move.location_dest_id and
                                                            ml.picking_id == move.picking_id and
                                                            not ml.lot_id and
                                                            not ml.package_id and
                                                            not ml.owner_id)
                    if to_update:
                        to_update[0].reserved_uom_qty += move.product_id.uom_id._compute_quantity(
                            missing_reserved_quantity, move.product_uom, rounding_method='HALF-UP')
                    else:
                        move_line_vals_list.append(move._prepare_move_line_vals(quantity=missing_reserved_quantity))
                assigned_moves_ids.add(move.id)
                moves_to_redirect.add(move.id)
            else:
                if float_is_zero(move.product_uom_qty, precision_rounding=move.product_uom.rounding):
                    assigned_moves_ids.add(move.id)
                elif not move.move_orig_ids:
                    if move.procure_method == 'make_to_order':
                        continue
                    # If we don't need any quantity, consider the move assigned.
                    need = missing_reserved_quantity
                    if float_is_zero(need, precision_rounding=rounding):
                        assigned_moves_ids.add(move.id)
                        continue
                    # Reserve new quants and create move lines accordingly.
                    forced_package_id = move.package_level_id.package_id or None
                    available_quantity = move._get_available_quantity(move.location_id, package_id=forced_package_id)
                    if available_quantity <= 0:
                        continue
                    taken_quantity = move._update_reserved_quantity(need, available_quantity, move.location_id, package_id=forced_package_id, strict=False)
                    if float_is_zero(taken_quantity, precision_rounding=rounding):
                        continue
                    moves_to_redirect.add(move.id)
                    if float_compare(need, taken_quantity, precision_rounding=rounding) == 0:
                        assigned_moves_ids.add(move.id)
                    else:
                        partially_available_moves_ids.add(move.id)
                else:
                    # Check what our parents brought and what our siblings took in order to
                    # determine what we can distribute.
                    # `qty_done` is in `ml.product_uom_id` and, as we will later increase
                    # the reserved quantity on the quants, convert it here in
                    # `product_id.uom_id` (the UOM of the quants is the UOM of the product).
                    available_move_lines = move._get_available_move_lines(assigned_moves_ids, partially_available_moves_ids)
                    if not available_move_lines:
                        continue
                    for move_line in move.move_line_ids.filtered(lambda m: m.reserved_qty):
                        if available_move_lines.get((move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)):
                            available_move_lines[(move_line.location_id, move_line.lot_id, move_line.result_package_id, move_line.owner_id)] -= move_line.reserved_qty
                    for (location_id, lot_id, package_id, owner_id), quantity in available_move_lines.items():
                        need = move.product_qty - sum(move.move_line_ids.mapped('reserved_qty'))
                        # `quantity` is what is brought by chained done move lines. We double check
                        # here this quantity is available on the quants themselves. If not, this
                        # could be the result of an inventory adjustment that removed totally of
                        # partially `quantity`. When this happens, we chose to reserve the maximum
                        # still available. This situation could not happen on MTS move, because in
                        # this case `quantity` is directly the quantity on the quants themselves.
                        available_quantity = move._get_available_quantity(location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=True)
                        if float_is_zero(available_quantity, precision_rounding=rounding):
                            continue
                        taken_quantity = move._update_reserved_quantity(need, min(quantity, available_quantity), location_id, lot_id, package_id, owner_id)
                        if float_is_zero(taken_quantity, precision_rounding=rounding):
                            continue
                        moves_to_redirect.add(move.id)
                        if float_is_zero(need - taken_quantity, precision_rounding=rounding):
                            assigned_moves_ids.add(move.id)
                            break
                        partially_available_moves_ids.add(move.id)
            if move.product_id.tracking == 'serial':
                move.next_serial_count = move.product_uom_qty

        self.env['stock.move.line'].create(move_line_vals_list)
        StockMove.browse(partially_available_moves_ids).write({'state': 'partially_available'})
        # StockMove.browse(assigned_moves_ids).write({'state': 'assigned'})
        if not self.env.context.get('bypass_entire_pack'):
            self.mapped('picking_id')._check_entire_pack()
        StockMove.browse(moves_to_redirect).move_line_ids._apply_putaway_strategy()
