from odoo import api, fields, models
from odoo.exceptions import UserError

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
    supplier_ids = fields.Many2many('res.partner', string='Suppliers')
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
    vin_sn = fields.Char(string="VIN Number")


    @api.model
    def create(self, vals):
        """Assign sequence number like RFQS0001, RFQS0002, etc."""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('rfq.request') or 'New'
        return super().create(vals)

    def action_confirm(self):
        """Create multiple Purchase Orders for selected suppliers"""
        for rec in self:
            if not rec.supplier_ids:
                raise UserError("Please select at least one supplier.")
            if not rec.line_ids:
                raise UserError("Please add at least one product line.")

            for supplier in rec.supplier_ids:
                po_vals = {
                    'partner_id': supplier.id,
                    'rfq_request_id': rec.id,
                    'vehicle_id': rec.vehicle_id.id if rec.vehicle_id else False,
                    'vin_sn': rec.vin_sn or False,
                    'order_line': [],
                }

                order_lines = []
                for line in rec.line_ids:
                    order_lines.append((0, 0, {
                        'part_type':line.part_type,
                        'product_id': line.product_id.id,
                        'name': line.product_id.display_name,
                        'product_qty': line.product_qty,
                        # 'price_unit': line.price_unit,
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
    product_id = fields.Many2one('product.product', string='Product', required=True)
    product_qty = fields.Float(string='Quantity', required=True, default=1)
    price_unit = fields.Float(string='Unit Price')




class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    rfq_request_id = fields.Many2one(
        'rfq.request',
        string='RFQ Reference',
        help='Reference to the RFQ Request that generated this purchase order.'
    )