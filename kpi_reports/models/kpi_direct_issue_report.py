from odoo import models, fields, tools


class KpiDirectIssueReport(models.Model):
    _name = 'kpi.direct.issue.report'
    _description = 'Direct Issue KPI Report'
    _auto = False
    _rec_name = 'product_id'
    _order = 'issue_date desc,id desc'

    issue_date = fields.Date(string='Date of Issuance')

    picking_id = fields.Many2one(
        'stock.picking',
        string='Delivery'
    )

    car_id = fields.Many2one(
        'vehicle.details',
        string='Car ID'
    )
    vehicle_name = fields.Char(string='Vehicle Name')

    vin_sn = fields.Char(string='VIN #')

    department_id = fields.Many2one(
        'hr.department',
        string='Department'
    )

    product_id = fields.Many2one(
        'product.product',
        string='Part'
    )

    issued_qty = fields.Float(string='Issued Qty')

    unit_price = fields.Float(string='Unit Price')

    total_value = fields.Float(string='Total Value')

    employee_id = fields.Many2one(
        'hr.employee',
        string='Taken By'
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW kpi_direct_issue_report AS (

                SELECT
                    row_number() OVER(
                        ORDER BY sp.date_done DESC, sm.id DESC
                    ) AS id,

                    sp.id AS picking_id,

                    sp.date_done::date AS issue_date,

                    sp.car_id AS car_id,
                    sp.vehicle_name AS vehicle_name,
                    vd.vin_sn AS vin_sn,

                    sp.department_id AS department_id,

                    sp.employee_id AS employee_id,

                    sm.product_id AS product_id,

                    sm.product_uom_qty AS issued_qty,

                    COALESCE(
                    (pp.standard_price->>'1')::numeric,
                    0
                ) AS unit_price,

                (
                    sm.product_uom_qty
                    * COALESCE(
                        (pp.standard_price->>'1')::numeric,
                        0
                    )
                ) AS total_value
                FROM stock_move sm

                JOIN stock_picking sp
                    ON sp.id = sm.picking_id

                LEFT JOIN vehicle_details vd
                    ON vd.id = sp.car_id

                JOIN product_product pp
                    ON pp.id = sm.product_id

                JOIN stock_picking_type spt
                    ON spt.id = sp.picking_type_id

                WHERE
                    spt.code = 'outgoing'
                    AND sp.state = 'done'
                    AND sp.custom_requisition_id IS NULL

            )
        """)