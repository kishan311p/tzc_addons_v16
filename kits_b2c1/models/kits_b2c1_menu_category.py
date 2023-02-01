from odoo import api, fields, models, _

class kits_b2c1_menu_category(models.Model):
    _name = "kits.b2c1.menu.category"
    _order = "sequence"
    
    name = fields.Char("Name")
    sequence = fields.Integer()
    