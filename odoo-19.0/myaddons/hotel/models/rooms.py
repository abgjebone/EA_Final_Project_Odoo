# -*- coding: utf-8 -*-

from odoo import models, fields, api

#roomtypes model 

class roomtypes(models.Model):
    _name = 'hotel.roomtypes'
    _description = 'hotel roomtypes master list'
    _order="name"

    name = fields.Char("Room Type Name")
    description = fields.Char("Room Type Description")
    pax = fields.Char("PAX")
    imageroom = fields.Image("Room")
    imagebathroom  = fields.Image("Bath Room")

    room_ids=fields.One2many('hotel.rooms','roomtype_id', string='Rooms')    
    dailycharges_ids=fields.One2many('hotel.dailycharges','roomtype_id', string='Daily Charges')

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,  # auto-assign current user's company
    )

#daily charges model per room type  

class dailycharges(models.Model):
    _name = 'hotel.dailycharges'
    _description = 'hotel roomtype daily charges list'

    dailyrate = fields.Float("Daily Rate", digits=(10,2))
    weekendrate = fields.Float("Weekend Rate", digits=(10,2))
    
    charge_id = fields.Many2one('hotel.charges',string="Charge Title")   

    roomtype_id = fields.Many2one('hotel.roomtypes', string="Roomtype")    

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,  # auto-assign current user's company
    )

#rooms model

class rooms(models.Model):
    _name = 'hotel.rooms'
    _description = 'hotel rooms master list'
    _order="name"

    name = fields.Char("Room No")
    description = fields.Char("Room Description")
    
    roomtype_id = fields.Many2one('hotel.roomtypes', string="Room Type")
    
    roomtypename=fields.Char("Room Type",related='roomtype_id.name')

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,  # auto-assign current user's company
    )