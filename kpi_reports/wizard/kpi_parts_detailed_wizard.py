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

        # ≤ 1 Day
        if self.kpi_point == 'parts_arranged_1_day':
            domain = [
                ('request_date', '!=', False),
                ('received_date', '!=', False),
                ('days_to_received', '<=', 1),
            ]

        # 1–3 Days
        elif self.kpi_point == 'parts_arranged_1_3_days':
            domain = [
                ('request_date', '!=', False),
                ('received_date', '!=', False),
                ('days_to_received', '>=', 1),
                ('days_to_received', '<=', 3),
            ]
            # above 3 days
        elif self.kpi_point == 'parts_arranged_above_3_days':
            domain = [
                ('request_date', '!=', False),
                ('received_date', '!=', False),
                ('days_to_received', '>', 3),
            ]


        return {
            'type': 'ir.actions.act_window',
            'name': 'KPI Parts Report',
            'res_model': 'kpi.parts.report',
            'view_mode': 'list',
            'domain': domain,
            'target': 'current',
        }



    # def action_print_xlsx(self):
    #     import io
    #     import base64
    #     import xlsxwriter
    #
    #     # ✅ SEARCH ON REPORT MODEL (NOT WIZARD)
    #     records = self.env['kpi.parts.report'].search([
    #         ('request_date', '!=', False),
    #         ('received_date', '!=', False),
    #         ('days_to_received', '<=', 1),
    #     ])
    #
    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    #     sheet = workbook.add_worksheet('Parts ≤ 1 Day')
    #
    #     # -----------------------
    #     # Formats
    #     # -----------------------
    #     header_fmt = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
    #     text_fmt = workbook.add_format({'border': 1})
    #     num_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
    #     int_fmt = workbook.add_format({'border': 1})
    #
    #     # -----------------------
    #     # Headers (MATCH VIEW)
    #     # -----------------------
    #     headers = [
    #         'SN', 'Car', 'VIN', 'Department', 'EPR',
    #         'Employee', 'Request Date', 'Part Type',
    #         'Product', 'Parts Price', 'Requested Qty',
    #         'Received Qty', 'Analytic Account',
    #         'PO Number', 'PO Date', 'Vendor',
    #         'Received Date', 'Days to Received', 'Issue Date'
    #     ]
    #
    #     for col, header in enumerate(headers):
    #         sheet.write(0, col, header, header_fmt)
    #         sheet.set_column(col, col, 18)
    #
    #     # -----------------------
    #     # Data
    #     # -----------------------
    #     row = 1
    #     sn = 1
    #
    #     for rec in records:
    #         sheet.write(row, 0, sn, int_fmt)
    #         sheet.write(row, 1, rec.car_id.car_id or '', text_fmt)
    #         sheet.write(row, 2, rec.vin_sn or '', text_fmt)
    #         sheet.write(row, 3, rec.department_id.name or '', text_fmt)
    #         sheet.write(row, 4, rec.epr_id.name or '', text_fmt)
    #         sheet.write(row, 5, rec.employee_id.name or '', text_fmt)
    #         sheet.write(row, 6, str(rec.request_date or ''), text_fmt)
    #         sheet.write(row, 7, rec.part_type or '', text_fmt)
    #         sheet.write(row, 8, rec.product_id.display_name or '', text_fmt)
    #         sheet.write(row, 9, rec.parts_price or 0.0, num_fmt)
    #         sheet.write(row, 10, rec.requested_qty or 0.0, num_fmt)
    #         sheet.write(row, 11, rec.received_qty or 0.0, num_fmt)
    #         sheet.write(row, 12, rec.analytic_account_id.name or '', text_fmt)
    #         sheet.write(row, 13, rec.po_number or '', text_fmt)
    #         sheet.write(row, 14, str(rec.po_date or ''), text_fmt)
    #         sheet.write(row, 15, rec.vendor_id.name or '', text_fmt)
    #         sheet.write(row, 16, str(rec.received_date or ''), text_fmt)
    #         sheet.write(row, 17, rec.days_to_received or 0, int_fmt)
    #         sheet.write(row, 18, str(rec.issue_date or ''), text_fmt)
    #
    #         row += 1
    #         sn += 1
    #
    #     workbook.close()
    #     output.seek(0)
    #
    #     # -----------------------
    #     # Attachment (YOUR STYLE ✅)
    #     # -----------------------
    #     attachment = self.env['ir.attachment'].create({
    #         'name': 'Parts_Arranged_Less_Than_1_Day.xlsx',
    #         'type': 'binary',
    #         'datas': base64.b64encode(output.read()),
    #         'res_model': self._name,
    #         'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    #     })
    #
    #     # -----------------------
    #     # Download
    #     # -----------------------
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': '/web/content/%s?download=true' % attachment.id,
    #         'target': 'self',
    #     }
    #

    def action_print_xlsx(self):
        self.ensure_one()

        import io
        import base64
        import xlsxwriter

        # --------------------------------
        # KPI BASED DOMAIN (SAME AS VIEW)
        # --------------------------------
        domain = []

        if self.kpi_point == 'parts_arranged_1_day':
            domain = [
                ('request_date', '!=', False),
                ('received_date', '!=', False),
                ('days_to_received', '<=', 1),
            ]
            sheet_name = 'Parts ≤ 1 Day'
            file_name = 'Parts_Arranged_Less_Than_1_Day.xlsx'

        elif self.kpi_point == 'parts_arranged_1_3_days':
            domain = [
                ('request_date', '!=', False),
                ('received_date', '!=', False),
                ('days_to_received', '>=', 1),
                ('days_to_received', '<=', 3),
            ]
            sheet_name = 'Parts 1–3 Days'
            file_name = 'Parts_Arranged_1_3_Days.xlsx'

        elif self.kpi_point == 'parts_arranged_above_3_days':
            domain = [
                ('request_date', '!=', False),
                ('received_date', '!=', False),
                ('days_to_received', '>', 3),
            ]
            sheet_name = 'Parts Above 3 Days'
            file_name = 'Parts_Arranged_Above_3_Days.xlsx'

        else:
            domain = []
            sheet_name = 'KPI Parts Report'
            file_name = 'KPI_Parts_Report.xlsx'

        # --------------------------------
        # SEARCH ON REPORT MODEL
        # --------------------------------
        records = self.env['kpi.parts.report'].search(domain)

        # --------------------------------
        # XLSX
        # --------------------------------
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet(sheet_name)

        # Formats
        header_fmt = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
        text_fmt = workbook.add_format({'border': 1})
        num_fmt = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        int_fmt = workbook.add_format({'border': 1})

        # Headers (MATCH VIEW)
        headers = [
            'SN', 'Car', 'VIN', 'Department', 'EPR',
            'Employee', 'Request Date', 'Part Type',
            'Product', 'Parts Price', 'Requested Qty',
            'Received Qty', 'Analytic Account',
            'PO Number', 'PO Date', 'Vendor',
            'Received Date', 'Days to Received', 'Issue Date'
        ]

        for col, header in enumerate(headers):
            sheet.write(0, col, header, header_fmt)
            sheet.set_column(col, col, 18)

        # Data
        row = 1
        sn = 1

        for rec in records:
            sheet.write(row, 0, sn, int_fmt)
            sheet.write(row, 1, rec.car_id.car_id or '', text_fmt)
            sheet.write(row, 2, rec.vin_sn or '', text_fmt)
            sheet.write(row, 3, rec.department_id.name or '', text_fmt)
            sheet.write(row, 4, rec.epr_id.name or '', text_fmt)
            sheet.write(row, 5, rec.employee_id.name or '', text_fmt)
            sheet.write(row, 6, str(rec.request_date or ''), text_fmt)
            sheet.write(row, 7, rec.part_type or '', text_fmt)
            sheet.write(row, 8, rec.product_id.display_name or '', text_fmt)
            sheet.write(row, 9, rec.parts_price or 0.0, num_fmt)
            sheet.write(row, 10, rec.requested_qty or 0.0, num_fmt)
            sheet.write(row, 11, rec.received_qty or 0.0, num_fmt)
            sheet.write(row, 12, rec.analytic_account_id.name or '', text_fmt)
            sheet.write(row, 13, rec.po_number or '', text_fmt)
            sheet.write(row, 14, str(rec.po_date or ''), text_fmt)
            sheet.write(row, 15, rec.vendor_id.name or '', text_fmt)
            sheet.write(row, 16, str(rec.received_date or ''), text_fmt)
            sheet.write(row, 17, rec.days_to_received or 0, int_fmt)
            sheet.write(row, 18, str(rec.issue_date or ''), text_fmt)

            row += 1
            sn += 1

        workbook.close()
        output.seek(0)

        # --------------------------------
        # ATTACHMENT (YOUR STYLE ✅)
        # --------------------------------
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'res_model': self._name,
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'self',
        }
