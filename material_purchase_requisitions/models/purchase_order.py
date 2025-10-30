# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import pytz
import urllib.parse


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    custom_requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string='Requisitions',
        copy=False
    )

    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    vehicle_name = fields.Char(string='Vehicle')
    vin_sn = fields.Char(string='VIN/SN')

    # def action_send_whatsapp_pdf(self):
    #     self.ensure_one()
    #
    #     # Determine which report to use
    #     if self.state in ['draft', 'purchase']:
    #         report_ref = 'purchase.report_purchase_quotation'  # RFQ report XML ID
    #     elif self.state == 'purchase':
    #         report_ref = 'purchase.action_report_purchase_order'  # PO report XML ID
    #     else:
    #         raise UserError("WhatsApp sending is allowed only for RFQ or Purchase Order.")
    #
    #     # Fetch report
    #     report = self.env.ref(report_ref)
    #
    #     # Generate the PDF
    #     pdf_content, _ = report._render_qweb_pdf(self.id)
    #
    #     # Optional: Save or attach to WhatsApp message
    #     attachment = self.env['ir.attachment'].create({
    #         'name': f'{self.name}.pdf',
    #         'type': 'binary',
    #         'datas': base64.b64encode(pdf_content),
    #         'res_model': 'purchase.order',
    #         'res_id': self.id,
    #         'mimetype': 'application/pdf'
    #     })
    #
    #     # Logic to send via WhatsApp (depending on your WhatsApp integration)
    #     # e.g. self.partner_id.send_whatsapp_message(attachment)
    #
    #     return {
    #         'effect': {
    #             'fadeout': 'slow',
    #             'message': f'WhatsApp message sent successfully for {self.name}',
    #             'type': 'rainbow_man',
    #         }
    #     }

    def action_send_whatsapp_pdf(self):
        for rec in self:
            if not rec.partner_id or not rec.partner_id.mobile:
                raise UserError("No mobile number found for this vendor.")

            # Format mobile number (UAE format)
            mobile = rec.partner_id.mobile.strip().replace(' ', '').replace('+', '')
            if mobile.startswith('0'):
                mobile = mobile[1:]
            if not mobile.startswith('971'):
                mobile = '971' + mobile

            # Choose correct report based on state
            if rec.state == 'draft':
                report = self.env.ref('purchase.report_purchase_quotation')
                print(report,'ffffffffffff')
                report_name = 'RFQ'
            elif rec.state == 'purchase':
                report = self.env.ref('purchase.action_report_purchase_order')
                print(report,'tttttttttt')
                report_name = 'Purchase_Order'
            else:
                raise UserError("Only RFQ or Purchase Order can be sent via WhatsApp.")


            # ✅ Render PDF
            pdf_content, _ = report._render_qweb_pdf(rec.id)
            print(pdf_content,'contenttttttttt')

            # Create attachment with access token
            attachment = self.env['ir.attachment'].create({
                'name': f"{report_name}_{rec.name}.pdf",
                'type': 'binary',
                'datas': base64.b64encode(pdf_content),
                'res_model': 'purchase.order',
                'res_id': rec.id,
                'public': True,
            })

            # Generate public link
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            report_url = f"{base_url}/web/content/{attachment.id}?download=true"

            # Prepare WhatsApp message
            message = f"""Dear {rec.partner_id.name},

    Thank you for your business.

    📄 Document: {report_name.replace('_', ' ')}
    🧾 Reference: {rec.name}
    📅 Date: {rec.date_order.strftime('%d-%b-%Y') if rec.date_order else 'N/A'}

    You can download the document here:
    🔗 {report_url}

    Best regards,  
    Purchase Department"""

            encoded_msg = urllib.parse.quote(message)
            whatsapp_url = f"https://web.whatsapp.com/send?phone={mobile}&text={encoded_msg}"

            return {
                'type': 'ir.actions.act_url',
                'url': whatsapp_url,
                'target': 'new',
            }

    # department = fields.Selection([
    #     ('labour', 'Labour'),
    #     ('parts', 'Parts'),
    #     ('material', 'Material'),
    #     ('lubricant', 'Lubricant'),
    #     ('sublets', 'Sublets'),
    #     ('paint_material', 'Paint Material'),
    #     ('tyre', 'Tyre'),
    # ], string="Department")

    # function added on july31 for fetching details from material purchase

    # @api.model
    # def default_get(self, fields):
    #     res = super().default_get(fields)
    #     requisition_id = self.env.context.get('default_custom_requisition_id')
    #     if requisition_id:
    #         requisition = self.env['material.purchase.requisition'].browse(requisition_id)
    #         order_lines = []
    #         for line in requisition.requisition_line_ids:
    #             seller = line.product_id._select_seller()
    #             order_lines.append((0, 0, {
    #                 'product_id': line.product_id.id,
    #                 'name': line.description or line.product_id.name,
    #                 'product_qty': line.qty,
    #                 'product_uom': line.uom.id,
    #                 # 'date_planned': fields.Date.today(),
    #                 # 'price_unit': seller.price if seller else line.product_id.standard_price,
    #                 'price_unit': line.cost_price,
    #                 'custom_requisition_line_id': line.id,
    #             }))
    #         res['order_line'] = order_lines
    #     return res
# uom issue corrected
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        requisition_id = self.env.context.get('default_custom_requisition_id')
        if requisition_id:
            requisition = self.env['material.purchase.requisition'].browse(requisition_id)
            order_lines = []
            for line in requisition.requisition_line_ids:
                seller = line.product_id._select_seller()
                order_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': line.description or line.product_id.name,
                    'product_qty': line.qty,
                    'product_uom': line.uom.id,
                    # 'product_uom': line.uom_id.id if line.uom_id else line.product_id.uom_po_id.id,
                    'price_unit': line.cost_price,
                    'custom_requisition_line_id': line.id,
                }))
            res['order_line'] = order_lines
        return res







class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'
    
    custom_requisition_line_id = fields.Many2one(
        'material.purchase.requisition.line',
        string='Requisitions Line',
        copy=False
    )

    part_type = fields.Selection([
        ('after_market', 'After Market'),
        ('genuine', 'Genuine'),
        ('used', 'Used'),
    ], string='Part Type', default='')

    part_no = fields.Char(string="Part Number")

    