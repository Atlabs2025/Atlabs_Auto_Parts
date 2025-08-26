# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    
    custom_requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string='Requisitions',
        copy=False
    )

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
