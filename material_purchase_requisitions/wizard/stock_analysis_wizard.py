import base64
from io import BytesIO

from xlsxwriter import Workbook

from odoo import models, fields, api
import xlsxwriter

class StockAnalysisWizard(models.TransientModel):
    _name = 'stock.analysis.wizard'
    _description = 'Stock Analysis Wizard'

    car_id = fields.Many2one('vehicle.details', string='Car ID', required=True)

    # def action_print_xlsx(self):
    #
    #     domain = [('state', '=', 'done')]
    #     if self.car_id:
    #         domain.append(('car_id', '=', self.car_id.id))
    #
    #     pickings = self.env['stock.picking'].search(domain, order='date_done asc')
    #
    #     # Create Excel file in memory
    #     fp = BytesIO()
    #     workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
    #     sheet = workbook.add_worksheet("Stock Analysis")
    #
    #     # Formats
    #     bold = workbook.add_format({'bold': True})
    #
    #     # Column widths
    #     sheet.set_column(0, 0, 40)
    #     sheet.set_column(1, 1, 15)
    #     sheet.set_column(2, 2, 25)
    #     sheet.set_column(3, 3, 10)
    #
    #     # -------------------------------------------------------------
    #     # HEADER SECTION (Uses car_id.title_en and car_id.vin_sn)
    #     # -------------------------------------------------------------
    #     sheet.write(0, 0, 'Car ID:', bold)
    #     sheet.write(0, 1, self.car_id.car_id or '')
    #
    #     sheet.write(1, 0, 'Vehicle Name:', bold)
    #     sheet.write(1, 1, self.car_id.title_en or '')
    #
    #     sheet.write(2, 0, 'VIN:', bold)
    #     sheet.write(2, 1, self.car_id.vin_sn or '')
    #
    #     # -------------------------------------------------------------
    #     # TABLE HEADERS
    #     # -------------------------------------------------------------
    #     row = 4
    #     headers = ['Product', 'Stock Qty', 'Vendor', 'UoM']
    #     for col, title in enumerate(headers):
    #         sheet.write(row, col, title, bold)
    #     row += 1
    #
    #     # -------------------------------------------------------------
    #     # DATA ROWS
    #     # -------------------------------------------------------------
    #     for picking in pickings:
    #         vendor_name = picking.partner_id.name or ''
    #
    #         for move in picking.move_ids_without_package:
    #             sheet.write(row, 0, move.product_id.display_name)
    #             sheet.write(row, 1, float(move.quantity_done))
    #             sheet.write(row, 2, vendor_name)
    #             sheet.write(row, 3, move.product_uom.name)
    #             row += 1
    #
    #     workbook.close()
    #     fp.seek(0)
    #
    #     # Save as attachment
    #     attachment = self.env['ir.attachment'].create({
    #         'name': 'Stock_Analysis.xlsx',
    #         'type': 'binary',
    #         'datas': base64.b64encode(fp.read()),
    #         'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    #     })
    #
    #     # Return download action
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': f'/web/content/{attachment.id}?download=true',
    #         'target': 'self',
    #     }

    def action_print_xlsx(self):

        domain = [('state', '=', 'done')]
        if self.car_id:
            domain.append(('car_id', '=', self.car_id.id))

        pickings = self.env['stock.picking'].search(domain, order='date_done asc')

        # Create Excel file
        fp = BytesIO()
        workbook = xlsxwriter.Workbook(fp, {'in_memory': True})
        sheet = workbook.add_worksheet("Stock Analysis")

        bold = workbook.add_format({'bold': True})

        # Column widths
        sheet.set_column(0, 0, 40)  # Product
        sheet.set_column(1, 1, 15)  # Stock Qty
        sheet.set_column(2, 2, 25)  # Vendor
        sheet.set_column(3, 3, 10)  # UoM
        sheet.set_column(4, 4, 25)  # Part Location  ← NEW

        # -------------------------------------------------------------
        # HEADER
        # -------------------------------------------------------------
        sheet.write(0, 0, 'Car ID:', bold)
        sheet.write(0, 1, self.car_id.title_en or '')

        sheet.write(1, 0, 'Vehicle Name:', bold)
        sheet.write(1, 1, self.car_id.title_en or '')

        sheet.write(2, 0, 'VIN:', bold)
        sheet.write(2, 1, self.car_id.vin_sn or '')

        # -------------------------------------------------------------
        # TABLE HEADERS
        # -------------------------------------------------------------
        row = 4
        headers = ['Product', 'Stock Qty (Done)', 'Vendor', 'UoM', 'Part Location']
        for col, title in enumerate(headers):
            sheet.write(row, col, title, bold)
        row += 1

        # -------------------------------------------------------------
        # DATA ROWS
        # -------------------------------------------------------------
        for picking in pickings:
            vendor_name = picking.partner_id.name or ''

            for move in picking.move_ids_without_package:
                stock_qty = move.available_qty or 0
                uom_qty = move.quantity or 0
                part_location = move.location_id.display_name or ''  # ← NEW

                sheet.write(row, 0, move.product_id.display_name)
                sheet.write(row, 1, stock_qty)
                sheet.write(row, 2, vendor_name)
                sheet.write(row, 3, uom_qty)
                sheet.write(row, 4, part_location)  # ← NEW
                row += 1

        workbook.close()
        fp.seek(0)

        # Save as attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'Stock_Analysis.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(fp.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
