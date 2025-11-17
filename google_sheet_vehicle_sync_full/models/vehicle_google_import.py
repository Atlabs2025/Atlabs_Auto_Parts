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
                vin = data.get('vin') or data.get('vin_sn') or data.get('chassis')
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



    # def action_import(self):
    #     if not self.uploaded_file:
    #         raise UserError("Please upload a CSV file.")
    #
    #     # Decode uploaded file
    #     try:
    #         decoded = base64.b64decode(self.uploaded_file)
    #         content = decoded.decode('utf-8', errors='replace')
    #     except Exception:
    #         raise UserError("Unable to read the uploaded file. Ensure it is a valid CSV file.")
    #
    #     # Use newline='' to prevent CSV line break errors
    #     sio = StringIO(content, newline='')
    #
    #     # Detect header or no header
    #     reader = csv.DictReader(sio) if self.use_first_row_as_header else csv.reader(sio)
    #
    #     Vehicle = self.env['vehicle.details']
    #     created = 0
    #     updated = 0
    #
    #     # -------------------------------------------------------
    #     # CASE 1: CSV WITH HEADER
    #     # -------------------------------------------------------
    #     if isinstance(reader, csv.DictReader):
    #         for row in reader:
    #
    #             # Full skip if row is empty or contains only None
    #             if not row or all(v in (None, "", " ") for v in row.values()):
    #                 continue
    #
    #             # Clean data safely (avoid None.strip error)
    #             data = {}
    #             for k, v in row.items():
    #                 if not k:  # Skip empty header columns
    #                     continue
    #                 key = k.strip().lower() if isinstance(k, str) else str(k).lower()
    #
    #                 if isinstance(v, str):
    #                     value = v.strip()
    #                 else:
    #                     value = v if v else ""
    #
    #                 data[key] = value
    #
    #             # Map columns (accept multiple possible naming styles)
    #             name = data.get('name') or data.get('vehicle name') or data.get('vehicle')
    #             vin = data.get('vin') or data.get('vin_sn') or data.get('chassis no')
    #             plate = data.get('plate_no') or data.get('plate') or data.get('plate number')
    #             driver = data.get('driver') or data.get('driver_name')
    #
    #             # Skip useless row
    #             if not name and not vin and not plate:
    #                 continue
    #
    #             # Search logic
    #             domain = []
    #             if vin:
    #                 domain = [('vin_sn', '=', vin)]
    #             elif plate:
    #                 domain = [('plate_no', '=', plate)]
    #             elif name:
    #                 domain = [('name', '=', name)]
    #
    #             existing = Vehicle.search(domain, limit=1) if domain else None
    #
    #             # Prepare create/update values
    #             vals = {}
    #             if name: vals['name'] = name
    #             if vin: vals['vin_sn'] = vin
    #             if plate: vals['plate_no'] = plate
    #             if driver: vals['driver'] = driver
    #
    #             # Write or create
    #             if existing:
    #                 existing.write(vals)
    #                 updated += 1
    #             else:
    #                 Vehicle.create(vals)
    #                 created += 1
    #
    #     # -------------------------------------------------------
    #     # CASE 2: CSV WITHOUT HEADER
    #     # -------------------------------------------------------
    #     else:
    #         for row in reader:
    #             if not row or len(row) == 0:
    #                 continue
    #
    #             # Read by index safely
    #             name = row[0].strip() if len(row) > 0 and isinstance(row[0], str) else False
    #             vin = row[1].strip() if len(row) > 1 and isinstance(row[1], str) else False
    #             plate = row[2].strip() if len(row) > 2 and isinstance(row[2], str) else False
    #             driver = row[3].strip() if len(row) > 3 and isinstance(row[3], str) else False
    #
    #             if not name and not vin and not plate:
    #                 continue
    #
    #             domain = []
    #             if vin:
    #                 domain = [('vin_sn', '=', vin)]
    #             elif plate:
    #                 domain = [('plate_no', '=', plate)]
    #             elif name:
    #                 domain = [('name', '=', name)]
    #
    #             existing = Vehicle.search(domain, limit=1) if domain else None
    #
    #             vals = {}
    #             if name: vals['name'] = name
    #             if vin: vals['vin_sn'] = vin
    #             if plate: vals['plate_no'] = plate
    #             if driver: vals['driver'] = driver
    #
    #             if existing:
    #                 existing.write(vals)
    #                 updated += 1
    #             else:
    #                 Vehicle.create(vals)
    #                 created += 1
    #
    #     # Notification
    #     message = f"Import completed: {created} created, {updated} updated."
    #
    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'display_notification',
    #         'params': {
    #             'title': "Vehicle Import",
    #             'message': message,
    #             'type': 'success',
    #             'sticky': False,
    #         }
    #     }

