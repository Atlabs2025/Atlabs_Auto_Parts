from odoo import models, fields, api
from odoo.exceptions import ValidationError
import requests
import logging


_logger = logging.getLogger(__name__)


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

    @api.model
    def cron_sync_inventory_feed(self):

        url = "https://api.kavak.com/karzaty/customer/instavid/inventory-feed"

        headers = {
            "Authorization": "9e7ba5v1-66af-4363-85a5-2a258fe16be1"
        }

        try:
            response = requests.get(url, headers=headers, timeout=30)

            _logger.info("Inventory Feed STATUS CODE: %s", response.status_code)

            if response.status_code != 200:
                _logger.error("Failed to fetch inventory feed")
                return

            data = response.json()

            # Handle response structure
            if isinstance(data, list):
                vehicles = data
            else:
                vehicles = data.get("body", [])

            _logger.info("TOTAL VEHICLES RECEIVED: %s", len(vehicles))

            for item in vehicles:
                try:
                    car_id = str(item.get("car_id") or "")
                    vin = item.get("VIN")

                    if not vin:
                        _logger.warning("Skipped record without VIN")
                        continue

                    #  Build title properly
                    year = str(item.get("year") or "")
                    make = item.get("make") or ""
                    model = item.get("model") or ""
                    trim = item.get("trim") or ""

                    title = " ".join(filter(None, [year, make, model, trim]))

                    _logger.info("Processing VIN: %s | Title: %s", vin, title)

                    # Check duplicate
                    existing = self.search([('vin_sn', '=', vin)], limit=1)

                    if existing:
                        _logger.info("Duplicate found, skipping VIN: %s", vin)
                        continue

                    # Create record
                    self.create({
                        'car_id': car_id,
                        'title_en': title,
                        'vin_sn': vin,
                    })

                    _logger.info("Created successfully VIN: %s", vin)

                except Exception as inner_error:
                    _logger.error("Error creating record for VIN %s: %s", vin, inner_error)

        except Exception as e:
            _logger.error("Cron Sync Inventory Feed Error: %s", e)



# commented this code on feb 25
    # @api.model
    # def cron_sync_inventory_feed(self):
    #     url = "https://api.kavak.com/karzaty/customer/instavid/inventory-feed"
    #
    #     headers = {
    #         "Authorization": "9e7ba5v1-66af-4363-85a5-2a258fe16be1"
    #     }
    #
    #     try:
    #         response = requests.get(url, headers=headers)
    #
    #         _logger.info("STATUS CODE: %s", response.status_code)
    #
    #         if response.status_code != 200:
    #             return
    #
    #         data = response.json()
    #
    #         if isinstance(data, list):
    #             vehicles = data
    #         else:
    #             vehicles = data.get("body", [])
    #
    #         _logger.info("TOTAL VEHICLES: %s", len(vehicles))
    #
    #         for item in vehicles:
    #
    #             try:
    #                 car_id = str(item.get("car_id"))
    #                 vin = item.get("VIN")
    #                 make = item.get("make") or "Unknown Vehicle"
    #
    #                 _logger.info("Processing VIN: %s", vin)
    #
    #                 if not vin:
    #                     continue
    #
    #                 existing = self.search([('vin_sn', '=', vin)], limit=1)
    #
    #                 if existing:
    #                     _logger.info("Duplicate found: %s", vin)
    #                     continue
    #
    #                 self.create({
    #                     'car_id': car_id,
    #                     'title_en': make,
    #                     'vin_sn': vin,
    #                 })
    #
    #                 _logger.info("Created: %s", vin)
    #
    #             except Exception as inner_error:
    #                 _logger.error("Error creating record: %s", inner_error)
    #
    #     except Exception as e:
    #         _logger.error("Cron Sync Error: %s", e)
    #







