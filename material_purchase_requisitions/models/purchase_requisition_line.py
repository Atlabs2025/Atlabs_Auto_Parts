# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

class MaterialPurchaseRequisitionLine(models.Model):
    _name = "material.purchase.requisition.line"
    _description = 'Material Purchase Requisition Lines'


    requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string='Requisitions', 
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )

#     layout_category_id = fields.Many2one(
#         'sale.layout_category',
#         string='Section',
#     )
    description = fields.Char(
        string='Description',
        required=True,
    )
    qty = fields.Float(
        string='Quantity',
        default=1,
        required=True,
    )
    uom = fields.Many2one(
        'uom.uom',#product.uom in odoo11
        string='Unit of Measure',
        required=True,
    )
    partner_id = fields.Many2many(
        'res.partner',
        string='Vendors',
    )
    requisition_type = fields.Selection(
        selection=[
                    ('internal','Internal Picking'),
                    ('purchase','Purchase Order'),
        ],
        string='Requisition Action',
        default='internal',
        required=True,
    )

    part_no = fields.Char(string="Part Number")
    product_template_id = fields.Many2one('product.template', string="Part Number")
    # part_no = fields.Many2one('product.product', string="Part Number", domain="[('default_code', '!=', False)]")
    cost_price = fields.Float(string="Cost Price")
    sale_price = fields.Float(string="Sale Price")
    # stock_qty = fields.Float(string="On Hand Quantity", readonly=True)

    stock_qty = fields.Float(string="Stock", compute="_compute_stock_qty", readonly=True)

    from_job_card = fields.Boolean(
        string='From Job Card')

    @api.depends('product_id')
    def _compute_stock_qty(self):
        for rec in self:
            rec.stock_qty = rec.product_id.qty_available if rec.product_id else 0.0
# commented default code
    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            # rec.description = rec.product_id.name
            rec.description = rec.product_id.display_name
            rec.uom = rec.product_id.uom_id.id
            rec.part_no =rec.product_id.default_code
            # rec.sale_price =rec.product_id.lst_price
            rec.cost_price =rec.product_id.standard_price

    @api.onchange('part_no')
    def _onchange_part_no(self):
        for rec in self:
            if rec.part_no:
                product = self.env['product.product'].search([('default_code', '=', rec.part_no)], limit=1)
                if product:
                    rec.product_id = product.id
                    rec.description = product.display_name
                    rec.uom = product.uom_id.id
                    rec.cost_price = product.standard_price
                    rec.sale_price = product.lst_price
                else:
                    rec.product_id = False
                    rec.description = ''
                    rec.uom = False
                    rec.cost_price = 0.0
                    rec.sale_price = 0.0
                    # Optional: raise error if not found
                    # raise UserError("Product with this part number not found.")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
# added for seeing the from job card field true
    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get('from_job_card_origin'):
            res['from_job_card'] = True
        return res



    # @api.model
    # def create(self, vals):
    #     # Check if we are coming from job card context
    #     if self.env.context.get('from_job_card_origin'):
    #         vals['from_job_card'] = True
    #     return super(MaterialPurchaseRequisitionLine, self).create(vals)
