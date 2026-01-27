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



# dec 30 for lot displaying
#     def button_validate(self):
#
#         for picking in self:
#
#             # 🔹 Get PO
#             po = picking.purchase_id or self.env['purchase.order'].search(
#                 [('name', '=', picking.origin)], limit=1
#             )
#
#             if not po or not po.custom_requisition_id:
#                 continue
#
#             requisition = po.custom_requisition_id
#             req_id = requisition.id
#
#             # 🔹 set epr on picking
#             picking.sudo().write({
#                 'custom_requisition_id': req_id
#             })
#
#             # 🔹 Loop through stock moves
#             for move in picking.move_ids_without_package:
#
#                 # 🔹 set epr on move
#                 move.sudo().write({
#                     'epr_id': req_id
#                 })
#
#                 req_line = requisition.requisition_line_ids.filtered(
#                     lambda l: l.product_id == move.product_id and l.lot_id
#                 )
#
#                 if not req_line:
#                     continue
#
#                 lot = req_line[0].lot_id
#
#                 # 🔹 Create / update move lines
#                 if not move.move_line_ids:
#                     self.env['stock.move.line'].sudo().create({
#                         'move_id': move.id,
#                         'picking_id': picking.id,
#                         'product_id': move.product_id.id,
#                         'product_uom_id': move.product_uom.id,
#                         'location_id': move.location_id.id,
#                         'location_dest_id': move.location_dest_id.id,
#                         'quantity': move.product_uom_qty,
#                         'lot_id': lot.id,
#                         'epr_id': req_id,  # ✅ HERE
#                     })
#                 else:
#                     move.move_line_ids.sudo().write({
#                         'lot_id': lot.id,
#                         'quantity': move.product_uom_qty,
#                         'epr_id': req_id,  # ✅ HERE
#                     })
#
#         # 🔥 finally validate
#         res = super(StockPicking, self).button_validate()
#         return res



# code added on january27 and above code commented
    def button_validate(self):

        for picking in self:

            # 🔹 Get PO
            po = picking.purchase_id or self.env['purchase.order'].search(
                [('name', '=', picking.origin)], limit=1
            )

            if not po or not po.custom_requisition_id:
                continue

            requisition = po.custom_requisition_id
            req_id = requisition.id

            # 🔹 set epr on picking
            picking.sudo().write({
                'custom_requisition_id': req_id
            })

            # 🔹 Loop through stock moves
            for move in picking.move_ids_without_package:

                # 🔹 set epr on move
                move.sudo().write({
                    'epr_id': req_id
                })

                req_line = requisition.requisition_line_ids.filtered(
                    lambda l: l.product_id == move.product_id and l.lot_id
                )

                if not req_line:
                    continue

                lot = req_line[0].lot_id

                # 🔹 Create / update move lines (NO QUANTITY)
                if not move.move_line_ids:
                    self.env['stock.move.line'].sudo().create({
                        'move_id': move.id,
                        'picking_id': picking.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'lot_id': lot.id,
                        'epr_id': req_id,
                    })
                else:
                    move.move_line_ids.sudo().write({
                        'lot_id': lot.id,
                        'epr_id': req_id,
                    })

        # 🔥 VERY IMPORTANT: let Odoo decide backorder
        res = super(StockPicking, self).button_validate()
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
        store=True,
    )
    part_location = fields.Char(string="Part Location")




# changed function on december3 because stock not comming
    @api.depends('product_id')
    def _compute_available_qty(self):
        for rec in self:
            if not rec.product_id:
                rec.available_qty = 0
                return
            # Get the product on-hand quantity AFTER picking validation
            rec.available_qty = rec.product_id.qty_available




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:




class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    epr_id = fields.Many2one('material.purchase.requisition', string="Requisition")
    car_id = fields.Many2one('vehicle.details', string="Car ID", store=True)

# only for local purpose
# class StockReturnPicking(models.TransientModel):
#     _inherit = 'stock.return.picking'
#
#     picking_type_code = fields.Selection(
#         related='picking_id.picking_type_id.code',
#         store=False
#     )