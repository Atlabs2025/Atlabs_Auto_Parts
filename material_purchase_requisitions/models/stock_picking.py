# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    custom_requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string='Purchase Requisition',
        readonly=True,
        copy=True
    )

    # newly added fields

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1),
        required=True,
        copy=True,
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        required=True,
        copy=True,
    )

    job_number = fields.Char(string="Car ID")
    vehicle_name = fields.Char(string="Vehicle")
    vin_sn = fields.Char(string="VIN Number")

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Auto fill department when employee selected"""
        for rec in self:
            if rec.employee_id and rec.employee_id.department_id:
                rec.department_id = rec.employee_id.department_id.id

class StockMove(models.Model):
    _inherit = 'stock.move'
    
    custom_requisition_line_id = fields.Many2one(
        'material.purchase.requisition.line',
        string='Requisitions Line',
        copy=True
    )

    available_qty = fields.Float(
        string="Stock",
        compute="_compute_available_qty",
        store=False,
    )

    @api.depends('product_id', 'location_id')
    def _compute_available_qty(self):
        for rec in self:
            qty = 0.0
            if rec.product_id and rec.location_id:
                # get quantity available in that location
                qty = rec.product_id.with_context(location=rec.location_id.id).qty_available
            rec.available_qty = qty

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
