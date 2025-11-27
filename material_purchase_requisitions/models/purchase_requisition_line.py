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
    # product_id = fields.Many2one(
    #     'product.product',
    #     string='Product',
    #     # required=True,
    # )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        domain="[('categ_id.name', '=', 'Non Inventory')] if requisition_type == 'purchase' else []",
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
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Nature Of Cost',
        copy=True,
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
    part_type = fields.Selection([
        ('after_market', 'After Market'),
        ('genuine', 'Genuine'),
        ('used', 'Used'),
    ], string='Part Type', default='')

    part_no = fields.Char(string="Part Number")
    product_template_id = fields.Many2one('product.template', string="Part Number")
    # part_no = fields.Many2one('product.product', string="Part Number", domain="[('default_code', '!=', False)]")
    cost_price = fields.Float(string="Cost Price")
    sale_price = fields.Float(string="Sale Price")
    # stock_qty = fields.Float(string="On Hand Quantity", readonly=True)

    stock_qty = fields.Float(string="Stock", compute="_compute_stock_qty", readonly=True)

    from_job_card = fields.Boolean(
        string='From Job Card')

    image = fields.Image(string="Image")
    is_stock = fields.Boolean(string="Stock Available", default=False)





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

    @api.depends('product_id')
    def _compute_stock_qty(self):
        for rec in self:
            rec.stock_qty = rec.product_id.qty_available if rec.product_id else 0.0
# commented default code
#     @api.onchange('product_id')
#     def onchange_product_id(self):
#         for rec in self:
#             # rec.description = rec.product_id.name
#             rec.description = rec.product_id.display_name
#             rec.uom = rec.product_id.uom_id.id
#             rec.part_no =rec.product_id.default_code
#             # rec.sale_price =rec.product_id.lst_price
#             rec.cost_price =rec.product_id.standard_price

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.description = rec.product_id.display_name
                rec.uom = rec.product_id.uom_id.id
                rec.part_no = rec.product_id.default_code
                rec.cost_price = rec.product_id.standard_price

                # ✔ Auto tick is_stock based on available quantity
                rec.is_stock = rec.product_id.qty_available > 0
            else:
                rec.description = False
                rec.uom = False
                rec.part_no = False
                rec.cost_price = False
                rec.is_stock = False

    @api.onchange('requisition_type')
    def _onchange_requisition_type(self):
        if self.requisition_type == 'purchase':
            self.is_stock = False



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




class ProductProduct(models.Model):
    _inherit = 'product.product'


    @api.model
    def create(self, vals):
        # Check if flag is passed from MPR lines
        if self.env.context.get('default_set_non_inventory'):
            category = self.env['product.category'].search([('name', '=', 'Non Inventory')], limit=1)
            if category:
                vals['categ_id'] = category.id

        return super().create(vals)




