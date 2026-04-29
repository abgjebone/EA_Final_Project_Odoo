# -*- coding: utf-8 -*-

#guestregistration.py
import pytz
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class guestregistration(models.Model):
    _name = 'hotel.guestregistration'
    _description = 'hotel guest registration list'
    
    grc_id = fields.Integer(string="GRC #")
    room_id = fields.Many2one("hotel.rooms", string="Room No.")
    guest_id = fields.Many2one("hotel.guests", string="Guest Name")
    
    #roomname -< related fields found in the model hotel.rooms  
    roomname=fields.Char("Room No.",related='room_id.name')
    
    #roomtname <- room type name found in the model hotel.rooms 
    # also related to hotel.roomtypes
    roomtname=fields.Char("Room Type",related='room_id.roomtypename')
    
    #guestname <- related field found as a computed field called name in 
    # the model hotel.guests
    guestname=fields.Char("Guest Name",related='guest_id.name')

    datecreated_fmt = fields.Char("Date Created", compute="_compute_datecreated_fmt")

    datefromsched = fields.Datetime('Scheduled Check In', required=True, index=True, copy=False, default=fields.Datetime.now)
    datetosched = fields.Datetime('Scheduled Check Out', required=True, index=True, copy=False, default=fields.Datetime.now)

    @api.depends('create_date')
    def _compute_datecreated_fmt(self):
        for rec in self:
            rec.datecreated_fmt = rec.create_date.strftime('%Y-%m-%d %H:%M') if rec.create_date else ''


    #uncomment later for guest billing 
    #roombill_ids=fields.One2many('hotel.roombill','guestregistration_id', string='Room Charges')

    state = fields.Selection([
        ('DRAFT', 'Draft'),
        ('RESERVED', 'Reserved'),
        ('CHECKEDIN', 'Checked In'),
        ('CHECKEDOUT', 'Checked Out'),
        ('CANCELLED', 'Cancelled')
    ], string="Status", default="DRAFT")

    actualpax = fields.Integer("Actual PAX")
    details = fields.Text("Details")

    company_id = fields.Many2one(
        'res.company',
        string="Company",
        required=True,
        index=True,
        default=lambda self: self.env.company,
    )

    name= fields.Char("Guest Registration",compute='_compute_name',store=False)  
    @api.depends('room_id', 'guest_id')
    def _compute_name(self):
        for rec in self:
            rec.name= f"{rec.roomname}, {rec.guestname}"

    create_date_ampm = fields.Char(
       string="Created ON",
        compute='_compute_create_date_ampm',
        store=False  # not stored in the database
    )

    @api.depends('create_date')
    def _compute_create_date_ampm(self):
        user_tz = self.env.user.tz or 'UTC'
        for rec in self:
            if rec.create_date:
                # convert from UTC to user timezone
                dt_utc = fields.Datetime.from_string(rec.create_date)
                dt_local = pytz.utc.localize(dt_utc).astimezone(pytz.timezone(user_tz))
                # format with AM/PM
                rec.create_date_ampm = dt_local.strftime('%m-%d-%Y %I:%M %p')
            else:
                rec.create_date_ampm = ''


    datefromsched_ampm = fields.Char(
       string="Check In Date",
        compute='_compute_datefromsched_ampm',
        store=False  # not stored in the database
    )

    @api.depends('datefromsched')
    def _compute_datefromsched_ampm(self):
        user_tz = self.env.user.tz or 'UTC'
        for rec in self:
            if rec.datefromsched:
                # convert from UTC to user timezone
                dt_utc = fields.Datetime.from_string(rec.datefromsched)
                dt_local = pytz.utc.localize(dt_utc).astimezone(pytz.timezone(user_tz))
                # format with AM/PM
                rec.datefromsched_ampm = dt_local.strftime('%m-%d-%Y %I:%M %p')
            else:
                rec.datefromsched_ampm = ''

    datetosched_ampm = fields.Char(
       string="Check Out Date",
        compute='_compute_datetosched_ampm',
        store=False  # not stored in the database
    )

    @api.depends('datetosched')
    def _compute_datetosched_ampm(self):
        user_tz = self.env.user.tz or 'UTC'
        for rec in self:
            if rec.datetosched:
                # convert from UTC to user timezone
                dt_utc = fields.Datetime.from_string(rec.datetosched)
                dt_local = pytz.utc.localize(dt_utc).astimezone(pytz.timezone(user_tz))
                # format with AM/PM
                rec.datetosched_ampm = dt_local.strftime('%m-%d-%Y %I:%M %p')
            else:
                rec.datetosched_ampm = ''


    grc_id_display = fields.Char(
        string="GRC #",
        compute="_compute_grc_id_display",
        store=False
    )

    @api.depends('grc_id')
    def _compute_grc_id_display(self):
        for rec in self:
            rec.grc_id_display = str(rec.grc_id)
                
 
    @api.model
    def create(self, vals_list):
    # vals_list can be a list of dicts
        for vals in vals_list:
            if not vals.get('grc_id'):
                doctype = 'GRC'
                cmp_id = self.env.company.id

                self.env.cr.execute("SELECT * FROM public.hotel_fnGetDocno(%s,%s)", (cmp_id,doctype))
        
                # Fetch the result
            
                result = self.env.cr.fetchone()
        
                vals['grc_id'] = result[0] if result else 1

        # Call the super with the list
        records = super().create(vals_list)
        return records
   
    def action_reserve(self):
        for rec in self:
            if not (rec.guest_id):
                raise ValidationError('Please supply a valid Guest Name.')

            elif not(rec.roomname):
                raise ValidationError('Please supply a valid Room Number.')
            elif not(rec.datefromsched):
                raise ValidationError('Please supply a valid Date from Schedule.')
            elif not(rec.datetosched):
                raise ValidationError('Please supply a valid Date to Schedule.')
            elif (rec.datetosched<=rec.datefromsched):
                raise ValidationError('Invalid Date Range.')
            else:
                rec.state = "RESERVED"
    
    def action_checkin(self):
        for rec in self:
            if not (rec.guest_id):
                raise ValidationError('Please supply a valid Guest Name.')

            elif not(rec.roomname):
                raise ValidationError('Please supply a valid Room Number.')
            elif not(rec.datefromsched):
                raise ValidationError('Please supply a valid Date from Schedule.')
            elif not(rec.datetosched):
                raise ValidationError('Please supply a valid Date to Schedule.')
            elif (rec.datetosched<=rec.datefromsched):
                raise ValidationError('Invalid Date Range.')
            else:
                rec.state = "CHECKEDIN"

    def action_checkout(self):
        for rec in self:
            if (rec.state=="CHECKEDIN"):
                rec.state = "CHECKEDOUT"
            else:
                raise ValidationError('Guest is not CHECKED IN.')

    def action_cancel(self):
        for rec in self:
            if (rec.state=="CHECKEDIN"):
                raise ValidationError('Guest is not CHECKED IN.')
            else:
                rec.state = "CANCELLED"
            
    def action_mark_draft(self):
        for rec in self:
            rec.state = "DRAFT"       
                    
