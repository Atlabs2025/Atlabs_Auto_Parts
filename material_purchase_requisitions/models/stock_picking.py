# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    custom_requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string='Purchase Requisition',
        readonly=True,

    )



    # newly added fields

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1),
        # required=True,
        copy=True,
    )

    taken_by = fields.Char(string="Taken By")

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        # required=True,
        copy=True,
    )

    car_id = fields.Many2one('vehicle.details', string="Car ID", store=True)
    vehicle_name = fields.Char(string="Vehicle")
    vin_sn = fields.Char(string="VIN Number")

    hide_in_requisition = fields.Boolean(
        string="Hide from Material Requisition",
        default=False
    )

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Auto fill department when employee selected"""
        for rec in self:
            if rec.employee_id and rec.employee_id.department_id:
                rec.department_id = rec.employee_id.department_id.id


    def button_validate(self):
        res = super(StockPicking, self).button_validate()

        for picking in self:
            # try to get linked purchase.order (recommended: use purchase_id)
            po = picking.purchase_id or self.env['purchase.order'].search([('name', '=', picking.origin)], limit=1)

            if po and po.custom_requisition_id:
                req_id = po.custom_requisition_id.id


                picking.sudo().write({'custom_requisition_id': req_id})

                #  write onto moves (so stock.move.epr_id is filled)
                picking.move_ids_without_package.sudo().write({'epr_id': req_id})

                #  onto move lines (so stock.move.line.epr_id is filled)
                picking.move_line_ids.sudo().write({'epr_id': req_id})

        return res


class StockMove(models.Model):
    _inherit = 'stock.move'



    custom_requisition_line_id = fields.Many2one(
        'material.purchase.requisition.line',
        string='Requisitions Line',
        copy=True
    )

    epr_id = fields.Many2one('material.purchase.requisition', string='EPR')

    available_qty = fields.Float(
        string="Stock",
        compute="_compute_available_qty",
        store=False,
    )
    part_location = fields.Char(string="Part Location")
    # commented because stock showing minus value
    #
    # @api.depends('product_id', 'location_id')
    # def _compute_available_qty(self):
    #     for rec in self:
    #         qty = 0.0
    #         if rec.product_id and rec.location_id:
    #             # get quantity available in that location
    #             qty = rec.product_id.with_context(location=rec.location_id.id).qty_available
    #         rec.available_qty = qty

    @api.depends('product_id', 'location_id')
    def _compute_available_qty(self):
        for rec in self:
            qty = 0.0
            if rec.product_id and rec.location_id:
                # get quantity available in that location
                qty = rec.product_id.with_context(location=rec.location_id.id).qty_available

            # ✅ ensure negative values display as 0
            rec.available_qty = max(qty, 0.0)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:



class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    epr_id = fields.Many2one('material.purchase.requisition', string="Requisition")
