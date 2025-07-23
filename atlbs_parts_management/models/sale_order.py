from odoo import models, fields,api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    description = fields.Char(string="Description")


    part_number_id = fields.Many2one(
        'product.template',
        string='Part Number',
        domain="[('default_code', '!=', False)]"
    )


    @api.onchange('part_number_id')
    def _onchange_part_number_id(self):
        if self.part_number_id:
            self.product_id = self.part_number_id.product_variant_id


