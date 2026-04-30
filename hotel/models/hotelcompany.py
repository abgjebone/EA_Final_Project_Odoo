from odoo import models, fields

class HotelCompany(models.Model):
    _inherit = 'res.company'  

    nextgrcno = fields.Integer(string="Next GRC No", default = 1)
    nextrcno = fields.Integer(string="Next RC No", default = 1)
    nextdmno = fields.Integer(string="Next DM No", default = 1)
    nextcmno = fields.Integer(string="Next CM No", default = 1)
    nextprno = fields.Integer(string="Next PR No", default = 1)

class hoteldocuments(models.Model):
    _name = 'hotel.documents'
    _description = 'hotel documents' 
    _order = 'name'

    name = fields.Char("Document Name")
    description = fields.Char("Document Description")