import datetime

from odoo import models, fields, tools
from odoo import http
from odoo.http import request
import io
import xlsxwriter
from datetime import datetime, date


class KpiPartsReport(models.Model):
    _name = "kpi.parts.report"
    _description = "KPI Parts Report"
    _auto = False

    sn = fields.Integer(string="S.N")

    car_id = fields.Many2one('vehicle.details', string="Car ID"
                                                       "")
    vin_sn = fields.Char(string="VIN/SN")
    department_id = fields.Many2one('hr.department',string="Department")

    employee_id = fields.Many2one(
        'hr.employee',
        string="Requester"
    )

    request_date = fields.Date(string="Request Date")

    epr_id = fields.Many2one(
        'material.purchase.requisition',
        string="EPR Number"
    )

    product_id = fields.Many2one('product.product', string="Parts")
    parts_price = fields.Float(string="Parts Price")
    po_date = fields.Date(string="PO Date")
    vendor_id = fields.Many2one('res.partner', string="Vendor")

    received_date = fields.Date(string="Received Date")
    days_to_received = fields.Integer(string="Days to Received")
    issue_date = fields.Date(string="Issue Date")





    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""
            CREATE VIEW kpi_parts_report AS (
                SELECT
                    row_number() OVER () AS id,
                    row_number() OVER () AS sn,

                    epr.car_id                  AS car_id,
                    vd.vin_sn                   AS vin_sn,
                    epr.department_id           AS department_id,
                    epr.employee_id             AS employee_id,
                    epr.request_date            AS request_date,
                    epr.id                      AS epr_id,

                    eprl.product_id             AS product_id,
                    eprl.qty                    AS qty,

                    po.date_order               AS po_date,
                    po.partner_id               AS vendor_id,
                    pol.price_unit              AS parts_price,

                    -- ✅ GRN received date
                    grn.date_done::date         AS received_date,

                    -- ✅ Days to received
                    CASE
                        WHEN grn.date_done IS NOT NULL
                             AND epr.request_date IS NOT NULL
                        THEN (grn.date_done::date - epr.request_date)
                        ELSE NULL
                    END                          AS days_to_received,

                    -- ✅ Issue date (internal picking)
                    issue.scheduled_date::date AS issue_date


                FROM material_purchase_requisition epr

                LEFT JOIN vehicle_details vd
                    ON vd.id = epr.car_id

                LEFT JOIN material_purchase_requisition_line eprl
                    ON eprl.requisition_id = epr.id

                LEFT JOIN purchase_order po
                    ON po.custom_requisition_id = epr.id

                LEFT JOIN purchase_order_line pol
                    ON pol.order_id = po.id
                   AND pol.product_id = eprl.product_id

                -- 🔹 stock move from PO line
                LEFT JOIN stock_move sm
                    ON sm.purchase_line_id = pol.id

                -- 🔹 GRN picking (incoming)
                LEFT JOIN stock_picking grn
                    ON grn.id = sm.picking_id
                   AND grn.state = 'done'
                   AND grn.picking_type_id IN (
                        SELECT id FROM stock_picking_type WHERE code = 'incoming'
                   )

                -- 🔹 Issue picking (internal)
                LEFT JOIN stock_picking issue
                    ON issue.custom_requisition_id = epr.id
                   AND issue.state = 'done'
                   AND issue.picking_type_id IN (
                        SELECT id FROM stock_picking_type WHERE code = 'internal'
                   )
            )
        """)

    # sn = fields.Integer(string="S.N")
    # car_id = fields.Char(string="Car ID")
    # vin = fields.Char(string="VIN")
    # # car_detail = fields.Char(string="Car Detail")
    # department = fields.Char(string="Department")
    # requester_name = fields.Char(string="Requester Name")
    # request_date = fields.Date(string="Request Date")
    #
    # cost_type = fields.Selection([
    #     ('pro', 'PRO'),
    #     ('gw', 'GW'),
    #     ('afs', 'AFS'),
    #     ('ad', 'AD'),
    #     ('wa', 'WA'),
    # ], string="Cost Type")
    #
    # part_id = fields.Many2one('product.product', string="Part")
    # qty = fields.Float(string="QTY")
    #
    # po_date = fields.Date(string="PO Date")
    # vendor_id = fields.Many2one('res.partner', string="Vendor")
    # parts_price = fields.Float(string="Parts Price")
    # unit_price = fields.Float(string="Unit Price")
    # total = fields.Float(string="Total")
    #
    # received_date = fields.Date(string="Received Date")
    # days_to_received = fields.Integer(string="Days to Received")
    # issue_date = fields.Date(string="Issue Date")
    # taken_by = fields.Char(string="Taken By")
    #






    def action_print_pdf(self):
        return self.env.ref(
            'kpi_reports.action_kpi_parts_report_pdf'
        ).report_action(self)

    def action_print_xlsx(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/kpi_parts_report/xlsx',
            'target': 'self',
        }






# class KpiPartsReportController(http.Controller):

    # @http.route('/kpi_parts_report/xlsx', type='http', auth='user')
    # def download_kpi_parts_report_xlsx(self, **kwargs):
    #
    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #     sheet = workbook.add_worksheet('KPI Parts Report')
    #
    #     # 🔹 Formats
    #     header_fmt = workbook.add_format({'bold': True, 'border': 1})
    #     text_fmt = workbook.add_format({'border': 1})
    #     date_fmt = workbook.add_format({
    #         'border': 1,
    #         'num_format': 'yyyy-mm-dd'
    #     })
    #
    #     headers = [
    #         'S.N', 'Car', 'VIN', 'Department', 'Requester',
    #         'Request Date', 'Product', 'Qty',
    #         'PO Date', 'Vendor', 'Part Price',
    #         'Received Date', 'Days To Receive', 'Issue Date'
    #     ]
    #
    #     for col, header in enumerate(headers):
    #         sheet.write(0, col, header, header_fmt)
    #         sheet.set_column(col, col, 18)
    #
    #     # 🔹 Fetch from VIEW
    #     request.env.cr.execute("""
    #             SELECT
    #                 sn,
    #                 car_id,
    #                 vin_sn,
    #                 department_id,
    #                 employee_id,
    #                 request_date,
    #                 product_id,
    #                 qty,
    #                 po_date,
    #                 vendor_id,
    #                 parts_price,
    #                 received_date,
    #                 days_to_received,
    #                 issue_date
    #             FROM kpi_parts_report
    #             ORDER BY request_date
    #         """)
    #
    #     rows = request.env.cr.fetchall()
    #
    #     def to_datetime(val):
    #         """Convert string/date to datetime safely"""
    #         if not val:
    #             return None
    #         if isinstance(val, datetime):
    #             return val
    #         if isinstance(val, date):
    #             return datetime.combine(val, datetime.min.time())
    #         if isinstance(val, str):
    #             try:
    #                 return datetime.strptime(val, '%Y-%m-%d')
    #             except Exception:
    #                 return None
    #         return None
    #
    #     row_no = 1
    #     for row in rows:
    #         (
    #             sn,
    #             car_id,
    #             vin_sn,
    #             department_id,
    #             employee_id,
    #             request_date,
    #             product_id,
    #             qty,
    #             po_date,
    #             vendor_id,
    #             parts_price,
    #             received_date,
    #             days_to_received,
    #             issue_date
    #         ) = row
    #
    #         # 🔹 ID → Name
    #         car_name = request.env['vehicle.details'].browse(car_id).display_name if car_id else ''
    #         department_name = request.env['hr.department'].browse(department_id).name if department_id else ''
    #         requester_name = request.env['hr.employee'].browse(employee_id).name if employee_id else ''
    #         product_name = request.env['product.product'].browse(product_id).display_name if product_id else ''
    #         vendor_name = request.env['res.partner'].browse(vendor_id).name if vendor_id else ''
    #
    #         values = [
    #             sn,
    #             car_name,
    #             vin_sn,
    #             department_name,
    #             requester_name,
    #             to_datetime(request_date),
    #             product_name,
    #             qty,
    #             to_datetime(po_date),
    #             vendor_name,
    #             parts_price,
    #             to_datetime(received_date),
    #             days_to_received,
    #             to_datetime(issue_date),
    #         ]
    #
    #         for col, value in enumerate(values):
    #             if isinstance(value, datetime):
    #                 sheet.write_datetime(row_no, col, value, date_fmt)
    #             else:
    #                 sheet.write(row_no, col, value if value is not None else '', text_fmt)
    #
    #         row_no += 1
    #
    #     workbook.close()
    #     output.seek(0)
    #
    #     return request.make_response(
    #         output.read(),
    #         headers=[
    #             ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    #             ('Content-Disposition', 'attachment; filename="kpi_parts_report.xlsx"')
    #         ]
    #     )
    # @http.route('/kpi_parts_report/xlsx', type='http', auth='user')
    # def download_kpi_parts_report_xlsx(self, **kwargs):
    #
    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #     sheet = workbook.add_worksheet('KPI Parts Report')
    #
    #     # 🔹 Header
    #     headers = [
    #         'S.N', 'Car', 'VIN', 'Department', 'Requester',
    #         'Request Date', 'Product', 'Qty',
    #         'PO Date', 'Vendor', 'Part Price',
    #         'Received Date', 'Days To Receive', 'Issue Date'
    #     ]
    #
    #     for col, header in enumerate(headers):
    #         sheet.write(0, col, header)
    #
    #     # 🔹 Query VIEW directly
    #     request.env.cr.execute("""
    #         SELECT
    #             sn,
    #             car_id,
    #             vin_sn,
    #             department_id,
    #             employee_id,
    #             request_date,
    #             product_id,
    #             qty,
    #             po_date,
    #             vendor_id,
    #             parts_price,
    #             received_date,
    #             days_to_received,
    #             issue_date
    #         FROM kpi_parts_report
    #         ORDER BY request_date
    #     """)
    #
    #     rows = request.env.cr.fetchall()
    #
    #     row_no = 1
    #     for row in rows:
    #         for col, value in enumerate(row):
    #             sheet.write(row_no, col, value)
    #         row_no += 1
    #
    #     workbook.close()
    #     output.seek(0)
    #
    #     return request.make_response(
    #         output.read(),
    #         headers=[
    #             ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
    #             ('Content-Disposition', 'attachment; filename="kpi_parts_report.xlsx"')
    #         ]
    #     )
    #


