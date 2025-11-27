# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
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
    car_id = fields.Many2one('vehicle.details', string="Car ID", store=True)
    vehicle_name = fields.Char(string='Vehicle')
    vin_sn = fields.Char(string='VIN/SN')

    @api.onchange('car_id')
    def _onchange_car_id(self):
        if self.car_id:
            self.vin_sn = self.car_id.vin_sn
            self.vehicle_name = self.car_id.title_en
        else:
            self.vin_sn = False
            self.vehicle_name = False

    # code by arvind
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
                report_ref = 'purchase.report_purchase_quotation'  # RFQ report
                report_name = 'RFQ'
            elif rec.state == 'purchase':
                report_ref = 'purchase.action_report_purchase_order'  # Purchase Order report
                report_name = 'Purchase_Order'
            else:
                raise UserError("Only RFQ or Purchase Order can be sent via WhatsApp.")

            # ✅ Render PDF using same style as account.invoice example
            pdf_content, _ = self.env['ir.actions.report'].with_context(force_report_rendering=True)._render_qweb_pdf(
                report_ref, res_ids=rec.id
            )

            # Create attachment
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

#     def button_confirm(self):
#         res = super(PurchaseOrder, self).button_confirm()
#
#         for rec in self:
#             rec.state = 'to approve'
#             manager_group = self.env.ref('purchase.group_purchase_manager', raise_if_not_found=False)
#             if not manager_group or not manager_group.users:
#                 raise UserError(_("No purchase manager found to notify."))
#
#             manager_employee = self.env['hr.employee'].search([
#                 ('user_id', 'in', manager_group.users.ids),
#                 ('work_phone', '!=', False)
#             ], limit=1)
#
#             if not manager_employee:
#                 raise UserError(_("Purchase Manager has no work phone number set."))
#
#             mobile = manager_employee.work_phone.strip().replace(' ', '').replace('+', '')
#             if mobile.startswith('0'):
#                 mobile = mobile[1:]
#             if not mobile.startswith('971'):
#                 mobile = '971' + mobile
#
#             # 🔹 Build correct Odoo form view link
#             base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
#             approval_link = f"{base_url}/web#id={rec.id}&model=purchase.order&view_type=form"
#
#             message = f"""Dear Manager,
#
# 🧾 A new Purchase Order request requires your approval.
#
# 📄 Reference: {rec.name}
# 👤 Requested by: {self.env.user.name}
# 📅 Date: {rec.date_order.strftime('%d-%b-%Y') if rec.date_order else 'N/A'}
#
# Please review and approve using the link below:
# 🔗 {approval_link}
#
# Best regards,
# Purchase Department"""
#
#             encoded_msg = urllib.parse.quote(message)
#             whatsapp_url = f"https://web.whatsapp.com/send?phone={mobile}&text={encoded_msg}"
#             return {
#                 'type': 'ir.actions.act_url',
#                 'url': whatsapp_url,
#                 'target': 'new',
#             }
#
#         return res

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()

        for rec in self:
            rec.state = 'to approve'

            #  UPDATE PICKING FIELDS
            if rec.picking_ids:
                rec.picking_ids.write({
                    'car_id': rec.car_id.id,
                    'vehicle_name': rec.vehicle_name,
                    'vin_sn': rec.vin_sn,
                })
            #END BLOCK

            # 🔹 Get Purchase Manager group
            manager_group = self.env.ref('purchase.group_purchase_manager', raise_if_not_found=False)
            if not manager_group or not manager_group.users:
                raise UserError(_("No purchase manager found to notify."))

            # 🔹 Find one manager with phone number (for WhatsApp)
            manager_employee = self.env['hr.employee'].search([
                ('user_id', 'in', manager_group.users.ids),
                ('work_phone', '!=', False)
            ], limit=1)

            if not manager_employee:
                raise UserError(_("Purchase Manager has no work phone number set."))

            # 🔹 Prepare WhatsApp number
            mobile = manager_employee.work_phone.strip().replace(' ', '').replace('+', '')
            if mobile.startswith('0'):
                mobile = mobile[1:]
            if not mobile.startswith('971'):
                mobile = '971' + mobile

            # 🔹 Build Odoo record link
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            approval_link = f"{base_url}/web#id={rec.id}&model=purchase.order&view_type=form"

            # 🔹 WhatsApp message
            message = f"""Dear Manager,

A new Purchase Order requires your approval.

Reference: {rec.name}
Requested by: {self.env.user.name}
Date: {rec.date_order.strftime('%d-%b-%Y') if rec.date_order else 'N/A'}

Please review and approve using the link below:
{approval_link}

Best regards,
Purchase Department"""

            encoded_msg = urllib.parse.quote(message)
            whatsapp_url = f"https://web.whatsapp.com/send?phone={mobile}&text={encoded_msg}"

            # ✅ Send ONE chat message to all managers (no duplicates)
            bot_user = self.env.ref('base.user_root')  # System (OdooBot)
            partner_ids = manager_group.users.mapped('partner_id').ids  # all managers’ partners

            plain_message = (
                f"Purchase Order Approval Needed\n\n"
                f"Reference: {rec.name}\n"
                f"Requested by: {self.env.user.name}\n"
                f"Date: {rec.date_order.strftime('%d-%b-%Y') if rec.date_order else 'N/A'}\n\n"
                f"Please review and approve this request:\n{approval_link}"
            )

            self.env['mail.message'].create({
                'model': 'purchase.order',
                'res_id': rec.id,
                'body': plain_message,
                'subject': 'Purchase Order Approval Needed',
                'message_type': 'comment',
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'author_id': bot_user.partner_id.id,
                'partner_ids': [(6, 0, partner_ids)],  # one message, all recipients
            })

            # 🔹 Open WhatsApp after sending Odoo message
            return {
                'type': 'ir.actions.act_url',
                'url': whatsapp_url,
                'target': 'new',
            }

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

    is_storable = fields.Boolean(
        string="Is Storable",
        compute="_compute_is_storable",
        store=False
    )
    # image = fields.Binary(string="Image")

    def _compute_is_storable(self):
        for line in self:
            line.is_storable = line.product_id and line.product_id.type == 'product'



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        # Automatically tick is_storable as True when creating a product
        vals['is_storable'] = True
        return super(ProductTemplate, self).create(vals)

    @api.constrains('default_code')
    def _check_unique_default_code(self):
        for rec in self:
            if not rec.default_code:
                continue

            # check in product.product because default_code is stored there
            duplicate = self.env['product.product'].search([
                ('default_code', '=', rec.default_code),
                ('product_tmpl_id', '!=', rec.id),
            ], limit=1)

            if duplicate:
                raise ValidationError(
                    "This Part Number  is already used by another product. "
                    "Please enter a unique value."
                )



# please remove this codes before pushing

# removed