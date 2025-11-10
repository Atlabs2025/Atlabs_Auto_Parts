# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError
from odoo.tools import float_compare
import logging
_logger = logging.getLogger(__name__)

class MaterialPurchaseRequisition(models.Model):

    _name = 'material.purchase.requisition'
    _description = 'Purchase Requisition'
    #_inherit = ['mail.thread', 'ir.needaction_mixin']
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']      # odoo11
    _order = 'id desc'

    # vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle")
    vehicle_id = fields.Many2one('fleet.vehicle',string="Vehicle")
    vehicle_name = fields.Char(string="Vehicle")
    vin_sn = fields.Char(string="VIN Number")
    requisition_deadline_type = fields.Selection([
        ('normal', 'Normal'),
        ('urgent', 'Urgent'),
    ], string='Requisition Deadline Type', default='normal', tracking=True)



    #@api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel', 'reject'):
                raise UserError(_('You can not delete Purchase Requisition which is not in draft or cancelled or rejected state.'))
#                raise UserError(_('You can not delete Purchase Requisition which is not in draft or cancelled or rejected state.'))
        return super(MaterialPurchaseRequisition, self).unlink()
    
    name = fields.Char(
        string='Number',
        index=True,
        readonly=1,
    )
    state = fields.Selection([
        ('draft', 'New'),
        ('dept_confirm', 'Waiting Department Approval'),
        ('ir_approve', 'Waiting IR Approval'),
        ('approve', 'Approved'),
        ('stock', 'Purchase Order Created'),
        ('receive', 'Received'),
        ('cancel', 'Cancelled'),
        ('reject', 'Rejected')],
        default='draft',
        # tracking=True,
        tracking=True
    )
    request_date = fields.Date(
        string='Requisition Date',
        # default=fields.Date.today(),
        default=lambda self: fields.Date.context_today(self),
        required=True,
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        required=True,
        copy=True,
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1),
        required=True,
        copy=True,
    )
    approve_manager_id = fields.Many2one(
        'hr.employee',
        string='Department Manager',
        readonly=True,
        copy=False,
    )
    reject_manager_id = fields.Many2one(
        'hr.employee',
        string='Department Manager Reject',
        readonly=True,
    )
    approve_employee_id = fields.Many2one(
        'hr.employee',
        string='Approved by',
        readonly=True,
        copy=False,
    )
    reject_employee_id = fields.Many2one(
        'hr.employee',
        string='Rejected by',
        readonly=True,
        copy=False,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.user.company_id,
        required=True,
        copy=True,
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Source Location',
        copy=True,
    )
    requisition_line_ids = fields.One2many(
        'material.purchase.requisition.line',
        'requisition_id',
        string='Purchase Requisitions Line',
        copy=True,
    )
    # date_end = fields.Date(
    #     string='Requisition Deadline',
    #     readonly=True,
    #     help='Last date for the product to be needed',
    #     copy=True,
    # )

    date_end = fields.Date(
        string='Requisition Deadline',
        help='Last date for the product to be needed',
        copy=True,
    )


    date_done = fields.Date(
        string='Date Done', 
        readonly=True, 
        help='Date of Completion of Purchase Requisition',
    )
    managerapp_date = fields.Date(
        string='Department Approval Date',
        readonly=True,
        copy=False,
    )
    manareject_date = fields.Date(
        string='Department Manager Reject Date',
        readonly=True,
    )
    userreject_date = fields.Date(
        string='Rejected Date',
        readonly=True,
        copy=False,
    )
    userrapp_date = fields.Date(
        string='Approved Date',
        readonly=True,
        copy=False,
    )
    # receive_date = fields.Date(
    #     string='Received Date',
    #     readonly=True,
    #     copy=False,
    # )

    receive_date = fields.Date(
        string='Received Date',
        copy=False,
    )
    reason = fields.Text(
        string='Reason for Requisitions',
        required=False,
        copy=True,
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        copy=True,
    )
    dest_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        required=False,
        copy=True,
    )
    delivery_picking_id = fields.Many2one(
        'stock.picking',
        string='Internal Picking',
        readonly=True,
        copy=False,
    )
    requisiton_responsible_id = fields.Many2one(
        'hr.employee',
        string='Requisition Responsible',
        copy=True,
    )
    employee_confirm_id = fields.Many2one(
        'hr.employee',
        string='Confirmed by',
        readonly=True,
        copy=False,
    )
    confirm_date = fields.Date(
        string='Confirmed Date',
        readonly=True,
        copy=False,
    )
    
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'custom_requisition_id',
        string='Purchase Ordes',
    )
    custom_picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Picking Type',
        copy=False,
    )

    # job_card_id = fields.Many2one('job.card.management', string="Job Card")
    # job_number = fields.Char(string="Job Number", compute="_compute_job_number", store=True)
    job_number = fields.Char(string="Car ID", store=True)

    rfq_created = fields.Boolean(string="RFQ Created", default=False)


    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('purchase.requisition.seq')
        vals.update({
            'name': name
            })
        res = super(MaterialPurchaseRequisition, self).create(vals)
        return res



    @api.constrains('department_id', 'vehicle_name', 'vin_sn')
    def _check_vehicle_required(self):
        for rec in self:
            if rec.department_id and rec.department_id.name != 'Inventory':
                if not rec.vehicle_name or not rec.vin_sn:
                    raise ValidationError(_("Vehicle Name and VIN No are required for non-Inventory departments."))


    # @api.model
    # def create(self, vals):
    #     _logger.info('Create method called')
    #     name = self.env['ir.sequence'].next_by_code('purchase.requisition.seq')
    #     vals.update({'name': name})
    #
    #     # Proceed with creation
    #     res = super(MaterialPurchaseRequisition, self).create(vals)
    #
    #     # Add your logic here to handle related material request
    #     if res.job_card_id:
    #         self.env['job.card.material.request'].create({
    #             # 'job_card_id': res.job_number,
    #             'employee_id': res.employee_id.id,
    #             'request_date': res.request_date,
    #         })
    #
    #     return res

    # def action_open_rfq_form(self):
    #     self.ensure_one()
    #
    #     rfq_line_vals = [(0, 0, {
    #         'product_id': line.product_id.id,
    #         'product_qty': line.qty,
    #         'price_unit': line.cost_price or 0.0,
    #     }) for line in self.requisition_line_ids]  # ✅ Correct field name
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'res_model': 'rfq.request',
    #         'view_mode': 'form',
    #         'target': 'current',
    #         'context': {
    #             'default_line_ids': rfq_line_vals,
    #         },
    #     }

    def action_open_rfq_form(self):
        self.ensure_one()

        rfq_line_vals = []
        for line in self.requisition_line_ids:
            # ✅ Ensure product exists (avoid NewId errors)
            if not line.product_id or not line.product_id.id:
                continue

            rfq_line_vals.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.qty,
                'price_unit': line.cost_price or 0.0,
                'part_type': line.part_type or False,
                'part_no': line.part_no or False,
            }))

        # new boolean field added
        self.rfq_created = True

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'rfq.request',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_line_ids': rfq_line_vals,
                'default_vehicle_name': self.vehicle_name if self.vehicle_name else False,
                'default_vin_sn': self.vin_sn or False,
            },
        }

    # @api.model
    # def create(self, vals):
    #     name = self.env['ir.sequence'].next_by_code('purchase.requisition.seq')
    #     vals.update({'name': name})
    #
    #     # Create the requisition record
    #     res = super(MaterialPurchaseRequisition, self).create(vals)
    #
    #     # Ensure job_card_id exists
    #     if res.job_card_id:
    #         # Loop through each requisition line and create a material request line
    #         for line in res.requisition_line_ids:
    #             self.env['job.card.material.request'].create({
    #                 # 'job_card_id': res.job_card_id.id,
    #                 'employee_id': res.employee_id.id,
    #                 'request_date': res.request_date,
    #                 'requisition_type': line.requisition_type,
    #                 'product_id': line.product_id.id,
    #                 'description': line.description,
    #                 'qty': line.qty,
    #                 'uom': line.uom.id,
    #             })
    #
    #     return res


    #@api.multi
    # def requisition_confirm(self):
    #     for rec in self:
    #         manager_mail_template = self.env.ref('material_purchase_requisitions.email_confirm_material_purchase_requistion')
    #         rec.employee_confirm_id = rec.employee_id.id
    #         rec.confirm_date = fields.Date.today()
    #         rec.state = 'dept_confirm'
    #         if manager_mail_template:
    #             manager_mail_template.send_mail(self.id)

    # @api.multi

    # habeeb sir ideas


    # def requisition_confirm(self):
    #     for rec in self:
    #         manager_mail_template = self.env.ref(
    #             'material_purchase_requisitions.email_confirm_material_purchase_requistion')
    #         rec.employee_confirm_id = rec.employee_id.id
    #         rec.confirm_date = fields.Date.today()
    #         rec.state = 'dept_confirm'
    #
    #         # ✅ Safely check if job_card_id exists
    #         if rec.job_card_id:
    #             job_card_material_requests = self.env['job.card.material.request'].search([
    #                 ('state', '=', 'pending')
    #             ])
    #             for request in job_card_material_requests:
    #                 request.state = 'pending'
    #
    #         if manager_mail_template:
    #             manager_mail_template.send_mail(rec.id)


# removed pop up told by habeeb sir on oct 10
#     def requisition_confirm(self):
#         for rec in self:
#             manager_mail_template = self.env.ref(
#                 'material_purchase_requisitions.email_confirm_material_purchase_requistion',
#                 raise_if_not_found=False
#             )
#             rec.employee_confirm_id = rec.employee_id.id
#             rec.confirm_date = fields.Date.today()
#             rec.state = 'dept_confirm'
#
#             # ✅ Only update job.card.material.request if requisition is approved
#             if rec.state == 'approve' and rec.job_card_id:
#                 job_card_material_requests = self.env['job.card.material.request'].search([
#                     ('job_card_id', '=', rec.job_card_id.id),
#                     ('state', '=', 'pending')
#                 ])
#                 for request in job_card_material_requests:
#                     request.state = 'completed'
#
#             if manager_mail_template:
#                 manager_mail_template.send_mail(rec.id)
#
#         # ✅ Don’t return an action — just return True to stay on the same form
#         return True


  # changed function on oct 29 for creating internal picking when the stock is there
  #   def requisition_confirm(self):
  #       stock_picking = self.env['stock.picking']
  #       stock_move = self.env['stock.move']
  #       picking_type_obj = self.env['stock.picking.type']
  #
  #       for rec in self:
  #           # 🔹 Send email template if available
  #           manager_mail_template = self.env.ref(
  #               'material_purchase_requisitions.email_confirm_material_purchase_requistion',
  #               raise_if_not_found=False
  #           )
  #
  #           # 🔹 Confirmation details
  #           rec.employee_confirm_id = rec.employee_id.id
  #           rec.confirm_date = fields.Date.today()
  #           rec.state = 'dept_confirm'
  #
  #           # 🔹 Ensure there are requisition lines
  #           if not rec.requisition_line_ids:
  #               raise UserError(_('Please create some requisition lines before confirming.'))
  #
  #           # 🔹 Get internal transfer picking type
  #           internal_type = picking_type_obj.search([('code', '=', 'internal')], limit=1)
  #           if not internal_type:
  #               raise UserError(_('Please configure an internal transfer picking type.'))
  #
  #           # 🔹 Get source & destination locations
  #           source_location = internal_type.default_location_src_id
  #           dest_location = internal_type.default_location_dest_id
  #           if not source_location or not dest_location:
  #               raise UserError(_('Please set source and destination locations for the internal picking type.'))
  #
  #           # 🔹 Create internal picking
  #           picking_vals = {
  #               'picking_type_id': internal_type.id,
  #               'location_id': source_location.id,
  #               'location_dest_id': dest_location.id,
  #               'origin': rec.name,
  #               'company_id': rec.company_id.id,
  #               'custom_requisition_id': rec.id if 'custom_requisition_id' in stock_picking._fields else False,
  #               'note': rec.reason if 'reason' in rec._fields else '',
  #           }
  #           picking = stock_picking.sudo().create(picking_vals)
  #
  #           # 🔹 Create stock moves for each line
  #           for line in rec.requisition_line_ids:
  #               if not line.product_id:
  #                   continue
  #               move_vals = {
  #                   'name': line.product_id.display_name,
  #                   'product_id': line.product_id.id,
  #                   'product_uom_qty': line.qty,
  #                   'product_uom': line.uom.id if line.uom else line.product_id.uom_id.id,
  #                   'location_id': source_location.id,
  #                   'location_dest_id': dest_location.id,
  #                   'picking_id': picking.id,
  #                   'company_id': rec.company_id.id,
  #               }
  #               stock_move.sudo().create(move_vals)
  #
  #           # 🔹 Link picking if you have a field for it
  #           if 'delivery_picking_id' in rec._fields:
  #               rec.delivery_picking_id = picking.id
  #
  #           # 🔹 Send confirmation email
  #           if manager_mail_template:
  #               manager_mail_template.send_mail(rec.id)
  #
  #       return True
# changed function october31 for create picking in done state
#     def requisition_confirm(self):
#         stock_picking = self.env['stock.picking']
#         stock_move = self.env['stock.move']
#         picking_type_obj = self.env['stock.picking.type']
#
#         for rec in self:
#             # 🔹 Send email template if available
#             manager_mail_template = self.env.ref(
#                 'material_purchase_requisitions.email_confirm_material_purchase_requistion',
#                 raise_if_not_found=False
#             )
#
#             # 🔹 Confirmation details
#             rec.employee_confirm_id = rec.employee_id.id
#             rec.confirm_date = fields.Date.today()
#             rec.state = 'dept_confirm'
#
#             # 🔹 Ensure there are requisition lines
#             if not rec.requisition_line_ids:
#                 raise UserError(_('Please create some requisition lines before confirming.'))
#
#             # 🔹 Get internal transfer picking type
#             internal_type = picking_type_obj.search([('code', '=', 'internal')], limit=1)
#             if not internal_type:
#                 raise UserError(_('Please configure an internal transfer picking type.'))
#
#             # 🔹 Get source & destination locations
#             source_location = internal_type.default_location_src_id
#             dest_location = internal_type.default_location_dest_id
#             if not source_location or not dest_location:
#                 raise UserError(_('Please set source and destination locations for the internal picking type.'))
#
#             # 🔹 Create internal picking
#             picking_vals = {
#                 'picking_type_id': internal_type.id,
#                 'location_id': source_location.id,
#                 'location_dest_id': dest_location.id,
#                 'origin': rec.name,
#                 'company_id': rec.company_id.id,
#                 'custom_requisition_id': rec.id if 'custom_requisition_id' in stock_picking._fields else False,
#                 'scheduled_date': fields.Datetime.now(),
#                 'note': rec.reason if 'reason' in rec._fields else '',
#             }
#             picking = stock_picking.sudo().create(picking_vals)
#
#             # 🔹 Create stock moves for each requisition line
#             for line in rec.requisition_line_ids:
#                 if not line.product_id:
#                     continue
#                 move_vals = {
#                     'name': line.product_id.display_name,
#                     'product_id': line.product_id.id,
#                     'product_uom_qty': line.qty,
#                     'product_uom': line.uom.id if line.uom else line.product_id.uom_id.id,
#                     'location_id': source_location.id,
#                     'location_dest_id': dest_location.id,
#                     'picking_id': picking.id,
#                     'company_id': rec.company_id.id,
#                 }
#                 stock_move.sudo().create(move_vals)
#
#             # 🔹 Link picking if you have a field for it
#             if 'delivery_picking_id' in rec._fields:
#                 rec.delivery_picking_id = picking.id
#
#             # ✅ Auto confirm, assign, and validate picking (mark as done)
#             picking.action_confirm()
#             picking.action_assign()
#
#             for move in picking.move_ids_without_package:
#                 if move.state not in ('done', 'cancel'):
#                     # Ensure at least one move line exists
#                     if not move.move_line_ids:
#                         self.env['stock.move.line'].sudo().create({
#                             'move_id': move.id,
#                             'product_id': move.product_id.id,
#                             'product_uom_id': move.product_uom.id,
#                             'quantity': move.product_uom_qty,  # ✅ updated field
#                             'location_id': move.location_id.id,
#                             'location_dest_id': move.location_dest_id.id,
#                             'company_id': move.company_id.id,
#                         })
#                     else:
#                         move.move_line_ids.write({'quantity': move.product_uom_qty})  # ✅ updated field
#
#             # ✅ Validate picking (mark as Done)
#             picking.button_validate()
#
#             # 🔹 Send confirmation email
#             if manager_mail_template:
#                 manager_mail_template.send_mail(rec.id)
#
#         return True

    #@api.multi
    def requisition_reject(self):
        for rec in self:
            rec.state = 'reject'
            rec.reject_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.userreject_date = fields.Date.today()

    #@api.multi
    def manager_approve(self):
        for rec in self:
            rec.managerapp_date = fields.Date.today()
            rec.approve_manager_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            employee_mail_template = self.env.ref('material_purchase_requisitions.email_purchase_requisition_iruser_custom')
            email_iruser_template = self.env.ref('material_purchase_requisitions.email_purchase_requisition')
            # employee_mail_template.sudo().send_mail(self.id)
            # email_iruser_template.sudo().send_mail(self.id)
            employee_mail_template.send_mail(self.id)
            email_iruser_template.send_mail(self.id)
            rec.state = 'ir_approve'

    #@api.multi
    # def user_approve(self):
    #     for rec in self:
    #         rec.userrapp_date = fields.Date.today()
    #         rec.approve_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    #         rec.state = 'approve'



    # def user_approve(self):
    #     for rec in self:
    #         rec.userrapp_date = fields.Date.today()
    #         rec.approve_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
    #         rec.state = 'approve'
    #
    #         # ✅ Safely check if job_card_id exists
    #         if rec.job_card_id:
    #             job_card_material_requests = self.env['job.card.material.request'].search([
    #                 ('state', '=', 'pending')
    #             ])
    #             for request in job_card_material_requests:
    #                 request.state = 'completed'

    from odoo.exceptions import UserError
 # changed user approve function on oct 22 because if stock not available it should show popup so if need refer abobe old function
 #    def user_approve(self):
 #        for rec in self:
 #            # 🔹 Check material lines for stock availability
 #            for line in rec.requisition_line_ids:
 #                if line.stock_qty <= 0:
 #                    raise UserError(
 #                        f"Cannot approve because the stock for product '{line.product_id.display_name}' is not available.")
 #
 #            # ✅ If stock is fine, proceed with approval
 #            rec.userrapp_date = fields.Date.today()
 #            rec.approve_employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
 #            rec.state = 'approve'
 #
 #            # ✅ If job_card_id exists, update related requests
 #            if rec.job_card_id:
 #                job_card_material_requests = self.env['job.card.material.request'].search([
 #                    ('state', '=', 'pending')
 #                ])
 #                for request in job_card_material_requests:
 #                    request.state = 'completed'

    # def user_approve(self):
    #     for rec in self:
    #         # 🔹 Check material lines for stock availability
    #         for line in rec.requisition_line_ids:
    #             if line.stock_qty <= 0:
    #                 raise UserError(
    #                     f"Cannot approve because the stock for product '{line.product_id.display_name}' is not available."
    #                 )
    #
    #         # ✅ Proceed with approval
    #         rec.userrapp_date = fields.Date.today()
    #         rec.approve_employee_id = self.env['hr.employee'].search(
    #             [('user_id', '=', self.env.uid)], limit=1
    #         )
    #         rec.state = 'approve'

    def user_approve(self):
        stock_picking = self.env['stock.picking']
        stock_move = self.env['stock.move']
        picking_type_obj = self.env['stock.picking.type']

        for rec in self:
            # 🔹 Check material lines for stock availability
            for line in rec.requisition_line_ids:
                if line.stock_qty <= 0:
                    raise UserError(
                        f"Cannot approve because the stock for product '{line.product_id.display_name}' is not available."
                    )

            # ✅ Proceed with approval
            rec.userrapp_date = fields.Date.today()
            rec.approve_employee_id = self.env['hr.employee'].search(
                [('user_id', '=', self.env.uid)], limit=1
            )
            rec.state = 'approve'

            # 🔹 Get delivery picking type (stock out)
            delivery_type = picking_type_obj.search([('code', '=', 'outgoing')], limit=1)
            if not delivery_type:
                raise UserError(
                    _('Please configure an outgoing picking type (Delivery Order) in Inventory > Settings.'))

            # 🔹 Get source & destination locations
            source_location = delivery_type.default_location_src_id
            dest_location = delivery_type.default_location_dest_id
            if not source_location or not dest_location:
                raise UserError(_('Please set source and destination locations for the outgoing picking type.'))

            # 🔹 Create delivery picking
            picking_vals = {
                'picking_type_id': delivery_type.id,
                'location_id': source_location.id,
                'location_dest_id': dest_location.id,
                'origin': rec.name,
                'company_id': rec.company_id.id,
                'custom_requisition_id': rec.id if 'custom_requisition_id' in stock_picking._fields else False,
                'scheduled_date': fields.Datetime.now(),
                'note': rec.reason if 'reason' in rec._fields else '',
                'employee_id': rec.employee_id.id if 'employee_id' in rec._fields else False,
                'department_id': rec.department_id.id if 'department_id' in rec._fields else False,
                'job_number': rec.job_number if 'job_number' in rec._fields else False,
                'vehicle_name': rec.vehicle_name if 'vehicle_name' in rec._fields else False,
                'vin_sn': rec.vin_sn if 'vin_sn' in rec._fields else False,
            }
            picking = stock_picking.sudo().create(picking_vals)

            # 🔹 Create stock moves for each requisition line
            for line in rec.requisition_line_ids:
                if not line.product_id:
                    continue
                move_vals = {
                    'name': line.product_id.display_name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.qty,
                    'product_uom': line.uom.id if line.uom else line.product_id.uom_id.id,
                    'location_id': source_location.id,
                    'location_dest_id': dest_location.id,
                    'picking_id': picking.id,
                    'company_id': rec.company_id.id,


                }
                stock_move.sudo().create(move_vals)

            # 🔹 Link picking to requisition if field exists
            if 'delivery_picking_id' in rec._fields:
                rec.delivery_picking_id = picking.id

            # ✅ Auto confirm, assign, and validate picking (mark as done)
            picking.action_confirm()
            picking.action_assign()

            for move in picking.move_ids_without_package:
                if move.state not in ('done', 'cancel'):
                    # Ensure at least one move line exists
                    if not move.move_line_ids:
                        self.env['stock.move.line'].sudo().create({
                            'move_id': move.id,
                            'product_id': move.product_id.id,
                            'product_uom_id': move.product_uom.id,
                            'quantity': move.product_uom_qty,
                            'location_id': move.location_id.id,
                            'location_dest_id': move.location_dest_id.id,
                            'company_id': move.company_id.id,
                        })
                    else:
                        move.move_line_ids.write({'quantity': move.product_uom_qty})

            # ✅ Validate picking (mark as Done)
            picking.button_validate()

        return True

    #@api.multi
    def reset_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.model
    def _prepare_pick_vals(self, line=False, stock_id=False):
        pick_vals = {
            'product_id' : line.product_id.id,
            'product_uom_qty' : line.qty,
            'product_uom' : line.uom.id,
            'location_id' : stock_id.location_id.id or self.location_id.id,
            'location_dest_id' : stock_id.location_dest_id.id or self.dest_location_id.id,
            'name' : line.product_id.name,
            'picking_type_id' : stock_id.picking_type_id.id or self.custom_picking_type_id.id,
            'picking_id' : stock_id.id,
            'custom_requisition_line_id' : line.id,
            'company_id' : line.requisition_id.company_id.id,
        }
        return pick_vals

    @api.model
    def _prepare_po_line(self, line=False, purchase_order=False):
        seller = line.product_id._select_seller(
                partner_id=self._context.get('partner_id'), 
                quantity=line.qty,
                date=purchase_order.date_order and purchase_order.date_order.date(), 
                uom_id=line.uom
                )
        po_line_vals = {
                'product_id': line.product_id.id,
                'name':line.product_id.name,
                'product_qty': line.qty,
                'product_uom': line.uom.id,
                'date_planned': fields.Date.today(),
                 # 'price_unit': line.product_id.standard_price,
                'price_unit': seller.price or line.product_id.standard_price or 0.0,
                'order_id': purchase_order.id,
                 'account_analytic_id': self.analytic_account_id.id,
                # 'analytic_distribution':  {self.sudo().analytic_account_id.id: 100} if self.analytic_account_id else False,
                'custom_requisition_line_id': line.id
        }
        return po_line_vals
    
    #@api.multi
    def request_stock(self):
        stock_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        #internal_obj = self.env['stock.picking.type'].search([('code','=', 'internal')], limit=1)
        #internal_obj = self.env['stock.location'].search([('usage','=', 'internal')], limit=1)
        purchase_obj = self.env['purchase.order']
        purchase_line_obj = self.env['purchase.order.line']
#         if not internal_obj:
#             raise UserError(_('Please Specified Internal Picking Type.'))
        for rec in self:
            if not rec.requisition_line_ids:
#                raise UserError(_('Please create some requisition lines.'))
                raise UserError(_('Please create some requisition lines.'))
            if any(line.requisition_type =='internal' for line in rec.requisition_line_ids):
                # if not rec.location_id.id:
                #     raise UserError(_('Select Source location under the picking details.'))
                if not rec.custom_picking_type_id.id:
                    rec.custom_picking_type_id = self.env['stock.picking.type'].search([('code', '=', 'outgoing')]).id
#                        raise UserError(_('Select Picking Type under the picking details.'))
#                    raise UserError(_('Select Picking Type under the picking details.'))
                # if not rec.dest_location_id:
                #     raise UserError(_('Select Destination location under the picking details.'))
#                 if not rec.employee_id.dest_location_id.id or not rec.employee_id.department_id.dest_location_id.id:
#                     raise UserError(_('Select Destination location under the picking details.'))
                picking_vals = {
                        'partner_id' : rec.employee_id.sudo().address_home_id.id,
                        #'min_date' : fields.Date.today(),
                        # 'location_id' : rec.location_id.id,
                        'location_id' : self.env['stock.location'].search([('id', '=', 1)]).id,
                        # 'location_dest_id' : rec.dest_location_id and rec.dest_location_id.id or rec.employee_id.dest_location_id.id or rec.employee_id.department_id.dest_location_id.id,
                        'location_dest_id' : self.env['stock.location'].search([('id', '=', 5)]).id,
                        'picking_type_id' : rec.custom_picking_type_id.id,#internal_obj.id,
                        'note' : rec.reason,
                        'custom_requisition_id' : rec.id,
                        'origin' : rec.name,
                        'company_id' : rec.company_id.id,
                        
                    }
                stock_id = stock_obj.sudo().create(picking_vals)
                delivery_vals = {
                        'delivery_picking_id' : stock_id.id,
                    }
                rec.write(delivery_vals)
                
            po_dict = {}
            for line in rec.requisition_line_ids:
                if line.requisition_type =='internal':
                    pick_vals = rec._prepare_pick_vals(line, stock_id)
                    move_id = move_obj.sudo().create(pick_vals)
                    # Check if the picking type is a delivery order
                    if stock_id.picking_type_id.code == 'outgoing':
                        if stock_id.state == 'draft':
                            stock_id.action_confirm()
                            stock_id.action_assign()
                            for move in stock_id.move_lines.filtered(
                                    lambda m: m.state not in ["done", "cancel"]
                            ):
                                rounding = move.product_id.uom_id.rounding
                                if (
                                        float_compare(
                                            move.quantity_done,
                                            move.product_qty,
                                            precision_rounding=rounding,
                                        )
                                        == -1
                                ):
                                    for move_line in move.move_line_ids:
                                        move_line.qty_done = move_line.product_uom_qty
                            stock_id.button_validate()

                #else:
                if line.requisition_type == 'purchase': #10/12/2019
                    if not line.partner_id:
                        raise UserError(_('Please enter atleast one vendor on Requisition Lines for Requisition Action Purchase'))
#                        raise UserError(_('Please enter atleast one vendor on Requisition Lines for Requisition Action Purchase'))
                    for partner in line.partner_id:
                        if partner not in po_dict:
                            po_vals = {
                                'partner_id':partner.id,
                                'currency_id':rec.env.user.company_id.currency_id.id,
                                'date_order':fields.Date.today(),
#                                'company_id':rec.env.user.company_id.id,
                                'company_id':rec.company_id.id,
                                'custom_requisition_id':rec.id,
                                'origin': rec.name,
                            }
                            purchase_order = purchase_obj.create(po_vals)
                            po_dict.update({partner:purchase_order})
                            po_line_vals = rec.with_context(partner_id=partner)._prepare_po_line(line, purchase_order)
#                            {
#                                     'product_id': line.product_id.id,
#                                     'name':line.product_id.name,
#                                     'product_qty': line.qty,
#                                     'product_uom': line.uom.id,
#                                     'date_planned': fields.Date.today(),
#                                     'price_unit': line.product_id.lst_price,
#                                     'order_id': purchase_order.id,
#                                     'account_analytic_id': rec.analytic_account_id.id,
#                            }
                            purchase_line_obj.sudo().create(po_line_vals)
                        else:
                            purchase_order = po_dict.get(partner)
                            po_line_vals = rec.with_context(partner_id=partner)._prepare_po_line(line, purchase_order)
#                            po_line_vals =  {
#                                 'product_id': line.product_id.id,
#                                 'name':line.product_id.name,
#                                 'product_qty': line.qty,
#                                 'product_uom': line.uom.id,
#                                 'date_planned': fields.Date.today(),
#                                 'price_unit': line.product_id.lst_price,
#                                 'order_id': purchase_order.id,
#                                 'account_analytic_id': rec.analytic_account_id.id,
#                            }
                            purchase_line_obj.sudo().create(po_line_vals)
                # rec.state = 'stock'
    
    #@api.multi
    def action_received(self):
        for rec in self:
            rec.receive_date = fields.Date.today()
            rec.state = 'receive'
    
    #@api.multi
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
    
    @api.onchange('employee_id')
    def set_department(self):
        for rec in self:
            rec.department_id = rec.employee_id.sudo().department_id.id
            rec.dest_location_id = rec.employee_id.sudo().dest_location_id.id or rec.employee_id.sudo().department_id.dest_location_id.id 

    #@api.multi
    def show_picking(self):
        #for rec in self:
            # res = self.env.ref('stock.action_picking_tree_all')
            # res = res.sudo().read()[0]
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('stock.action_picking_tree_all')
        res['domain'] = str([('custom_requisition_id','=',self.id)])
        return res
        
    #@api.multi
    # def action_show_po(self):
    #     # for rec in self:
    #     #     purchase_action = self.env.ref('purchase.purchase_rfq')
    #     #     purchase_action = purchase_action.sudo().read()[0]
    #     self.ensure_one()
    #     purchase_action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_rfq')
    #     purchase_action['domain'] = str([('custom_requisition_id','=',self.id)])
    #     return purchase_action

    # function added on july31 for fetching details from material purchase

    def action_show_po(self):
        self.ensure_one()
        purchase_action = self.env['ir.actions.act_window']._for_xml_id('purchase.purchase_rfq')
        purchase_action['domain'] = [('custom_requisition_id', '=', self.id)]
        purchase_action['context'] = {
            'default_custom_requisition_id': self.id,
            'default_origin': self.name,
        }
        return purchase_action




    # @api.model
    # def default_get(self, fields):
    #     res = super(MaterialPurchaseRequisition, self).default_get(fields)
    #     job_card_id = self.env.context.get('default_job_card_id')
    #     if job_card_id:
    #         job_card = self.env['job.card.management'].browse(job_card_id)
    #         lines = []
    #         for line in job_card.job_detail_line_ids.filtered(
    #                 lambda l: l.department == 'parts' and not l.is_request_completed and not l.is_request_pending):
    #             product_variant = line.product_template_id.product_variant_id
    #             if product_variant and product_variant.active:
    #                 lines.append((0, 0, {
    #                     'product_id': product_variant.id,
    #                     'qty': line.quantity,
    #                     'description': line.description,
    #                     # Add other fields as needed
    #                 }))
    #         res['requisition_line_ids'] = lines
    #     return res
 # october 27
    # @api.model
    # def default_get(self, fields):
    #     res = super(MaterialPurchaseRequisition, self).default_get(fields)
    #     job_card_id = self.env.context.get('default_job_card_id')
    #     if job_card_id:
    #         job_card = self.env['job.card.management'].browse(job_card_id)
    #         lines = []
    #         for line in job_card.job_detail_line_ids.filtered(
    #                 lambda l: l.department == 'parts' and not l.is_request_completed and not l.is_request_pending):
    #             product_variant = line.product_template_id.product_variant_id
    #             if product_variant and product_variant.active:
    #                 lines.append((0, 0, {
    #                     # 'part_no':line.product_template_id,
    #                     # 'part_no': product_variant.name,
    #                     'part_no': f"[{product_variant.default_code}] {product_variant.name}" if product_variant.default_code else product_variant.name,
    #                     'product_id': product_variant.id,
    #                     'qty': line.quantity,
    #                     'uom':line.uom,
    #                     'description': line.description,
    #                 }))
    #         res['requisition_line_ids'] = lines
    #     return res

    @api.onchange('vehicle_id')
    def _onchange_vehicle_id(self):
        if self.vehicle_id:
            self.vin_sn = self.vehicle_id.vin_sn
        else:
            self.vin_sn = False




