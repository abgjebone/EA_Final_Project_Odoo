# -*- coding: utf-8 -*-

#guestregistration.py
import pytz
from datetime import datetime

from odoo import _, models, fields, api
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
    guestname=fields.Char(string="Created by",
        related='create_uid.login',
        store=False,
        readonly=True    
    )

    creator_login = fields.Char("Created By", compute="_compute_creator_login")

    datecreated_fmt = fields.Char("Date Created", compute="_compute_datecreated_fmt")

    datefromsched = fields.Datetime('Scheduled Check In', required=True, index=True, copy=False, default=fields.Datetime.now)
    datetosched = fields.Datetime('Scheduled Check Out', required=True, index=True, copy=False, default=fields.Datetime.now)

    @api.depends('create_date')
    def _compute_datecreated_fmt(self):
        for rec in self:
            rec.datecreated_fmt = rec.create_date.strftime('%Y-%m-%d %H:%M') if rec.create_date else ''


    #uncomment later for guest billing 
    roombill_ids=fields.One2many('hotel.roombill','guestregistration_id', string='Room Charges')
    total_amount_applied = fields.Float(
        string='Total Balance',
        compute='_compute_total_amount_applied',
        store=False,
        digits=(12, 2),
    )

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

    @api.depends('roombill_ids.diffamt')
    def _compute_total_amount_applied(self):
        for rec in self:
            rec.total_amount_applied = sum(rec.roombill_ids.mapped('diffamt')) if rec.roombill_ids else 0.0
                
 
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
   
    # Helper validations and DB call wrappers to avoid repetition
    def _validate_basic(self):
        self.ensure_one()
        if not self.guest_id:
            raise ValidationError(_('Please supply a valid guest.'))
        if not self.room_id:
            raise ValidationError(_('Please supply a valid Room Number.'))
        if not self.datefromsched:
            raise ValidationError(_('Please supply a valid Date From Schedule.'))
        if not self.datetosched:
            raise ValidationError(_('Please supply a valid Date To Schedule.'))
        if self.datetosched <= self.datefromsched:
            raise ValidationError(_('Invalid Date Range: Check-out must be after Check-in.'))

    def _validate_reserve(self):
        self._validate_basic()
        now = fields.Datetime.now()
        if now > self.datefromsched:
            raise ValidationError(_('Cannot reserve past the scheduled check-in date.'))
        if now >= self.datetosched:
            raise ValidationError(_('Cannot reserve past the scheduled check-out date.'))

    def _validate_checkin(self):
        self._validate_basic()
        # Compare dates in user's timezone and allow check-in on the scheduled day.
        user_tz = self.env.user.tz or 'UTC'
        now_dt = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        for rec in self:
            # convert scheduled datetimes to user tz
            scheduled_from = fields.Datetime.context_timestamp(rec, rec.datefromsched) if rec.datefromsched else None
            scheduled_to = fields.Datetime.context_timestamp(rec, rec.datetosched) if rec.datetosched else None
            # compare only dates: allow check-in on the same calendar day
            if scheduled_from and now_dt.date() < scheduled_from.date():
                raise ValidationError(_('Cannot check in before the scheduled check-in date.'))
            if scheduled_to and now_dt.date() >= scheduled_to.date():
                raise ValidationError(_('Cannot check in past the scheduled check-out date.'))

    def _check_registration_conflict(self):
        pkid = self.id
        cmp_id = self.env.company.id
        
        
        self.env.cr.execute("SELECT rid, rmessage FROM public.hotel_fncheck_registrationconflict(%s,%s)", (pkid, cmp_id)
        )
        return self.env.cr.fetchone()

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

    def action_refresh_guest_list(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_check_availability(self):
        self.ensure_one()
        # Basic validation
        self._validate_basic()

        # DB conflict check
        result = self._check_registration_conflict()
        if result:
            if result[0] == 0:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': ("Availability Check"),
                        'message': ("The room schedule is available for the selected dates."),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise ValidationError(result[1])
        return True

    def action_reserve(self):
        self.ensure_one()
        # validation including reservation-specific time checks
        self._validate_reserve()

        result = self._check_registration_conflict()
        if result and result[0] == 0:
            self.state = "RESERVED"
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Availability Check',
                    'message': 'The room is RESERVED for the selected dates.',
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                }
            }
        else:
            raise ValidationError(result[1] if result else "Schedule Conflict. Please check room availability for the selected dates.")

    def action_checkin(self):
        for rec in self:
            rec._validate_checkin()
            result = rec._check_registration_conflict()
            if result and result[0] == 0:
                now = fields.Datetime.now()
                if rec.datefromsched != now:
                    rec.datefromsched = now

                self.env.cr.execute("SELECT * FROM public.hotel_fnCheckin(%s,%s)", (rec.id, self.env.company.id))
                rec.state = "CHECKEDIN"
                # consume any DB output
                self.env.cr.fetchall()

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': 'Check In',
                        'message': 'Guest has been CHECKED IN successfully.',
                        'type': 'success',
                        'sticky': False,
                        'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                    }
                }
            else:
                raise ValidationError(result[1] if result else "Schedule Conflict. Please check room availability for the selected dates.")

    def get_roombill_pages(self, lines_per_page=65):
        """Return the room bill lines split into pages of at most `lines_per_page`.

        The report `guestbill2.xml` calls `o.get_roombill_pages(65)` and expects
        a sequence of page-sized lists/recordsets so QWeb can iterate and render
        each page. This helper keeps the logic in Python and avoids template-side
        slicing or errors when there are many bill lines.
        """
        self.ensure_one()
        # Order bills in a deterministic way (by id). Use recordset slicing which
        # QWeb can iterate over.
        lines = self.roombill_ids.sorted('id') if self.roombill_ids else self.env['hotel.roombill']
        pages = []
        total = len(lines)
        if total == 0:
            return pages
        for i in range(0, total, int(lines_per_page)):
            pages.append(lines[i:i + int(lines_per_page)])
        return pages

    def action_print_bill(self):
        self.ensure_one()
        return self.env.ref('hotel.action_report_bill').report_action(self)

    def action_print_bill_multipage(self):
        self.ensure_one()
        return self.env.ref('hotel.action_report_bill2').report_action(self)
