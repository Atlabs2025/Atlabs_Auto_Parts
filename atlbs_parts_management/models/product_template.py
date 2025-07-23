from odoo import models, fields, api



class ProductTemplate(models.Model):
    _inherit = 'product.template'

    group_id = fields.Many2one('product.group', string="Group")
    sub_group_id = fields.Many2one('product.sub.group', string="Sub Group")

    used_in_vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        'product_template_fleet_vehicle_rel',
        'product_tmpl_id',
        'vehicle_id',
        string="Used in Vehicles"
    )

    oe_number_line_ids = fields.One2many('product.oe.line', 'product_tmpl_id', string="OE Number Lines")
    manufacturer_id = fields.Many2one('fleet.vehicle.model.brand', string="Manufacturer")
    characteristic_line_ids = fields.One2many(
        'product.characteristic.line',
        'product_tmpl_id',
        string='Characteristics'
    )

    technical_data_ids = fields.One2many(
        'product.technical.data',
        'product_tmpl_id',
        string='Technical Data'
    )


    # def name_get(self):
    #     result = []
    #     for product in self:
    #         name = product.default_code or product.name
    #         result.append((product.id, name))
    #     return result

    # def name_get(self):
    #     result = []
    #     for rec in self:
    #         if rec.default_code:
    #             name = rec.default_code
    #         else:
    #             name = rec.name
    #         result.append((rec.id, name))
    #     return result



class ProductGroup(models.Model):
    _name = 'product.group'
    _description = 'Product Group'

    name = fields.Char(string="Group Name", required=True)

class ProductSubGroup(models.Model):
    _name = 'product.sub.group'
    _description = 'Product Sub Group'

    name = fields.Char(string="Sub Group Name", required=True)
    group_id = fields.Many2one('product.group', string="Parent Group")


class ProductOENumberLine(models.Model):
    _name = 'product.oe.line'
    _description = 'Product OE Number Line'

    product_tmpl_id = fields.Many2one('product.template', string="Product", ondelete='cascade')
    oe_number_id = fields.Many2many('fleet.oe.number', string="OE Number", required=True)
    description = fields.Text(related='oe_number_id.description', string="Description", readonly=True)
    manufacturer_id = fields.Many2one('fleet.vehicle.model.brand', string="Manufacturer")


class ProductCharacteristicLine(models.Model):
    _name = 'product.characteristic.line'
    _description = 'Product Characteristic Line'

    product_tmpl_id = fields.Many2one('product.template', string="Product", ondelete='cascade')
    key = fields.Char(string="Key", required=True)
    value = fields.Char(string="Value", required=True)


class ProductTechnicalData(models.Model):
    _name = 'product.technical.data'
    _description = 'Technical Data'

    product_tmpl_id = fields.Many2one('product.template', string="Product Template", ondelete='cascade')
    caption = fields.Char(string="Caption", required=True)
    technical_link = fields.Char(string="Technical Data Link")
