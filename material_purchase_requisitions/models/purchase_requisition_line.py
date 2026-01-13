# -*- coding: utf-8 -*-

from odoo import models, fields, api
import odoo.addons.decimal_precision as dp

from odoo.exceptions import ValidationError


class MaterialPurchaseRequisitionLine(models.Model):
    _name = "material.purchase.requisition.line"
    _description = 'Material Purchase Requisition Lines'


    requisition_id = fields.Many2one(
        'material.purchase.requisition',
        string='Requisitions', 
    )
    # product_id = fields.Many2one(
    #     'product.product',
    #     string='Product',
    #     # required=True,
    # )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        domain="[('categ_id.name', '=', 'Non Inventory')] if requisition_type == 'purchase' else []",required=True,
    )

    #     layout_category_id = fields.Many2one(
#         'sale.layout_category',
#         string='Section',
#     )
    description = fields.Char(
        string='Description',

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
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Nature Of Cost',
        copy=True,required=True
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
        default='purchase',
        required=True,
    )
    part_type = fields.Selection([
        ('after_market', 'After Market'),
        ('genuine', 'Genuine'),
        ('used', 'Used'),
    ], string='Part Type', default='',required=True)

    part_no = fields.Char(string="Part Number")
    product_template_id = fields.Many2one('product.template', string="Part Number")
    # part_no = fields.Many2one('product.product', string="Part Number", domain="[('default_code', '!=', False)]")
    cost_price = fields.Float(string="Cost Price")
    sale_price = fields.Float(string="Sale Price")
    # stock_qty = fields.Float(string="On Hand Quantity", readonly=True)

    stock_qty = fields.Float(string="Stock", compute="_compute_stock_qty", readonly=True)
    # stock_qty = fields.Float(string="Stock")

    from_job_card = fields.Boolean(
        string='From Job Card')

    image = fields.Image(string="Image")
    # is_stock = fields.Boolean(string="Stock Available", default=False)
    is_stock = fields.Boolean(
        string="Has Stock",
        compute="_compute_is_stock",
        store=False
    )

    picking_created = fields.Boolean(string="Picking Created", default=False)

    lot_id = fields.Many2one('stock.lot',string='Lot / Car ID',domain="[('product_id', '=', product_id)]",)

    parts_state = fields.Selection([('approved', 'Approved'),('not_approved', 'Not Approved'),],string="Parts State",default='not_approved',tracking=True)

    @api.depends('stock_qty')
    def _compute_is_stock(self):
        for line in self:
            line.is_stock = line.stock_qty > 0

    def action_preview_image(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Image Preview',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'new',  # popup
            'views': [(self.env.ref('material_purchase_requisitions.image_preview_form').id, 'form')],
        }

    # @api.depends('product_id')
    # def _compute_stock_qty(self):
    #     for rec in self:
    #         rec.stock_qty = rec.product_id.qty_available if rec.product_id else 0.0

    @api.depends('product_id', 'lot_id', 'requisition_type')
    def _compute_stock_qty(self):
        for rec in self:
            if rec.requisition_type == 'purchase' and rec.lot_id:
                rec.stock_qty = rec.lot_id.product_qty
            elif rec.product_id:
                rec.stock_qty = rec.product_id.qty_available
            else:
                rec.stock_qty = 0.0







# changed on jan 10 for duplication of product for the same car id
#     @api.onchange('product_id')
#     def onchange_product_id(self):
#         for rec in self:
#             rec.lot_id = False  # 🔥 IMPORTANT
#
#             if not rec.product_id:
#                 rec.description = False
#                 rec.uom = False
#                 rec.part_no = False
#                 rec.cost_price = False
#                 rec.is_stock = False
#                 return
#
#             # 🔒 DUPLICATE CHECK (ONLY FOR PURCHASE)
#             if (
#                     rec.requisition_type == 'purchase'
#                     and rec.requisition_id
#                     and rec.requisition_id.car_id
#             ):
#                 duplicate = self.env['material.purchase.requisition.line'].search([
#                     ('id', '!=', rec.id),
#                     ('product_id', '=', rec.product_id.id),
#                     ('requisition_type', '=', 'purchase'),
#                     ('requisition_id.car_id', '=', rec.requisition_id.car_id.id),
#                 ], limit=1)
#
#                 if duplicate:
#                     warning = {
#                         'title': 'Duplicate Product Not Allowed',
#                         'message': (
#                             f"The product '{rec.product_id.display_name}' "
#                             f"is already requested for this CAR ID "
#                         )
#                     }
#
#                     rec.product_id = False
#                     return {'warning': warning}
#
#             # 🔹 NORMAL EXISTING LOGIC
#             if rec.requisition_type == 'purchase':
#                 rec.description = rec.product_id.display_name
#             else:
#                 rec.description = False
#
#             rec.uom = rec.product_id.uom_id.id
#             rec.part_no = rec.product_id.default_code
#             rec.cost_price = rec.product_id.standard_price
#             rec.is_stock = rec.product_id.qty_available > 0


# function changed on jan 13
    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            rec.lot_id = False  # 🔥 IMPORTANT

            if not rec.product_id:
                rec.description = False
                rec.uom = False
                rec.part_no = False
                rec.cost_price = False
                rec.is_stock = False
                return

            # 🔒 DUPLICATE CHECK (WITHIN SAME REQUISITION FORM)
            if (
                    rec.requisition_type == 'purchase'
                    and rec.requisition_id
                    and rec.requisition_id.car_id
            ):
                for line in rec.requisition_id.requisition_line_ids:
                    if (
                            line.id != rec.id
                            and line.product_id == rec.product_id
                            and line.requisition_type == 'purchase'
                    ):
                        rec.product_id = False

                        return {
                            'warning': {
                                'title': 'Product Already Used',
                                'message': (
                                    f"The product '{line.product_id.display_name}' "
                                    f"is already selected for this CAR ID."
                                )
                            }
                        }

            # 🔹 NORMAL EXISTING LOGIC
            if rec.requisition_type == 'purchase':
                rec.description = rec.product_id.display_name
            else:
                rec.description = False

            rec.uom = rec.product_id.uom_id.id
            rec.part_no = rec.product_id.default_code
            rec.cost_price = rec.product_id.standard_price
            rec.is_stock = rec.product_id.qty_available > 0

    @api.onchange('requisition_type')
    def _onchange_requisition_type(self):
        for rec in self:
            if rec.requisition_type == 'internal':
                # 🔥 VERY IMPORTANT
                rec.lot_id = False

            rec.product_id = False
            rec.description = False
            rec.uom = False
            rec.part_no = False
            rec.cost_price = 0.0
            rec.sale_price = 0.0
            rec.stock_qty = 0.0
            rec.is_stock = False

    @api.onchange('part_no')
    def _onchange_part_no(self):
        for rec in self:
            if rec.part_no:
                product = self.env['product.product'].search([('default_code', '=', rec.part_no)], limit=1)
                if product:
                    rec.product_id = product.id
                    # rec.description = product.display_name
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




    @api.constrains('requisition_type', 'lot_id')
    def _check_lot_required_for_purchase(self):
        for rec in self:
            if rec.requisition_type == 'purchase' and not rec.lot_id:
                raise ValidationError("Lot / Car ID is mandatory for Purchase requisition.")



    @api.constrains('qty', 'lot_id', 'requisition_type')
    def _check_lot_stock_qty(self):
        for rec in self:
            if rec.requisition_type != 'purchase':
                continue
            if not rec.lot_id:
                continue
            if rec.lot_id.product_qty <= 0:
                continue

            if rec.qty > rec.lot_id.product_qty:
                raise ValidationError(
                    "Requested quantity exceeds available stock for this Lot / Car ID."
                )


class ProductProduct(models.Model):
    _inherit = 'product.product'
# added on jan 03 create write
    @api.model
    def create(self, vals):
        # Called from Material Purchase Requisition
        if self.env.context.get('default_set_non_inventory'):
            category = self.env['product.category'].search(
                [('name', '=', 'Non Inventory')], limit=1
            )
            if category:
                vals['categ_id'] = category.id

            # 🔥 IMPORTANT PART
            vals['tracking'] = 'lot'  # 👈 Track by Lot

        return super(ProductProduct, self).create(vals)

    def write(self, vals):
        if self.env.context.get('default_set_non_inventory'):
            category = self.env['product.category'].search(
                [('name', '=', 'Non Inventory')], limit=1
            )
            if category:
                vals['categ_id'] = category.id

            # 🔥 ensure tracking stays lot
            vals['tracking'] = 'lot'

        return super(ProductProduct, self).write(vals)





    # @api.model
    # def create(self, vals):
    #     # Check if flag is passed from MPR lines
    #     if self.env.context.get('default_set_non_inventory'):
    #         category = self.env['product.category'].search([('name', '=', 'Non Inventory')], limit=1)
    #         if category:
    #             vals['categ_id'] = category.id
    #
    #     return super().create(vals)
    #
    #
    #
    #
    # def write(self, vals):
    #     if self.env.context.get('default_set_non_inventory'):
    #         category = self.env['product.category'].search([('name', '=', 'Non Inventory')], limit=1)
    #         if category:
    #             vals['categ_id'] = category.id
    #     return super().write(vals)



