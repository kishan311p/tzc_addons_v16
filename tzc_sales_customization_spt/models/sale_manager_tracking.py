from odoo import api,models,fields,_

class sale_manager_tracking(models.Model):
    _name = 'sale.manager.tracking'
    _rec_name = 'order_id'

    order_id = fields.Many2one('sale.order','Order')
    create_date = fields.Datetime('Date')
    user = fields.Many2one('res.users','User')
    user_id = fields.Many2one('res.users','From Sales Person')
    new_user_id = fields.Many2one('res.users','To Sales Person')
    sale_manager_id = fields.Many2one('res.users','From Sales Manager')                                      
    new_sale_manager_id = fields.Many2one('res.users','To Sales Manager')
   