from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError


class RFQRequest(models.Model):
    _name = 'rfq.request'
    _description = 'RFQ Multi Vendor Request'

    name = fields.Char(
        string='RFQ Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New'
    )

    supplier_ids = fields.Many2many('res.partner', string='Suppliers', domain=[('supplier_rank', '>', 0)])
    line_ids = fields.One2many('rfq.request.line', 'rfq_id', string='Products')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
    ], string='Status', default='draft')

    purchase_order_ids = fields.One2many(
        'purchase.order', 'rfq_request_id', string='RFQ'
    )
    rfq_count = fields.Integer(
        string='RFQ Count',
        compute='_compute_rfq_count'
    )

    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")
    car_id = fields.Many2one('vehicle.details', string="Car ID", store=True)
    vehicle_name = fields.Char(string="Vehicle")
    vin_sn = fields.Char(string="VIN Number")

    material_requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string='Material Requisition',store=True,readonly=True,
    )





    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('rfq.request') or 'New'
        return super().create(vals)


 # problem of comfirming solved

    # def action_confirm(self):
    #     for rec in self:
    #         if not rec.supplier_ids:
    #             raise UserError("Please select at least one supplier.")
    #         if not rec.line_ids:
    #             raise UserError("Please add at least one product line.")
    #
    #         # ✅ Try to get incoming picking type first
    #         picking_type = self.env['stock.picking.type'].search([
    #             ('code', '=', 'incoming'),
    #             ('warehouse_id.company_id', '=', self.env.company.id)
    #         ], limit=1)
    #
    #         # 🔁 Fallback to internal if not found
    #         if not picking_type:
    #             picking_type = self.env['stock.picking.type'].search([
    #                 ('code', '=', 'internal'),
    #                 ('warehouse_id.company_id', '=', self.env.company.id)
    #             ], limit=1)
    #
    #         if not picking_type:
    #             raise UserError(
    #                 "No picking type found for this company. Please configure it in Inventory > Settings."
    #             )
    #
    #         for supplier in rec.supplier_ids:
    #             po_vals = {
    #                 'partner_id': supplier.id,
    #                 'rfq_request_id': rec.id,
    #                 'vehicle_name': rec.vehicle_name if rec.vehicle_name else False,
    #                 'vin_sn': rec.vin_sn or False,
    #                 'picking_type_id': picking_type.id,  # ✅ ensure assigned
    #                 'order_line': [],
    #             }
    #
    #             order_lines = []
    #             for line in rec.line_ids:
    #                 order_lines.append((0, 0, {
    #                     'part_type': line.part_type,
    #                     'part_no': line.part_no,
    #                     'product_id': line.product_id.id,
    #                     'name': line.product_id.display_name,
    #                     'product_qty': line.product_qty,
    #                     'price_unit': 0.0,
    #                     'date_planned': fields.Date.today(),
    #                 }))
    #             po_vals['order_line'] = order_lines
    #
    #             self.env['purchase.order'].create(po_vals)
    #         if rec.material_requisition_id:
    #             rec.material_requisition_id.state = 'rfq'
    #         rec.state = 'confirmed'

    def action_confirm(self):
        for rec in self:
            if not rec.supplier_ids:
                raise UserError("Please select at least one supplier.")
            if not rec.line_ids:
                raise UserError("Please add at least one product line.")

            picking_type = self.env['stock.picking.type'].search([
                ('code', '=', 'incoming'),
                ('warehouse_id.company_id', '=', self.env.company.id)
            ], limit=1)

            if not picking_type:
                picking_type = self.env['stock.picking.type'].search([
                    ('code', '=', 'internal'),
                    ('warehouse_id.company_id', '=', self.env.company.id)
                ], limit=1)

            if not picking_type:
                raise UserError(
                    "No picking type found for this company. Please configure it in Inventory > Settings."
                )

            for supplier in rec.supplier_ids:
                po_vals = {
                    'partner_id': supplier.id,
                    'rfq_request_id': rec.id,
                    'car_id': rec.car_id.id if rec.car_id else False,
                    'vehicle_name': rec.vehicle_name if rec.vehicle_name else False,
                    'vin_sn': rec.vin_sn or False,
                    'picking_type_id': picking_type.id,
                    # 'material_requisition_id': rec.material_requisition_id.id,
                    'order_line': [],
                }

                order_lines = []
                for line in rec.line_ids:
                    order_lines.append((0, 0, {
                        'part_type': line.part_type,
                        'part_no': line.part_no,
                        'product_id': line.product_id.id,
                        'name': line.product_id.display_name,
                        'product_qty': line.product_qty,
                        'price_unit': 0.0,
                        'date_planned': fields.Date.today(),
                    }))
                po_vals['order_line'] = order_lines

                self.env['purchase.order'].create(po_vals)

            rec.state = 'confirmed'



    def _compute_rfq_count(self):
        for rec in self:
            rec.rfq_count = self.env['purchase.order'].search_count([
                ('rfq_request_id', '=', rec.id)
            ])

    def action_view_rfq(self):
        return {
            'name': 'RFQ',
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'list,form',
            'domain': [('rfq_request_id', '=', self.id)],
            'context': {'default_rfq_request_id': self.id},
        }



class RFQManagementLine(models.Model):
    _name = 'rfq.request.line'
    _description = 'RFQ Management Line'

    rfq_id = fields.Many2one('rfq.request', string='RFQ Reference')
    part_type = fields.Selection([
        ('after_market', 'After Market'),
        ('genuine', 'Genuine'),
        ('used', 'Used'),
    ], string='Part Type', default='')
    part_no = fields.Char(string="Part Number")
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', required=True, default=1)
    price_unit = fields.Float(string='Unit Price')
    # image = fields.Binary(string="Image")




class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    rfq_request_id = fields.Many2one(
        'rfq.request',
        string='RFQ Reference',
        help='Reference to the RFQ Request that generated this purchase order.'
    )


    material_requisition_id = fields.Many2one(
        'material.purchase.requisition',
        related='rfq_request_id.material_requisition_id',
        store=True,
        readonly=True,
    )

    def button_approve(self, force=False):
        res = super(PurchaseOrder, self).button_approve(force)

        for po in self:
            if po.material_requisition_id:
                po.material_requisition_id.state = 'purchase'

        return res






