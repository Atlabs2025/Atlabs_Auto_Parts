from odoo import models, fields, api
from odoo.exceptions import ValidationError


class VehicleDetails(models.Model):
    _name = 'vehicle.details'
    _description = 'Vehicle Details'
    _rec_name = 'car_id'


    car_id = fields.Char(string="Car ID")
    title_en = fields.Char(string='Vehicle Name', required=True)
    vin_sn = fields.Char(string='VIN / Serial Number')
    # plate_no = fields.Char(string='Plate Number')
    # driver = fields.Char(string='Driver')

    @api.constrains('car_id', 'vin_sn')
    def _check_duplicates(self):
        for rec in self:
            if rec.car_id:
                dup = self.search([
                    ('car_id', '=', rec.car_id),
                    ('id', '!=', rec.id)
                ])
                if dup:
                    raise ValidationError("Car ID already exists!")

            if rec.vin_sn:
                dup = self.search([
                    ('vin_sn', '=', rec.vin_sn),
                    ('id', '!=', rec.id)
                ])
                if dup:
                    raise ValidationError("VIN/Serial Number already exists!")
