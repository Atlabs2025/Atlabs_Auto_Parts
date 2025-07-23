from odoo import models, fields,api



class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    oe_number_ids = fields.Many2many('fleet.oe.number', string="OE Numbers")




class OENumber(models.Model):
    _name = 'fleet.oe.number'
    _description = 'OE Number Master'

    name = fields.Char(string="OE Number", required=True)
    description = fields.Text(string="Description")
    vehicle_ids = fields.Many2many('fleet.vehicle', string="Linked Vehicles")

