from odoo import api, fields, models, _

class kits_multi_website_address(models.Model):
    _name = "kits.multi.website.address"

    # address_type = fields.Selection([('delivery','Delivery Address'),('invoice','Invoice Address')],string="Address Type")
    name= fields.Char('Name')
    street = fields.Char("Street")
    street2 = fields.Char("Street2")
    city = fields.Char("City")
    zip = fields.Char("Zip")
    state_id = fields.Many2one("res.country.state", "State")
    country_id = fields.Many2one("res.country", "Country",store=True)
    customer_id = fields.Many2one("kits.multi.website.customer","Customer")
    is_delivery_address_default = fields.Boolean("Preferred Delivery Default Address")
    is_invoice_address_default = fields.Boolean("Preferred Invoice Default Address")
    phone = fields.Char('Phone No.')

    def name_get(self):
        result = []
        for record in self:
            name = ''
            name_list = []
            if record.customer_id.display_name:
                name = name+'%s' if not name else name+','+'%s'
                name_list.append(record.customer_id.display_name)
            if record.street:
                name = name+'%s' if not name else name+','+'%s'
                name_list.append(record.street)
            if record.street2:
                name = name+'%s' if not name else name+','+'%s'
                name_list.append(record.street2)
            if record.city:
                name = name+'%s' if not name else name+','+'%s'
                name_list.append(record.city)
            if record.zip:
                name = name+'%s' if not name else name+','+'%s'
                name_list.append(record.zip)
            if record.state_id.name:
                name = name+'%s' if not name else name+','+'%s'
                name_list.append(record.state_id.name)
            if record.country_id.name:
                name = name+'%s' if not name else name+','+'%s'
                name_list.append(record.country_id.name)
            name = name%tuple(name_list)
            result.append((record.id,name))
        return result


    def write(self, vals):
        for record in self:
            if vals.get('is_delivery_address_default',False):
                self.search([('customer_id','=',record.customer_id.id),('is_delivery_address_default','=',True)]).write({'is_delivery_address_default':False})
            if  vals.get('is_invoice_address_default',False):
                self.search([('customer_id','=',record.customer_id.id),('is_invoice_address_default','=',True)]).write({'is_invoice_address_default':False})

        return super(kits_multi_website_address,self).write(vals)
