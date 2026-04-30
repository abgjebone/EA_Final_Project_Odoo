# -*- coding: utf-8 -*-

from odoo import models, fields, api

class hoteldocuments(models.Model):
    _name = 'hotel.documents'
    _description = 'hotel documents'
    _order = "name"
    
    name = fields.Char("Document Name")
    description = fields.Char("Document Description")
    # nextno = fields.Integer("Next Value")
    # roombill_ids=fields.One2many('hotel.roombill','document_id', string='Room Bills')      
