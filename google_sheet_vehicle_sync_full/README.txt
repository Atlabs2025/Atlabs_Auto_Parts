Google Sheet Vehicle Sync (CSV Import)
=====================================

Instructions:
1. Install the module 'Google Sheet Vehicle Sync (CSV Import)'.
2. Ensure the 'requests' Python package is installed on the Odoo server:
   pip install requests
3. Create or paste a Google Sheet URL into the import wizard:
   - If you paste the normal Google Sheets URL, the wizard will convert it to a CSV export URL automatically.
   - Alternatively, publish the sheet as CSV or use the export link.
4. Go to: Vehicles -> Google Sheet -> Import Vehicles
   Paste the sheet URL and click 'Import Vehicles'.
5. The module will create or update records in 'vehicle.details' (matching by vin -> plate -> name).
6. To enable automatic periodic imports, enable and configure the cron in Settings -> Technical -> Automation -> Scheduled Actions (search 'Vehicle Google Sheet Import (auto)') and set it active.

Columns supported (case-insensitive):
- name, vehicle name, vehicle
- vin, vin_sn, VIN / Serial Number
- plate_no, plate, plate number
- driver, driver_name

