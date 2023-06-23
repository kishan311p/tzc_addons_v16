from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class delivery_box_line(models.Model):
    _name = 'delivery.box.line'
    _rec_name = 'name'
    _description = 'Delivery Box Line'

    deliver_box_id = fields.Many2one('delivery.box','Box')
    weight = fields.Float('Weight (in kg)')
    qty = fields.Integer('Quantity')
    # extra_case_qty = fields.Float('Extra Case Qty')
    picking_id = fields.Many2one('stock.picking')
    delivery_package_line_id = fields.Many2one('delivery.package.line','Package Line')
    name = fields.Char('Name',default="box_",compute='update_box_name')

    @api.depends('deliver_box_id','weight','qty')
    def update_box_name(self):
        for rec in self:
            rec.name = 'Box:' + (rec.deliver_box_id.name.lower() if rec.deliver_box_id else "")+ ",Weight:" + (str(rec.weight) if rec.weight else "") + "kg,Qty:" +str((rec.qty if rec.qty else ""))

    @api.model_create_multi
    def create(self,vals):
        res = super(delivery_box_line,self).create(vals)
        # As domain is not updating so doing it from here.
        res.picking_id.delivery_package_line_ids._compute_box_domain()
        return res
