from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import csv
from io import BytesIO, StringIO
from openpyxl import load_workbook
from odoo.exceptions import UserError

class VehicleGoogleImport(models.TransientModel):
    _name = "vehicle.google.import"
    _description = "Import Vehicles from File"

    uploaded_file = fields.Binary("Upload CSV File", required=True)
    file_name = fields.Char("Filename")
    use_first_row_as_header = fields.Boolean("First row contains headers", default=True)

    def action_import(self):
        if not self.uploaded_file:
            raise UserError("Please upload a CSV file.")

        # Decode uploaded file
        try:
            decoded = base64.b64decode(self.uploaded_file)
            content = decoded.decode('utf-8', errors='replace')
        except Exception:
            raise UserError("Unable to read the uploaded file. Ensure it is a valid CSV file.")

        sio = StringIO(content, newline='')

        # Detect header or no header
        reader = csv.DictReader(sio) if self.use_first_row_as_header else csv.reader(sio)

        Vehicle = self.env['vehicle.details']
        created = 0
        updated = 0

        # -------------------------------------------------------
        # CASE 1: CSV WITH HEADER
        # -------------------------------------------------------
        if isinstance(reader, csv.DictReader):
            for row in reader:

                if not row or all(v in (None, "", " ") for v in row.values()):
                    continue

                # Clean row
                data = {}
                for k, v in row.items():
                    if not k:
                        continue
                    key = k.strip().lower()
                    value = v.strip() if isinstance(v, str) else (v or "")
                    data[key] = value

                # MAP CSV → Odoo Fields
                car_id = data.get('name') or data.get('car_id') or data.get('vehicle')
                # vin = data.get('vin') or data.get('vin_sn') or data.get('chassis')
                vin = (data.get('vin') or data.get('vin_sn') or data.get('vin_no') or data.get('chassis'))
                title = data.get('title_en') or data.get('plate_no') or data.get('plate')
                # driver = data.get('driver') or data.get('driver_name')

                if not car_id and not vin and not title:
                    continue

                # Search by unique identifiers
                domain = []
                if vin:
                    domain = [('vin_sn', '=', vin)]
                elif title:
                    domain = [('title_en', '=', title)]
                elif car_id:
                    domain = [('car_id', '=', car_id)]

                existing = Vehicle.search(domain, limit=1)

                vals = {}
                if car_id: vals['car_id'] = car_id
                if vin: vals['vin_sn'] = vin
                if title: vals['title_en'] = title
                # if driver: vals['driver'] = driver

                if existing:
                    existing.write(vals)
                    updated += 1
                else:
                    Vehicle.create(vals)
                    created += 1

        # -------------------------------------------------------
        # CASE 2: CSV WITHOUT HEADER
        # -------------------------------------------------------
        else:
            for row in reader:
                if not row:
                    continue

                car_id = row[0].strip() if len(row) > 0 else False
                vin = row[1].strip() if len(row) > 1 else False
                title = row[2].strip() if len(row) > 2 else False
                # driver = row[3].strip() if len(row) > 3 else False

                if not car_id and not vin and not title:
                    continue

                domain = []
                if vin:
                    domain = [('vin_sn', '=', vin)]
                elif title:
                    domain = [('title_en', '=', title)]
                elif car_id:
                    domain = [('car_id', '=', car_id)]

                existing = Vehicle.search(domain, limit=1)

                vals = {}
                if car_id: vals['car_id'] = car_id
                if vin: vals['vin_sn'] = vin
                if title: vals['title_en'] = title
                # if driver: vals['driver'] = driver

                if existing:
                    existing.write(vals)
                    updated += 1
                else:
                    Vehicle.create(vals)
                    created += 1

        message = f"Import completed: {created} created, {updated} updated."

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': "Vehicle Import",
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }



