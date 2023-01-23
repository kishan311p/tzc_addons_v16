from odoo import _, api, fields, models, tools

class kits_double_move_log(models.Model):
    _name = 'kits.double.move.log'
    _rec_name = 'product_id'
    _description = 'Kits Double Move Log'

    created_date = fields.Datetime('Date')
    user_id = fields.Many2one('res.users','User Name')
    product_id = fields.Many2one('product.product','Product')
    picking_id = fields.Many2one('stock.picking','Delivery Order')
    other_move_ids = fields.Many2many('kits.stock.move',string='Move')

    def genarete_double_move_log(self,product_id,picking_id,other_moves):
        log_ids  =self.search([('product_id','=',product_id.id),('picking_id','=',picking_id.id)])
        if not log_ids:
            kits_other_moves = self.env['kits.stock.move'].get_kits_move(other_moves)
            self.env['kits.double.move.log'].create({
                'created_date' : fields.Date.today(),
                'user_id' : self.env.uid,
                'product_id' : product_id.id,
                'picking_id' : picking_id.id,
                'other_move_ids' : [(6,0,kits_other_moves)]
            })
        else:
            for log_id in log_ids :
                kits_other_moves = self.env['kits.stock.move'].get_kits_move(other_moves)
                if log_id.other_move_ids.ids != other_moves:
                    log_id.other_move_ids = [(6,0,kits_other_moves)]  
                else:
                    self.env['kits.double.move.log'].create({
                        'created_date' : other_moves[0].date,
                        'user_id' : self.env.uid,
                        'product_id' : product_id.id,
                        'picking_id' : picking_id.id,
                        'other_move_ids' : [(6,0,kits_other_moves)]                        
                    })

