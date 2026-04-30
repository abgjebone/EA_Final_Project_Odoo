import pytz
import logging
from datetime import datetime
import io
import base64
import xlsxwriter

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

class HotelTransactionDashboard(models.Model):
    _name = 'hotel.transaction.dashboard'
    _description = 'Hotel Transaction Dashboard'

    # 1. Identity and Context
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    
    # 2. Filter Parameters
    date_from = fields.Date(string='Start Date', default=fields.Date.context_today, required=True)
    date_to = fields.Date(string='End Date', default=fields.Date.context_today, required=True)
    
    datefrom_fmt = fields.Char(
        string="Date From",
        compute='_compute_datefrom_fmt',
        store=False  # not stored in the database
    )

    @api.depends('date_from')
    def _compute_datefrom_fmt(self):
        user_tz = self.env.user.tz or 'UTC'
        for record in self:
            if record.date_from:
                # convert from UTC to user timezone
                dt_utc = fields.Datetime.from_string(str(record.date_from))
                dt_local = pytz.utc.localize(dt_utc).astimezone(pytz.timezone(user_tz))
                # format with AM/PM
                record.datefrom_fmt = dt_local.strftime('%m-%d-%Y')
            else:
                record.datefrom_fmt = ''
    
    report_line_ids = fields.Many2many(
        'hotel.transaction_report', 
        compute='_compute_report_lines',
        compute_sudo=True,
        string="Transaction Results"
    )

    @api.depends('date_from', 'date_to')
    def _compute_report_lines(self):
        for record in self:
            # We fetch all rows currently available in the SQL view.
            # The view is updated whenever 'action_refresh_results' is clicked.
            record.report_line_ids = self.env['hotel.transaction_report'].sudo().search([])

    def hotel_transaction_report_action(self, page_size=65):
        self.ensure_one()
        lines = self.report_line_ids
        return [lines[i:i + page_size] for i in range(0, len(lines), page_size)]

    def hotel_transaction_report_pages(self, lines_per_page=65):
        """Return transaction report lines split into pages.
        
        The report `hoteltransaction.xml` calls `o.hotel_transaction_report_pages(65)` 
        to paginate results across multiple PDF pages.
        """
        self.ensure_one()
        lines = self.report_line_ids.sorted('dateapplied') if self.report_line_ids else self.env['hotel.transaction_report']
        pages = []
        total = len(lines)
        if total == 0:
            return pages
        for i in range(0, total, int(lines_per_page)):
            pages.append(lines[i:i + int(lines_per_page)])
        return pages

    def action_refresh_results(self):
        self.ensure_one()
        
        # Call your updated stored procedure with the company ID
        # Note: Use self.env.cr.execute for direct procedure calls
        self.sudo().env.cr.execute(
            "CALL create_hotel_transaction_report_view(%s, %s, %s)", 
            (self.date_from, self.date_to, self.company_id.id)
        )
        
        # IMPORTANT: We must invalidate the cache for the report model 
        # so Odoo fetches the fresh data from the newly created SQL View.
        self.env['hotel.transaction_report'].sudo().invalidate_model()

        # Reload the client UI to show the new data
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_export_excel(self):
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet('Transactions')

        # Formatting
        title_style = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
        header_style = workbook.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 'border': 1})
        text_style = workbook.add_format({'border': 1})
        money_style = workbook.add_format({'num_format': '#,##0.00', 'border': 1})
        date_style = workbook.add_format({'num_format': 'mm-dd-yyyy', 'border': 1})

        # Report Header - Extended to column I now
        sheet.merge_range('A1:I1', f'Hotel Transaction Report: {self.date_from} to {self.date_to}', title_style)

        # Updated Column Headers
        headers = [ 'Date', 'Doc.', 'No.', 'Guest Name', 'Room', 'Room Type', 'Account Title', 'Debit', 'Credit' ]
        
        # Adjust Column Widths
        sheet.set_column('A:A', 12) # Date
        sheet.set_column('B:C', 12) # Doc & No.
        sheet.set_column('D:D', 35) # Guest Name
        sheet.set_column('E:E', 10) # Room
        sheet.set_column('F:F', 18) # Room Type (Added)
        sheet.set_column('G:G', 25) # Account Title
        sheet.set_column('H:I', 14) # Debit & Credit

        for col, label in enumerate(headers):
            sheet.write(2, col, label, header_style)

        # Write Data Lines
        row = 3
        for line in self.report_line_ids:
            sheet.write(row, 0, line.dateapplied or '', date_style)
            sheet.write(row, 1, line.doc or '', text_style)
            sheet.write(row, 2, line.documentno or '', text_style)
            sheet.write(row, 3, line.guestname or '', text_style)
            sheet.write(row, 4, line.roomname or '', text_style)
            sheet.write(row, 5, line.roomtypename or '', text_style) # Added: Room Type
            sheet.write(row, 6, line.accounttitle or '', text_style)
            sheet.write(row, 7, line.debit_amt or 0.0, money_style)
            sheet.write(row, 8, line.credit_amt or 0.0, money_style)
            
            row += 1

        workbook.close()
        output.seek(0)
        
        file_name = f'Transactions_{self.date_from}_{self.date_to}.xlsx'
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(output.read()).decode('utf-8'),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })
        output.close()

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }

class HotelTransactionReport(models.Model):
    _name = 'hotel.transaction_report'
    _description = 'Hotel Transaction Analysis'
    _auto = False  # Tells Odoo NOT to create a table in the database
    _order = 'accounttitle, dateapplied'

    # Mapping fields to the SQL view columns
    # id = fields.Integer(readonly=True)

    
    grc_id = fields.Many2one('hotel.guestregistration', string="Registration", readonly=True)
    doc = fields.Char(string="Doc.", readonly=True)
    dateapplied = fields.Datetime(string="Date", readonly=True)
    documentno = fields.Char(string="No.", readonly=True)
    details = fields.Text(string="Details", readonly=True)
    accounttitle = fields.Char(string="Account/Charge", readonly=True)
    state = fields.Char(string="Status", readonly=True)
    debit_amt = fields.Float(string="Debit", readonly=True, digits=(12, 2))
    credit_amt = fields.Float(string="Credit", readonly=True, digits=(12, 2))
    guestname = fields.Char(string="Guest Name", readonly=True)
    roomname = fields.Char(string="Room", readonly=True)
    roomtypename = fields.Char(string="Room Type", readonly=True)
    staystatus = fields.Char(string="Stay Status", readonly=True)
    company_id = fields.Many2one('res.company', string="Company", readonly=True)


    line_no = fields.Integer(string='Line #',readonly=True)  # This will be computed in SQL, not in Python

    def init(self):
        """
        This method runs when the module is installed/updated.
        It ensures the view exists even before the user clicks 'Refresh'.
        """
        try:
            default_company = self.env.company.id if self.env.company else 1
            # Initialize with a broad range so the dashboard is populated on first open.
            self.sudo().env.cr.execute(
                "CALL create_hotel_transaction_report_view(%s, %s, %s)", 
                ('1900-01-01', '2999-12-31', default_company)
            )
        except Exception as e:
            # If the stored procedure fails, continue anyway
            # The view will be created when the user clicks "Refresh Data"
            _logger.warning(f"Failed to initialize transaction report view: {e}")

    dateapplied_ampm = fields.Char(
       string="Date",
        compute='_compute_dateapplied_ampm',
        store=False  # not stored in the database
    )

    @api.depends('dateapplied')
    def _compute_dateapplied_ampm(self):
        user_tz = self.env.user.tz or 'UTC'
        for rec in self:
            if rec.dateapplied:
                # convert from UTC to user timezone
                dt_utc = fields.Datetime.from_string(rec.dateapplied)
                dt_local = pytz.utc.localize(dt_utc).astimezone(pytz.timezone(user_tz))
                # format with AM/PM
                rec.dateapplied_ampm = dt_local.strftime('%m-%d-%Y %I:%M %p')
            else:
                rec.dateapplied_ampm = ''

                
