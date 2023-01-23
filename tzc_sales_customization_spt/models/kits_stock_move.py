from odoo import _, api, fields, models, tools
class kits_stock_move(models.Model):
    _name = 'kits.stock.move'
    _rec_name = 'name'
    _description = "Kits Stock Move"

    name = fields.Char('Description')
    move_id = fields.Integer('Move Id')
    product_id = fields.Many2one('product.product','Product')
    quantity_done = fields.Float('Done')
    product_uom_qty = fields.Float('Demand')
    status = fields.Char('Status')
    company_id = fields.Many2one('res.company','Company')
    date = fields.Datetime('Date')
    date_expected = fields.Datetime('Expected Date')
    location_dest_id = fields.Many2one('stock.location','Dest Location')
    location_id = fields.Many2one('stock.location','Location')
    product_uom = fields.Many2one('uom.uom','UOM')
    procure_method = fields.Char('Supply Method')

    def get_kits_move(self,moves_ids):
        move_list = []
        kits_move_ids = self.search([('move_id','in',moves_ids.ids)])
        move_list.extend(kits_move_ids.ids)
        create_move = moves_ids.filtered(lambda kits: kits.id not in  kits_move_ids.mapped('move_id'))
        for move in create_move:
            move_id = self.create({
                'move_id': move.id,
                'product_id': move.product_id.id,
                'quantity_done': move.quantity_done,
                'product_uom_qty': move.product_uom_qty,
                'status': move.state,
                'company_id': move.company_id.id,
                'date': move.date,
                'date_expected': move.date_expected,
                'location_dest_id': move.location_dest_id.id,
                'location_id': move.location_id.id,
                'product_uom': move.product_uom.id,
                'procure_method': move.procure_method,
                'name': move.name,
                
            })
            move_list.append(move_id.id)
        return move_list
