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



    @api.model
    def init(self):
        self._cr.execute(""" 
            CREATE OR REPLACE VIEW stock_analysis_view AS (
                SELECT
                    sm.id AS id,
                    sp.car_id AS car_id,              
                    sm.product_id AS product_id,
                    sp.partner_id AS vendor_id,
                    sm.product_uom AS uom_id,
                    sm.part_location AS part_location,
                    sp.custom_requisition_id AS epr_id,
                    sp.id AS picking_id,
                    sm.available_qty AS available_qty,
                    sp.vehicle_name AS vehicle_name,  
                    sp.vin_sn AS vin_sn
                FROM stock_move sm
                JOIN stock_picking sp ON sm.picking_id = sp.id
                JOIN product_product pp ON sm.product_id = pp.id
                JOIN product_template pt ON pp.product_tmpl_id = pt.id
                JOIN product_category pc ON pt.categ_id = pc.id
                WHERE sp.state = 'done'
                  AND pc.name = 'Non Inventory'
                  AND sp.car_id IS NOT NULL
            );
        """)

