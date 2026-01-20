from odoo import models, fields, api

class StockAnalysisView(models.Model):
    _name = "stock.analysis.view"
    _description = "Stock Analysis Report View"
    _auto = False

    car_id = fields.Many2one('vehicle.details', string="Car")
    vehicle_name = fields.Char(string="Vehicle")
    vin_sn = fields.Char(string="VIN/SN")
    product_id = fields.Many2one('product.product', string="Product")
    # qty = fields.Float("Qty")
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    uom_id = fields.Many2one('uom.uom', string="UoM")
    part_location = fields.Char("Part Location")       # ✔ char field

    epr_id = fields.Many2one(
        'material.purchase.requisition',
        string="EPR Number",
        help="Click to open EPR"
    )  # ✔ Only this field needed

    picking_id = fields.Many2one("stock.picking", string="Picking")
    available_qty = fields.Float("Available Qty")


    lot_id = fields.Many2one("stock.lot", string="Lot / Car ID")

    lot_qty = fields.Float(string="Lotwise Quantity")

    employee_id = fields.Many2one('hr.employee',string="Employee")




# jan 06 function
#     @api.model
#     def init(self):
#         self._cr.execute("""
#                          DROP VIEW IF EXISTS stock_analysis_view CASCADE;
#
#                          CREATE VIEW stock_analysis_view AS
#                          (
#                          SELECT sml.id                   AS id,
#
#                                 sp.car_id,
#                                 sp.vehicle_name,
#                                 sp.vin_sn,
#
#                                 sm.product_id,
#                                 sp.partner_id            AS vendor_id,
#                                 sm.product_uom           AS uom_id,
#                                 sm.part_location,
#
#                                 sp.custom_requisition_id AS epr_id,
#                                 epr.employee_id          AS employee_id,
#                                 sp.id                    AS picking_id,
#
#                                 sm.available_qty,
#                                 sml.lot_id,
#
#                                 -- 🔥 FINAL DISPLAY QTY
#                                 ROUND(
#                                         (
#                                             CASE
#                                                 WHEN epr.state IN ('approve', 'partial')
#                                                     THEN COALESCE(mprl.stock_qty, 0)
#                                                 ELSE COALESCE(sml.quantity, 0)
#                                                 END
#                                             ):: numeric
#                                     , 6)                 AS lot_qty
#
#                          FROM stock_move sm
#                                   JOIN stock_picking sp ON sm.picking_id = sp.id
#                                   JOIN stock_move_line sml ON sml.move_id = sm.id
#
#                                   JOIN material_purchase_requisition epr
#                                        ON epr.id = sp.custom_requisition_id
#
#                                   JOIN material_purchase_requisition_line mprl
#                                        ON mprl.requisition_id = epr.id
#                                            AND mprl.product_id = sm.product_id
#                                            AND mprl.lot_id = sml.lot_id
#
#                                   JOIN product_product pp ON sm.product_id = pp.id
#                                   JOIN product_template pt ON pp.product_tmpl_id = pt.id
#                                   JOIN product_category pc ON pt.categ_id = pc.id
#
#                          WHERE sp.state = 'done'
#                            AND pc.name = 'Non Inventory'
#                            AND sp.car_id IS NOT NULL
#                            AND sml.lot_id IS NOT NULL
#                            AND sml.epr_id = epr.id
#
#                            -- 🔒 STRICT ZERO HIDE
#                            AND ROUND(
#                                        (
#                                            CASE
#                                                WHEN epr.state IN ('approve', 'partial')
#                                                    THEN COALESCE(mprl.stock_qty, 0)
#                                                ELSE COALESCE(sml.quantity, 0)
#                                                END
#                                            ):: numeric
#                                    , 6) > 0
#                              );
#                          """)
#
#


# jan20 function added
    @api.model
    def init(self):
        self._cr.execute("""
            DROP VIEW IF EXISTS stock_analysis_view CASCADE;

            CREATE VIEW stock_analysis_view AS
            (
                SELECT
                    sml.id AS id,

                    sp.car_id,
                    sp.vehicle_name,
                    sp.vin_sn,

                    sm.product_id,
                    sp.partner_id AS vendor_id,
                    sm.product_uom AS uom_id,
                    sm.part_location,

                    sp.custom_requisition_id AS epr_id,
                    epr.employee_id AS employee_id,
                    sp.id AS picking_id,

                    sm.available_qty,
                    sml.lot_id,

                    --  NET QTY = OUT - RETURN
                    ROUND(
                        (
                            COALESCE(sml.quantity, 0)
                            -
                            COALESCE((
                                SELECT SUM(rml.quantity)
                                FROM stock_move rm
                                JOIN stock_move_line rml
                                    ON rml.move_id = rm.id
                                WHERE rm.origin_returned_move_id = sm.id
                                  AND rml.lot_id = sml.lot_id
                            ), 0)
                        )::numeric,
                        6
                    ) AS lot_qty

                FROM stock_move sm
                JOIN stock_picking sp
                    ON sm.picking_id = sp.id
                JOIN stock_move_line sml
                    ON sml.move_id = sm.id

                JOIN material_purchase_requisition epr
                    ON epr.id = sp.custom_requisition_id

                JOIN material_purchase_requisition_line mprl
                    ON mprl.requisition_id = epr.id
                    AND mprl.product_id = sm.product_id
                    AND mprl.lot_id = sml.lot_id

                JOIN product_product pp ON sm.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                JOIN product_category pc ON pt.categ_id = pc.id

                WHERE sp.state = 'done'

                  --  ONLY DELIVERY (NOT RETURN PICKING)
                  AND sm.origin_returned_move_id IS NULL

                  --  NON INVENTORY
                  AND pc.name = 'Non Inventory'

                  --  REQUIRED
                  AND sp.car_id IS NOT NULL
                  AND sml.lot_id IS NOT NULL
                  AND sml.epr_id = epr.id

                  -- 🔒 HIDE ZERO / NEGATIVE QTY
                  AND (
                      COALESCE(sml.quantity, 0)
                      -
                      COALESCE((
                          SELECT SUM(rml.quantity)
                          FROM stock_move rm
                          JOIN stock_move_line rml
                              ON rml.move_id = rm.id
                          WHERE rm.origin_returned_move_id = sm.id
                            AND rml.lot_id = sml.lot_id
                      ), 0)
                  ) > 0
            );
        """)












