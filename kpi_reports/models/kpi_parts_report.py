import base64
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

    # sn = fields.Integer(string="S.N")

    sn = fields.Char(string="S.N", compute="_compute_sn", store=False)



    car_id = fields.Many2one('vehicle.details', string="Car ID")
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

    part_type = fields.Char(string="Part Type")
    product_id = fields.Many2one('product.product', string="Parts")
    parts_price = fields.Float(string="Parts Price")
    po_number = fields.Char(string="PO Number")
    po_date = fields.Date(string="PO Date")
    vendor_id = fields.Many2one('res.partner', string="Vendor")

    received_date = fields.Date(string="Received Date")
    days_to_received = fields.Integer(string="Days to Received")
    issue_date = fields.Date(string="Issue Date")
    requested_qty = fields.Float(string="Requested Quantity")
    received_qty = fields.Float(string="Received Quantity")
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Nature Of Cost',
        copy=True, required=True
    )
    total_parts_received_percentage = fields.Float(
        string="Total Parts Received %",
        readonly=True
    )

    total_parts_issued_percentage = fields.Float(
        string="Total Parts Issued %",
        readonly=True
    )

    total_parts_available = fields.Integer(
        string='Total Parts Available',
        readonly=True
    )

    utilization_percentage = fields.Float(
        string="Utilization %",
        readonly=True
    )

    def _compute_sn(self):
        for i, rec in enumerate(self, start=1):
            rec.sn = str(i)




    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #
    #     self.env.cr.execute("""
    #         CREATE VIEW kpi_parts_report AS (
    #             SELECT
    #                 row_number() OVER () AS id,
    #
    #                 -- Requisition
    #                 epr.id                      AS epr_id,
    #                 epr.car_id                  AS car_id,
    #                 vd.vin_sn                   AS vin_sn,
    #                 epr.department_id           AS department_id,
    #                 epr.employee_id             AS employee_id,
    #                 epr.request_date            AS request_date,
    #
    #                 -- Product
    #                 eprl.part_type              AS part_type,
    #                 eprl.product_id             AS product_id,
    #                 eprl.qty                    AS requested_qty,
    #                 eprl.analytic_account_id    AS analytic_account_id,
    #
    #                 -- PO
    #                 po.name                     AS po_number,
    #                 po.date_order               AS po_date,
    #                 po.partner_id               AS vendor_id,
    #                 pol.price_unit              AS parts_price,
    #
    #                 -- GRN received date
    #                 grn.date_done::date         AS received_date,
    #
    #                 -- Received Quantity
    #                 COALESCE(recv.received_qty, 0) AS received_qty,
    #
    #                 -- Days to received
    #                 CASE
    #                     WHEN grn.date_done IS NOT NULL
    #                          AND epr.request_date IS NOT NULL
    #                     THEN (grn.date_done::date - epr.request_date)
    #                     ELSE NULL
    #                 END AS days_to_received,
    #
    #                 --  TOTAL PARTS RECEIVED % (RATIO 0–1)
    #                 CASE
    #                     WHEN eprl.qty > 0
    #                     THEN ROUND(
    #                         COALESCE(recv.received_qty, 0)::numeric
    #                         / eprl.qty::numeric,
    #                         4
    #                     )
    #                     ELSE 0
    #                 END AS total_parts_received_percentage,
    #
    #                 -- Issue date
    #                 issue_ml.issue_date         AS issue_date,
    #
    #                 --  Issued Quantity
    #                 COALESCE(issue_ml.issued_qty, 0) AS issued_qty,
    #
    #                 --  TOTAL PARTS ISSUED % (RATIO 0–1, NEVER > 1)
    #                 CASE
    #                     WHEN COALESCE(recv.received_qty, 0) > 0
    #                     THEN ROUND(
    #                         LEAST(
    #                             COALESCE(issue_ml.issued_qty, 0),
    #                             COALESCE(recv.received_qty, 0)
    #                         )::numeric
    #                         / recv.received_qty::numeric,
    #                         4
    #                     )
    #                     ELSE 0
    #                 END AS total_parts_issued_percentage
    #
    #             FROM material_purchase_requisition epr
    #
    #             LEFT JOIN vehicle_details vd
    #                 ON vd.id = epr.car_id
    #
    #             LEFT JOIN material_purchase_requisition_line eprl
    #                 ON eprl.requisition_id = epr.id
    #
    #             LEFT JOIN purchase_order po
    #                 ON po.custom_requisition_id = epr.id
    #
    #             LEFT JOIN purchase_order_line pol
    #                 ON pol.order_id = po.id
    #                AND pol.product_id = eprl.product_id
    #
    #             LEFT JOIN stock_move sm
    #                 ON sm.purchase_line_id = pol.id
    #
    #             LEFT JOIN stock_picking grn
    #                 ON grn.id = sm.picking_id
    #                AND grn.state = 'done'
    #                AND grn.picking_type_id IN (
    #                     SELECT id FROM stock_picking_type WHERE code = 'incoming'
    #                )
    #
    #             -- 🔹 Received Qty
    #             LEFT JOIN LATERAL (
    #                 SELECT
    #                     SUM(sml.quantity) AS received_qty
    #                 FROM stock_move_line sml
    #                 JOIN stock_move sm3 ON sm3.id = sml.move_id
    #                 JOIN stock_picking sp3 ON sp3.id = sm3.picking_id
    #                 JOIN stock_picking_type spt3 ON spt3.id = sp3.picking_type_id
    #                 WHERE
    #                     spt3.code = 'incoming'
    #                     AND sp3.state = 'done'
    #                     AND sm3.purchase_line_id = pol.id
    #             ) recv ON TRUE
    #
    #             -- 🔹 Issued Qty + Issue Date
    #             LEFT JOIN LATERAL (
    #                 SELECT
    #                     MIN(sml.date::date) AS issue_date,
    #                     SUM(sml.quantity)   AS issued_qty
    #                 FROM stock_move_line sml
    #                 JOIN stock_move sm2 ON sm2.id = sml.move_id
    #                 JOIN stock_picking sp2 ON sp2.id = sm2.picking_id
    #                 JOIN stock_picking_type spt2 ON spt2.id = sp2.picking_type_id
    #                 WHERE
    #                     spt2.code = 'outgoing'
    #                     AND sm2.product_id = eprl.product_id
    #                     AND sp2.state = 'done'
    #             ) issue_ml ON TRUE
    #         )
    #     """)

    # def init(self):
    #     tools.drop_view_if_exists(self.env.cr, self._table)
    #
    #     self.env.cr.execute("""
    #         CREATE VIEW kpi_parts_report AS (
    #             SELECT
    #                 row_number() OVER () AS id,
    #
    #                 -- Requisition
    #                 epr.id                      AS epr_id,
    #                 epr.car_id                  AS car_id,
    #                 vd.vin_sn                   AS vin_sn,
    #                 epr.department_id           AS department_id,
    #                 epr.employee_id             AS employee_id,
    #                 epr.request_date            AS request_date,
    #
    #                 -- Product
    #                 eprl.part_type              AS part_type,
    #                 eprl.product_id             AS product_id,
    #                 eprl.qty                    AS requested_qty,
    #                 eprl.analytic_account_id    AS analytic_account_id,
    #
    #                 -- PO
    #                 po.name                     AS po_number,
    #                 po.date_order               AS po_date,
    #                 po.partner_id               AS vendor_id,
    #                 pol.price_unit              AS parts_price,
    #
    #                 -- GRN
    #                 grn.date_done::date         AS received_date,
    #
    #                 -- Received Qty
    #                 COALESCE(recv.received_qty, 0) AS received_qty,
    #
    #                 -- Days to received
    #                 CASE
    #                     WHEN grn.date_done IS NOT NULL
    #                      AND epr.request_date IS NOT NULL
    #                     THEN (grn.date_done::date - epr.request_date)
    #                     ELSE NULL
    #                 END AS days_to_received,
    #
    #                 --  TOTAL PARTS RECEIVED %
    #                 CASE
    #                     WHEN eprl.qty > 0
    #                     THEN ROUND(
    #                         COALESCE(recv.received_qty, 0)::numeric
    #                         / eprl.qty::numeric,
    #                         4
    #                     )
    #                     ELSE 0
    #                 END AS total_parts_received_percentage,
    #
    #                 -- Issue
    #                 issue_ml.issue_date         AS issue_date,
    #                 COALESCE(issue_ml.issued_qty, 0) AS issued_qty,
    #
    #                 --  TOTAL PARTS ISSUED %
    #                 CASE
    #                     WHEN COALESCE(recv.received_qty, 0) > 0
    #                     THEN ROUND(
    #                         LEAST(
    #                             COALESCE(issue_ml.issued_qty, 0),
    #                             COALESCE(recv.received_qty, 0)
    #                         )::numeric
    #                         / recv.received_qty::numeric,
    #                         4
    #                     )
    #                     ELSE 0
    #                 END AS total_parts_issued_percentage,
    #
    #                 --  TOTAL PARTS AVAILABLE
    #                 ROUND(
    #                     COALESCE(recv.received_qty, 0)
    #                     - COALESCE(issue_ml.issued_qty, 0)
    #                 ) AS total_parts_available
    #
    #             FROM material_purchase_requisition epr
    #
    #             LEFT JOIN vehicle_details vd
    #                 ON vd.id = epr.car_id
    #
    #             LEFT JOIN material_purchase_requisition_line eprl
    #                 ON eprl.requisition_id = epr.id
    #
    #             LEFT JOIN purchase_order po
    #                 ON po.custom_requisition_id = epr.id
    #
    #             LEFT JOIN purchase_order_line pol
    #                 ON pol.order_id = po.id
    #                AND pol.product_id = eprl.product_id
    #
    #             LEFT JOIN stock_move sm
    #                 ON sm.purchase_line_id = pol.id
    #
    #             LEFT JOIN stock_picking grn
    #                 ON grn.id = sm.picking_id
    #                AND grn.state = 'done'
    #                AND grn.picking_type_id IN (
    #                     SELECT id FROM stock_picking_type WHERE code = 'incoming'
    #                )
    #
    #             -- 🔹 Received Qty
    #             LEFT JOIN LATERAL (
    #                 SELECT
    #                     SUM(sml.quantity) AS received_qty
    #                 FROM stock_move_line sml
    #                 JOIN stock_move sm3 ON sm3.id = sml.move_id
    #                 JOIN stock_picking sp3 ON sp3.id = sm3.picking_id
    #                 JOIN stock_picking_type spt3 ON spt3.id = sp3.picking_type_id
    #                 WHERE
    #                     spt3.code = 'incoming'
    #                     AND sp3.state = 'done'
    #                     AND sm3.purchase_line_id = pol.id
    #             ) recv ON TRUE
    #
    #             -- 🔹 Issued Qty
    #             LEFT JOIN LATERAL (
    #                 SELECT
    #                     MIN(sml.date::date) AS issue_date,
    #                     SUM(sml.quantity)   AS issued_qty
    #                 FROM stock_move_line sml
    #                 JOIN stock_move sm2 ON sm2.id = sml.move_id
    #                 JOIN stock_picking sp2 ON sp2.id = sm2.picking_id
    #                 JOIN stock_picking_type spt2 ON spt2.id = sp2.picking_type_id
    #                 WHERE
    #                     spt2.code = 'outgoing'
    #                     AND sm2.product_id = eprl.product_id
    #                     AND sp2.state = 'done'
    #             ) issue_ml ON TRUE
    #         )
    #     """)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""
            CREATE VIEW kpi_parts_report AS (
                SELECT
                    row_number() OVER () AS id,

                    -- Requisition
                    epr.id                    AS epr_id,
                    epr.car_id                AS car_id,
                    vd.vin_sn                 AS vin_sn,
                    epr.department_id         AS department_id,
                    epr.employee_id           AS employee_id,
                    epr.request_date          AS request_date,

                    -- Product
                    eprl.part_type            AS part_type,
                    eprl.product_id           AS product_id,
                    eprl.qty                  AS requested_qty,
                    eprl.analytic_account_id  AS analytic_account_id,

                    -- PO
                    po.name                   AS po_number,
                    po.date_order             AS po_date,
                    po.partner_id             AS vendor_id,
                    pol.price_unit            AS parts_price,

                    -- GRN
                    grn.date_done::date       AS received_date,

                    -- Received Qty
                    COALESCE(recv.received_qty, 0) AS received_qty,

                    -- Days to Received
                    CASE
                        WHEN grn.date_done IS NOT NULL
                         AND epr.request_date IS NOT NULL
                        THEN (grn.date_done::date - epr.request_date)
                        ELSE NULL
                    END AS days_to_received,

                    -- TOTAL PARTS RECEIVED %
                    CASE
                        WHEN eprl.qty > 0
                        THEN ROUND(
                            COALESCE(recv.received_qty, 0)::numeric
                            / eprl.qty::numeric,
                            4
                        )
                        ELSE 0
                    END AS total_parts_received_percentage,

                    -- Issue
                    issue_ml.issue_date       AS issue_date,
                    COALESCE(issue_ml.issued_qty, 0) AS issued_qty,

                    -- TOTAL PARTS ISSUED %
                    CASE
                        WHEN COALESCE(recv.received_qty, 0) > 0
                        THEN ROUND(
                            LEAST(
                                COALESCE(issue_ml.issued_qty, 0),
                                COALESCE(recv.received_qty, 0)
                            )::numeric
                            / recv.received_qty::numeric,
                            4
                        )
                        ELSE 0
                    END AS total_parts_issued_percentage,

                    -- TOTAL PARTS AVAILABLE
                    ROUND(
                        COALESCE(recv.received_qty, 0)
                        - COALESCE(issue_ml.issued_qty, 0)
                    ) AS total_parts_available,

                    -- ✅ UTILIZATION %
                    CASE
                        WHEN COALESCE(recv.received_qty, 0) > 0
                        THEN ROUND(
                            LEAST(
                                COALESCE(issue_ml.issued_qty, 0),
                                COALESCE(recv.received_qty, 0)
                            )::numeric
                            / recv.received_qty::numeric,
                            4
                        )
                        ELSE 0
                    END AS utilization_percentage

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

                LEFT JOIN stock_move sm
                    ON sm.purchase_line_id = pol.id

                LEFT JOIN stock_picking grn
                    ON grn.id = sm.picking_id
                   AND grn.state = 'done'
                   AND grn.picking_type_id IN (
                        SELECT id FROM stock_picking_type WHERE code = 'incoming'
                   )

                -- 🔹 Received Qty
                LEFT JOIN LATERAL (
                    SELECT
                        SUM(sml.quantity) AS received_qty
                    FROM stock_move_line sml
                    JOIN stock_move sm3 ON sm3.id = sml.move_id
                    JOIN stock_picking sp3 ON sp3.id = sm3.picking_id
                    JOIN stock_picking_type spt3 ON spt3.id = sp3.picking_type_id
                    WHERE
                        spt3.code = 'incoming'
                        AND sp3.state = 'done'
                        AND sm3.purchase_line_id = pol.id
                ) recv ON TRUE

                -- 🔹 Issued Qty
                LEFT JOIN LATERAL (
                    SELECT
                        MIN(sml.date::date) AS issue_date,
                        SUM(sml.quantity)   AS issued_qty
                    FROM stock_move_line sml
                    JOIN stock_move sm2 ON sm2.id = sml.move_id
                    JOIN stock_picking sp2 ON sp2.id = sm2.picking_id
                    JOIN stock_picking_type spt2 ON spt2.id = sp2.picking_type_id
                    WHERE
                        spt2.code = 'outgoing'
                        AND sm2.product_id = eprl.product_id
                        AND sp2.state = 'done'
                ) issue_ml ON TRUE
            )
        """)

    def action_print_xlsx(self):
        output = io.BytesIO()

        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet('KPI Parts Report')

        # -----------------------
        # Formats
        # -----------------------
        header_fmt = workbook.add_format({
            'bold': True,
            'border': 1,
            'align': 'center'
        })
        text_fmt = workbook.add_format({'border': 1})
        date_fmt = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd'})
        num_fmt = workbook.add_format({'border': 1})
        percent_fmt = workbook.add_format({
            'border': 1,
            'num_format': '0.00"%"'
        })

        # -----------------------
        # Headers
        # -----------------------
        headers = [
            'S.N', 'Car ID', 'VIN/SN', 'Department','EPR Number', 'Requester',
            'Request Date','Requested Qty','Received Qty','Total Parts Available','Utilization %','Utilization %', 'Part', 'Parts Price','PO Number' ,'PO Date', 'Vendor',
            'Received Date', 'Days To Received', 'Issue Date'
        ]

        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_fmt)
            sheet.set_column(col, col, 19)

        # -----------------------
        # Data
        # -----------------------
        row = 1
        sn = 1

        for rec in self.search([]):
            sheet.write(row, 0, sn, num_fmt)
            sheet.write(row, 1, rec.car_id.car_id or '', text_fmt)
            sheet.write(row, 2, rec.vin_sn or '', text_fmt)
            sheet.write(row, 3, rec.department_id.name or '', text_fmt)
            sheet.write(row, 4, rec.epr_id.name if rec.epr_id else '', text_fmt)
            sheet.write(row, 5, rec.employee_id.name or '', text_fmt)
            sheet.write(row, 6, rec.request_date or 0.0, date_fmt)
            sheet.write(row, 7, rec.requested_qty or 0.0, num_fmt)
            sheet.write(row, 8, rec.received_qty or '', num_fmt)
            sheet.write(row, 9, rec.total_parts_available or 0, num_fmt)
            sheet.write(row, 10, rec.product_id.display_name or '', text_fmt)
            sheet.write(row, 11, rec.parts_price or 0.0, num_fmt)
            sheet.write(row, 12, rec.po_date or '', date_fmt)
            sheet.write(row, 13, rec.vendor_id.name or '', text_fmt)
            sheet.write(row, 14, rec.received_date or '', date_fmt)
            sheet.write(row, 15, rec.days_to_received or 0, num_fmt)
            sheet.write(row, 16, rec.issue_date or '', date_fmt)


            row += 1
            sn += 1

        workbook.close()
        output.seek(0)

        # -----------------------
        # Attachment (IMPORTANT)
        # -----------------------
        attachment = self.env['ir.attachment'].create({
            'name': 'KPI_Parts_Report.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        # -----------------------
        # Download
        # -----------------------
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }


    def action_print_pdf(self):
        return self.env.ref(
            'kpi_reports.action_kpi_parts_report_pdf'
        ).report_action(self)








