from odoo.exceptions import UserError
from odoo import models, fields, api, _
import base64

class EmailGuestBillWizard(models.TransientModel):
    _name = 'hotel.email.guestbill.wizard' 
    _description = 'Email Guest Bill Wizard'

    email_to = fields.Char(string="Recipient Email", required=True, default=lambda self: self._get_default_email_to())

    def _get_default_email_to(self):
        res_id = self.env.context.get('default_res_id') or self.env.context.get('active_id')
        if res_id:
            guestreg = self.env['hotel.guestregistration'].browse(res_id).exists()
            return guestreg.guest_id.email or ''
        return ''
    
    subject = fields.Char(string="Subject", required=True, default="Updated Bill")

    body = fields.Html(
        string="Message",
        default="""Dear Guest,<br/><br/>Attached is the updated hotel room bill for your perusal.<br/><br/> Please settle existing balances if you have one and disregard this message if it has already been settled.<br/><br/>Sincerely,<br/><br/><br/>Hotel Management"""
    )

    res_id = fields.Integer(string="Record ID", default=lambda self: self.env.context.get('default_res_id') or self.env.context.get('active_id'))

    def action_send_email(self):
        self.ensure_one()

        registration = self.env['hotel.guestregistration'].browse(self.res_id).exists()
        if not registration:
            raise UserError(_('Please open the guest registration again and retry sending the bill.'))

        report_action = self.env.ref('hotel.action_report_bill2').sudo()
        pdf_content, content_type = report_action._render_qweb_pdf(registration.ids)

        # 2. Create Attachment (Linked to the Guest Registration record)
        attachment_id = self.env['ir.attachment'].create({
            'name': 'GuestBill_%s.pdf' % self.res_id,
            'type': 'binary',
            'datas': base64.b64encode(pdf_content).decode('utf-8'),
            'res_model': 'hotel.guestregistration',
            'res_id': self.res_id,
            'mimetype': 'application/pdf',
        })

        # 3. Create and Send Mail
        mail_values = {
            'subject': self.subject,
            'body_html': self.body,
            'email_to': self.email_to,
            'email_from': self.env.user.email_formatted or self.env.user.email or 'noreply@yourhotel.com',
            'attachment_ids': [(6, 0, [attachment_id.id])],
            'model': 'hotel.guestregistration',
            'res_id': self.res_id,
        }

        self.env['mail.mail'].create(mail_values).send()