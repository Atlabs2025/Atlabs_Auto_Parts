from odoo import models, fields

class VehicleDetails(models.Model):
    _name = 'vehicle.details'
    _description = 'Vehicle Details'
    _rec_name = 'car_id'


    car_id = fields.Char(string="Car ID")
    title_en = fields.Char(string='Vehicle Name', required=True)
    vin_sn = fields.Char(string='VIN / Serial Number')
    # plate_no = fields.Char(string='Plate Number')
    # driver = fields.Char(string='Driver')
