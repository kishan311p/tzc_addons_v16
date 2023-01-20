from odoo import models,fields,api,_

class stock_move_line(models.Model):
    _inherit = 'stock.move.line'

    attach_file_name = fields.Char(compute="_compute_attach_file_name",string="Attachment File Name")
    
    @api.depends('reference')
    def _compute_attach_file_name(self):
        for rec in self:
            import_id = False
            if ':' in rec.reference:
                reference = rec.reference.split(':')
                import_id = self.env['product.import.spt'].search([('name','=',reference[1])]) if reference[0] == 'INV' else ''
            else:
                reference = rec.reference.split('/')
                if len(reference)==4 and reference[0]== 'IP' and len(reference[1])==4:
                    import_id = self.env['product.import.spt'].search([('name','=', rec.reference)]) 
            rec.attach_file_name = import_id.attach_file_name if import_id else ''

class stock_move(models.Model):
    _inherit = 'stock.move'

    product_import_id = fields.Many2one('product.import.spt','Product Import') 
