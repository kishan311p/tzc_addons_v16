from odoo import models,fields,api,_

class kits_search_sale_state(models.TransientModel):
    _name = 'kits.search.sale.order.status'
    _description = 'Search Sale Order Status'

    name = fields.Char('Name')
    tech_name = fields.Char('Technical Name')

class kits_search_sale_order_wizard(models.TransientModel):
    _name = "kits.search.sale.order.wizard"
    _description = "Search Sale Order Wizard"

    def _get_deafult_state(self):
        status_obj = self.env['kits.search.sale.order.status']
        statuses = self.env['sale.order']._fields['state'].selection
        [status_obj.create({'name':status[1],'tech_name':status[0]}) for status in statuses if not status_obj.search([('tech_name','=',status[0])])]
        return False

    customer_ids = fields.Many2many('res.partner','kits_search_sale_order_res_partner_rel','kits_search_sale_order_id','res_partner_id','Customers')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    state = fields.Many2many('kits.search.sale.order.status','kits_search_sale_order_state_rel','kits_search_sale_order_id','state_id','Order Status',default=_get_deafult_state)


    def action_search_orders(self):
        domain = []
        if self.start_date:
            domain.append(('date_order','>=',self.start_date))
        if self.end_date:
            domain.append(('date_order','<=',self.end_date))
        if self.state:
            status = self.state.mapped('tech_name')
            domain.append(('state','in',status))
        if self.customer_ids:
            domain.append(('partner_id','in',self.customer_ids.ids))
        return {
            'name':'Orders',
            'type':'ir.actions.act_window',
            'res_model':'sale.order',
            'view_mode':'tree,kanban,form,calendar,pivot,graph,activity',
            'domain':domain,
            'target':'self',
        }
