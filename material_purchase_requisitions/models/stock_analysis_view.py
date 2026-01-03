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




    # @api.model
    # def init(self):
    #     self._cr.execute("""
    #         CREATE OR REPLACE VIEW stock_analysis_view AS (
    #             SELECT
    #                 sm.id AS id,
    #                 sp.car_id AS car_id,
    #                 sm.product_id AS product_id,
    #                 sp.partner_id AS vendor_id,
    #                 sm.product_uom AS uom_id,
    #                 sm.part_location AS part_location,
    #                 sp.custom_requisition_id AS epr_id,
    #                 sp.id AS picking_id,
    #                 sm.available_qty AS available_qty,
    #                 sp.vehicle_name AS vehicle_name,
    #                 sp.vin_sn AS vin_sn
    #
    #             FROM stock_move sm
    #             JOIN stock_picking sp ON sm.picking_id = sp.id
    #             JOIN product_product pp ON sm.product_id = pp.id
    #             JOIN product_template pt ON pp.product_tmpl_id = pt.id
    #             JOIN product_category pc ON pt.categ_id = pc.id
    #             WHERE sp.state = 'done'
    #               AND pc.name = 'Non Inventory'
    #               AND sp.car_id IS NOT NULL
    #               AND sm.available_qty > 0    -- Filter zero qty
    #         );
    #     """)

# dec31 added lot also

    # @api.model
    # def init(self):
    #     self._cr.execute("""
    #                      DROP VIEW IF EXISTS stock_analysis_view CASCADE;
    #
    #                      CREATE VIEW stock_analysis_view AS
    #                      (
    #                      SELECT sml.id                   AS id,
    #
    #                             sp.car_id                AS car_id,
    #                             sp.vehicle_name          AS vehicle_name,
    #                             sp.vin_sn                AS vin_sn,
    #
    #                             sm.product_id            AS product_id,
    #                             sp.partner_id            AS vendor_id,
    #                             sm.product_uom           AS uom_id,
    #                             sm.part_location         AS part_location,
    #
    #                             sp.custom_requisition_id AS epr_id,
    #                             sp.id                    AS picking_id,
    #
    #                             sm.available_qty         AS available_qty,
    #
    #                             sml.lot_id               AS lot_id
    #
    #
    #
    #                      FROM stock_move sm
    #                               JOIN stock_picking sp ON sm.picking_id = sp.id
    #                               JOIN stock_move_line sml ON sml.move_id = sm.id
    #                               JOIN product_product pp ON sm.product_id = pp.id
    #                               JOIN product_template pt ON pp.product_tmpl_id = pt.id
    #                               JOIN product_category pc ON pt.categ_id = pc.id
    #
    #                      WHERE sp.state = 'done'
    #                        AND pc.name = 'Non Inventory'
    #                        AND sp.car_id IS NOT NULL
    #                        AND sm.available_qty > 0
    #                        AND sml.lot_id IS NOT NULL
    #
    #                        -- 🔥 ONLY requisition-approved lot
    #                        AND sml.epr_id = sp.custom_requisition_id
    #                          );
    #                      """)
# added in dec 31 to disply lotwise qty and lot if you want use above function
#     @api.model
#     def init(self):
#         self._cr.execute("""
#                          DROP VIEW IF EXISTS stock_analysis_view CASCADE;
#
#                          CREATE VIEW stock_analysis_view AS
#                          (
#                          SELECT sml.id                   AS id,
#
#                                 sp.car_id                AS car_id,
#                                 sp.vehicle_name          AS vehicle_name,
#                                 sp.vin_sn                AS vin_sn,
#
#                                 sm.product_id            AS product_id,
#                                 sp.partner_id            AS vendor_id,
#                                 sm.product_uom           AS uom_id,
#                                 sm.part_location         AS part_location,
#
#                                 sp.custom_requisition_id AS epr_id,
#                                 sp.id                    AS picking_id,
#
#                                 sm.available_qty         AS available_qty,
#
#                                 sml.lot_id               AS lot_id,
#
#                                 -- ✅ REQUISITION STOCK QTY (LOT WISE)
#                                 sml.quantity           AS lot_qty
#
#                          FROM stock_move sm
#                                   JOIN stock_picking sp ON sm.picking_id = sp.id
#                                   JOIN stock_move_line sml ON sml.move_id = sm.id
#
#                              -- 🔥 JOIN requisition line
#                                   JOIN material_purchase_requisition_line mprl
#                                        ON mprl.requisition_id = sp.custom_requisition_id
#                                            AND mprl.product_id = sm.product_id
#                                            AND mprl.lot_id = sml.lot_id
#
#
#                                   JOIN product_product pp ON sm.product_id = pp.id
#                                   JOIN product_template pt ON pp.product_tmpl_id = pt.id
#                                   JOIN product_category pc ON pt.categ_id = pc.id
#
#                          WHERE sp.state = 'done'
#                            AND pc.name = 'Non Inventory'
#                            AND sm.available_qty > 0
#                            AND sp.car_id IS NOT NULL
#                            AND sml.lot_id IS NOT NULL
#
#                            -- 🔥 only requisition-approved moves
#                            AND sml.epr_id = sp.custom_requisition_id
#                              );
#                          """)


# added this in jan2 for getting lot quantity wise reccord and it will disappera if it is zero
    @api.model
    def init(self):
        self._cr.execute("""
                         DROP VIEW IF EXISTS stock_analysis_view CASCADE;

                         CREATE VIEW stock_analysis_view AS
                         (
                         SELECT sml.id                   AS id,

                                sp.car_id,
                                sp.vehicle_name,
                                sp.vin_sn,

                                sm.product_id,
                                sp.partner_id            AS vendor_id,
                                sm.product_uom           AS uom_id,
                                sm.part_location,

                                sp.custom_requisition_id AS epr_id,
                                sp.id                    AS picking_id,

                                sm.available_qty,
                                sml.lot_id,

                                -- show balance only AFTER approve
                                CASE
                                    WHEN epr.state IN ('approve', 'partial')
                                        THEN mprl.stock_qty
                                    ELSE sml.quantity
                                    END                  AS lot_qty

                         FROM stock_move sm
                                  JOIN stock_picking sp ON sm.picking_id = sp.id
                                  JOIN stock_move_line sml ON sml.move_id = sm.id

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
                           AND pc.name = 'Non Inventory'
                           AND sp.car_id IS NOT NULL
                           AND sml.lot_id IS NOT NULL
                           AND sml.epr_id = epr.id

                           -- 🔥 HIDE ONLY WHEN APPROVED AND STOCK ZERO
                           AND NOT (
                             epr.state IN ('approve', 'partial')
                                 AND mprl.stock_qty = 0
                             )
                             );
                         """)














