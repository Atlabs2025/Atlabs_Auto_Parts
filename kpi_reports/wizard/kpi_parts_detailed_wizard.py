from odoo import models, fields


class KpiPartsDetailedWizard(models.TransientModel):
    _name = 'kpi.parts.detailed.wizard'
    _description = 'Detailed KPI Parts Wizard'

    kpi_point = fields.Selection([
        ('parts_arranged_1_day', 'Parts Arranged ≤ 1 Day'),
        ('parts_arranged_1_3_days', 'Parts Arranged 1 – 3 Days'),
        ('parts_arranged_above_3_days', 'Parts Arranged > 3 Days'),
        ('total_parts_purchased', 'Total Parts Purchased'),
        ('total_parts_received', 'Total Parts Received'),
        ('total_parts_issued', 'Total Parts Issued'),
        ('utilization_percentage', 'Utilization %'),
        ('returned_parts', 'Returned Parts'),
        ('genuine_parts_spend', 'Genuine Parts Spend %'),
        ('aftermarket_parts_spend', 'Aftermarket Parts Spend %'),
        ('production_spend', 'Production Spend'),
        ('vendor_spend', 'Vendor Spend'),
    ], string="KPI Point", required=True)

    def action_view(self):
        self.ensure_one()

        domain = []

        if self.kpi_point == 'parts_arranged_1_day':
            domain = [
                ('request_date', '!=', False),
                ('received_date', '!=', False),
                ('days_to_received', '<=', 1),
            ]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Parts Arranged ≤ 1 Day',
            'res_model': 'kpi.parts.report',
            'view_mode': 'list',
            'domain': domain,
            'target': 'current',
        }



    # # PLACEHOLDER BUTTONS (logic later)
    # def action_view(self):
    #     return {'type': 'ir.actions.act_window_close'}

    def action_print_xlsx(self):
        return {'type': 'ir.actions.act_window_close'}
