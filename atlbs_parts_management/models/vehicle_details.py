from odoo import models, fields

class VehicleDetails(models.Model):
    _name = 'vehicle.details'
    _description = 'Vehicle Details'

    name = fields.Char(string='Vehicle Name', required=True)
    vin_sn = fields.Char(string='VIN / Serial Number')
