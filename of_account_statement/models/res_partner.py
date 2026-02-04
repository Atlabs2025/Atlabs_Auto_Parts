# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models
import xlsxwriter
import io
import base64


class SupplierStatement(models.Model):
    _name = 'supplier.statement'
    _description = 'Supplier Statement'

    partner_id = fields.Many2one('res.partner', string="Partner", required=True, ondelete="cascade")
    move_id = fields.Many2one('account.move')
    move_line_id = fields.Many2one('account.move.line')
    bill_date = fields.Date(string="Bill Date")
    month = fields.Char(string="Month")
    reference = fields.Char(string="Reference")
    bill_reference = fields.Char(string="Bill Reference", related="move_id.ref")
    company = fields.Many2one(string="Company", related="move_id.company_id")
    due_date = fields.Date(string="Due Date", related="move_id.invoice_date_due")
    debit = fields.Float(string="Debit")
    credit = fields.Float(string="Credit")
    balance = fields.Float(string="Balance")
    status = fields.Selection(related="move_id.state")


class AccountMove(models.Model):
    _inherit = "account.move"

    paid_amount = fields.Monetary(
        string='Paid Amount', compute='_compute_paid_amount', store=True, help="Paid Amount.")
    month = fields.Char(string="Month", compute='_compute_month', store=True)

    @api.depends('invoice_date')
    def _compute_month(self):
        for rec in self:
            rec.month = rec.invoice_date.strftime("%B") if rec.invoice_date else ''

    @api.depends('amount_residual', 'state')
    def _compute_paid_amount(self):
        for rec in self:
            if rec.state != 'draft':
                rec.paid_amount = rec.amount_total - rec.amount_residual
            else:
                rec.paid_amount = 0.0

    @property
    def return_due_days(self):
        return (datetime.now().date() - self.invoice_date).days




class ResPartner(models.Model):
    _inherit = "res.partner"

    # Statements
    supplier_statement_ids = fields.One2many('supplier.statement', 'partner_id', string="Supplier Statements", compute="_compute_supp_statement")
    customer_statement_ids = fields.One2many('supplier.statement', 'partner_id', string="Customer Statements", compute="_compute_cust_statement")

    # Account Moves
    cust_acc_stat_line_ids = fields.Many2many(
        "account.move", string="Customer Account Statement", compute="compute_cust_statement_lines")
    supp_acc_stat_line_ids = fields.Many2many(
        "account.move", string="Supplier Account Statement", compute="compute_supplier_statement_lines")

    # Filters
    cust_from_date = fields.Date(string="From Date")
    cust_to_date = fields.Date(string="To Date")
    supp_from_date = fields.Date(string="From Date")
    supp_to_date = fields.Date(string="To Date")

    # Totals
    cust_overall_balance_due = fields.Float(compute='_get_cust_amounts_and_date')
    cust_total_overdue_amount = fields.Float(compute='_get_cust_amounts_and_date')
    supp_overall_balance_due = fields.Float(compute='_get_supp_amounts_and_date')
    supp_total_overdue_amount = fields.Float(compute='_get_supp_amounts_and_date')

    # extra added fields for installation
    duplicate_bank_partner_ids = fields.Many2one(
        'res.partner',
        string="Duplicate Bank Partners"
    )

    available_peppol_eas = fields.Char(string="")
    # ----------------------------
    # Compute statements
    # ----------------------------
    def _compute_cust_statement(self):
        Statement = self.env['supplier.statement']
        for partner in self:
            moves = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                # ('state', '=', 'posted','draft'),
                ('state', 'in', ['draft', 'posted']),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
                ('invoice_date', '>=', partner.cust_from_date if partner.cust_from_date else '1970-01-01'),
                ('invoice_date', '<=', partner.cust_to_date if partner.cust_to_date else fields.Date.today())
            ], order='invoice_date')

            # Remove old statements
            partner.customer_statement_ids.unlink()

            # Create new statement lines
            records = []
            for move in moves:
                rec_vals = {
                    'partner_id': partner.id,
                    'move_id': move.id,
                    'bill_date': move.invoice_date,
                    'month': move.invoice_date.strftime("%B") if move.invoice_date else '',
                    'reference': move.name,
                    'debit': move.amount_total if move.move_type in ['out_invoice'] else 0.0,
                    'credit': move.amount_total if move.move_type in ['out_refund'] else 0.0,
                    'balance': move.amount_residual,
                }
                records.append(Statement.create(rec_vals).id)
            partner.customer_statement_ids = [(6, 0, records)]

    def _compute_supp_statement(self):
        Statement = self.env['supplier.statement']
        for partner in self:
            moves = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('state', '=', 'posted'),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('invoice_date', '>=', partner.supp_from_date if partner.supp_from_date else '1970-01-01'),
                ('invoice_date', '<=', partner.supp_to_date if partner.supp_to_date else fields.Date.today())
            ], order='invoice_date')

            partner.supplier_statement_ids.unlink()
            records = []
            for move in moves:
                rec_vals = {
                    'partner_id': partner.id,
                    'move_id': move.id,
                    'bill_date': move.invoice_date,
                    'month': move.invoice_date.strftime("%B") if move.invoice_date else '',
                    'reference': move.name,
                    'debit': move.amount_total if move.move_type in ['in_invoice'] else 0.0,
                    'credit': move.amount_total if move.move_type in ['in_refund'] else 0.0,
                    'balance': move.amount_residual,
                }
                records.append(Statement.create(rec_vals).id)
            partner.supplier_statement_ids = [(6, 0, records)]

    # ----------------------------
    # Compute totals
    # ----------------------------
    @api.depends('cust_acc_stat_line_ids.amount_residual')
    def _get_cust_amounts_and_date(self):
        today = fields.Date.today()
        for partner in self:
            amount_due = sum(line.amount_residual for line in partner.cust_acc_stat_line_ids)
            overdue = sum(line.amount_residual for line in partner.cust_acc_stat_line_ids if line.invoice_date_due and line.invoice_date_due <= today)
            partner.cust_overall_balance_due = amount_due
            partner.cust_total_overdue_amount = overdue

    @api.depends('supp_acc_stat_line_ids.amount_residual')
    def _get_supp_amounts_and_date(self):
        today = fields.Date.today()
        for partner in self:
            amount_due = sum(line.amount_residual for line in partner.supp_acc_stat_line_ids)
            overdue = sum(line.amount_residual for line in partner.supp_acc_stat_line_ids if line.invoice_date_due and line.invoice_date_due <= today)
            partner.supp_overall_balance_due = amount_due
            partner.supp_total_overdue_amount = overdue

    # ----------------------------
    # Compute account moves for wizard filtering
    # ----------------------------
    def compute_cust_statement_lines(self):
        for partner in self:
            domain = [
                ('partner_id', '=', partner.id),
                ('state', '=', 'posted'),
                ('move_type', 'in', ['out_invoice', 'out_refund']),
            ]
            if partner.cust_from_date:
                domain.append(('invoice_date', '>=', partner.cust_from_date))
            if partner.cust_to_date:
                domain.append(('invoice_date', '<=', partner.cust_to_date))
            partner.cust_acc_stat_line_ids = self.env['account.move'].search(domain, order='invoice_date')

    def compute_supplier_statement_lines(self):
        for partner in self:
            domain = [
                ('partner_id', '=', partner.id),
                ('state', '=', 'posted'),
                ('move_type', 'in', ['in_invoice', 'in_refund']),
            ]
            if partner.supp_from_date:
                domain.append(('invoice_date', '>=', partner.supp_from_date))
            if partner.supp_to_date:
                domain.append(('invoice_date', '<=', partner.supp_to_date))
            partner.supp_acc_stat_line_ids = self.env['account.move'].search(domain, order='invoice_date')

    # ----------------------------
    # Excel Reports
    # ----------------------------
    # def _generate_excel_report(self, statement_type='customer'):
    #     self.ensure_one()
    #     output = io.BytesIO()
    #     workbook = xlsxwriter.Workbook(output)
    #     sheet = workbook.add_worksheet(f'{statement_type.title()} Statement')
    #
    #     bold = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
    #     date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
    #     currency_format = workbook.add_format({'num_format': '#,##0.00'})
    #
    #     sheet.merge_range('A1:F1', f'{statement_type.title()} Statement', bold)
    #     sheet.write('A2', 'Print Date:', bold)
    #     sheet.write('B2', fields.Datetime.now().strftime('%Y-%m-%d %H:%M'))
    #     sheet.write('A3', 'Partner Name:', bold)
    #     sheet.write('B3', self.name)
    #
    #     row = 5
    #     headers = ['Invoice Date', 'Reference', 'Due Date', 'Debit', 'Credit', 'Balance']
    #     for col, header in enumerate(headers):
    #         sheet.write(row, col, header, bold)
    #     row += 1
    #
    #     lines = self.customer_statement_ids if statement_type == 'customer' else self.supplier_statement_ids
    #     for line in lines:
    #         sheet.write(row, 0, line.move_id.invoice_date, date_format)
    #         sheet.write(row, 1, line.reference)
    #         sheet.write(row, 2, line.move_id.invoice_date_due, date_format)
    #         sheet.write(row, 3, line.debit, currency_format)
    #         sheet.write(row, 4, line.credit, currency_format)
    #         sheet.write(row, 5, line.balance, currency_format)
    #         row += 1
    #
    #     workbook.close()
    #     output.seek(0)
    #     xls_data = output.read()
    #     attachment = self.env['ir.attachment'].create({
    #         'name': f'{self.name}_{statement_type}_statement.xlsx',
    #         'type': 'binary',
    #         'datas': base64.b64encode(xls_data),
    #         'res_model': 'res.partner',
    #         'res_id': self.id,
    #     })
    #     return {
    #         'type': 'ir.actions.act_url',
    #         'url': f'/web/content/{attachment.id}?download=true',
    #         'target': 'new',
    #     }

    def _generate_excel_report(self, statement_type='customer'):
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output)
        sheet = workbook.add_worksheet(f'{statement_type.title()} Statement')

        # Formats
        bold = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
        date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
        currency_format = workbook.add_format({'num_format': '#,##0.00'})

        # Title
        sheet.merge_range('A1:F1', f'{statement_type.title()} Statement', bold)
        sheet.write('A2', 'Print Date:', bold)
        sheet.write('B2', fields.Datetime.now().strftime('%Y-%m-%d %H:%M'))
        sheet.write('A3', 'Partner Name:', bold)
        sheet.write('B3', self.name)

        row = 5
        headers = ['Invoice Date', 'Reference', 'Due Date', 'Debit', 'Credit', 'Balance']
        for col, header in enumerate(headers):
            sheet.write(row, col, header, bold)
        row += 1

        # Get lines
        if statement_type == 'customer':
            # Include draft and posted invoices
            lines = self.env['account.move'].search([
                ('partner_id', '=', self.id),
                ('move_type', 'in', ['out_invoice', 'out_refund', 'out_receipt']),
            ], order='invoice_date')
        else:
            # Supplier lines (already working)
            lines = self.supplier_statement_ids

        # Populate rows
        for line in lines:
            if statement_type == 'customer':
                invoice_date = line.invoice_date
                due_date = line.invoice_date_due
                reference = line.name
                debit = line.amount_total if line.move_type == 'out_invoice' else 0.0
                credit = line.amount_total if line.move_type == 'out_refund' else 0.0
                balance = line.amount_residual
            else:
                invoice_date = line.move_id.invoice_date
                due_date = line.move_id.invoice_date_due
                reference = line.reference
                debit = line.debit
                credit = line.credit
                balance = line.balance

            sheet.write(row, 0, invoice_date, date_format)
            sheet.write(row, 1, reference)
            sheet.write(row, 2, due_date, date_format)
            sheet.write(row, 3, debit, currency_format)
            sheet.write(row, 4, credit, currency_format)
            sheet.write(row, 5, balance, currency_format)
            row += 1

        workbook.close()
        output.seek(0)
        xls_data = output.read()
        attachment = self.env['ir.attachment'].create({
            'name': f'{self.name}_{statement_type}_statement.xlsx',
            'type': 'binary',
            'datas': base64.b64encode(xls_data),
            'res_model': 'res.partner',
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }

    def do_print_cust_due_state(self):
        return self.env.ref('of_account_statement.action_report_customer_overdue_report').sudo().report_action(self.id)

    def do_print_cust_state(self):
        return self.env.ref('of_account_statement.action_report_customer_statement_report').sudo().report_action(self.id)



    def do_print_cust_state_excel(self):
        return self._generate_excel_report('customer')

    def do_print_supp_state_excel(self):
        return self._generate_excel_report('supplier')

    def do_print_supp_state(self):
        """Print Supplier Statement PDF using the QWeb report"""
        self.ensure_one()
        return self.env.ref('of_account_statement.action_report_supplier_statement_report').sudo().report_action(
            self.id)


    def do_print_supp_due_state(self):
        return self.env.ref('of_account_statement.action_report_supplier_overdue_report').sudo().report_action(self.id)


    def action_cust_due_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id =self.env.ref('of_account_statement.mail_template_cust_overdue').id
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'res.partner',
            'default_res_id' : self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode' : 'comment',
            'force_email' : True
        }

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }



# # -*- coding: utf-8 -*-
# from datetime import datetime
# from odoo import api, fields, models, _
# from odoo.exceptions import ValidationError, UserError
# import xlsxwriter
# import io
# import base64
#
#
#
# class SupplierStatement(models.Model):
#     _name = 'supplier.statement'
#     _description = 'Supplier Statement'
#
#     partner_id = fields.Many2one('res.partner', string="Supplier", required=True, ondelete="cascade")
#     move_id = fields.Many2one('account.move')
#     move_line_id = fields.Many2one('account.move.line')
#     bill_date = fields.Date(string="Bill Date")
#     month = fields.Char(string="Month")
#     reference = fields.Char(string="Reference")
#     bill_reference = fields.Char(string="Bill Reference",related="move_id.ref")
#     company = fields.Many2one(string="Company",related="move_id.company_id")
#     due_date = fields.Date(string="Due Date",related="move_id.invoice_date_due")
#     debit = fields.Float(string="Debit", )
#     credit = fields.Float(string="Credit")
#     balance = fields.Float(string="Balance")
#     status = fields.Selection(related="move_id.state")
#
#
# class AccountInvoice(models.Model):
#     _inherit = "account.move"
#     _description = "Account Move Paid Amounts"
#
#     paid_amount = fields.Monetary(string='Paid Amount', compute='_compute_paid_amount', store=True, help="Paid Amount.")
#     month = fields.Char(string="Month", compute='_compute_month', store=True)
#
    # @property
    # def return_due_days(self):
    #     return (datetime.now().date()-self.invoice_date).days
#
#     @api.onchange('invoice_date')
#     @api.depends('invoice_date')
#     def _compute_month(self):
#         for rec in self:
#             if rec.invoice_date:
#                 rec.month = rec.invoice_date.strftime("%B")
#
#     @api.depends('amount_residual')
#     def _compute_paid_amount(self):
#         for inv in self:
#             inv.paid_amount = 0.0
#             if inv.state != 'draft':
#                 inv.paid_amount = inv.amount_total - inv.amount_residual
#
#
# class Partner(models.Model):
#     _inherit = "res.partner"
#
#     supplier_statement_ids = fields.One2many('supplier.statement', 'partner_id', string="Supplier Statements",compute="_compute_supp_statement")
#     customer_statement_ids = fields.One2many('supplier.statement', 'partner_id', string="Supplier Statements",compute="_compute_cust_statement")
#
#     def do_print_cust_state_excel(self):
#         """Generate Excel report and download it"""
#         output = io.BytesIO()
#         workbook = xlsxwriter.Workbook(output)
#         sheet = workbook.add_worksheet('Customer Statement')
#
#         # Formatting
#         bold = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
#         date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
#         currency_format = workbook.add_format({'num_format': '#,##0.00'})
#
#         # Title and customer info
#         sheet.merge_range('A1:I1', 'Customer Statement', bold)
#         sheet.write('A2', 'Print Date:', bold)
#         sheet.write('B2', fields.Datetime.now().strftime('%Y-%m-%d %H:%M'))
#         sheet.write('A3', 'Customer Name:', bold)
#         sheet.write('B3', self.name)
#         sheet.write('A4', 'Customer Ref:', bold)
#         sheet.write('B4', self.ref or '')
#
#         # VAT and Project Filters
#         row = 5
#
#         if self.cust_from_date and self.cust_to_date:
#             sheet.write(row, 0, 'Date From:', bold)
#             sheet.write(row, 1, self.cust_from_date,date_format)
#             sheet.write(row + 1, 0, 'Date To:', bold)
#             sheet.write(row + 1, 1, self.cust_to_date,date_format)
#             row += 2
#
#         # Table headers
#         headers = [
#             'Invoice Date', 'Reference', 'Due Date', 'Debit', 'Credit', 'Balance'
#         ]
#
#         for col, header in enumerate(headers):
#             sheet.write(row, col, header, bold)
#
#         row += 1
#
#         # Totals
#         sum_amount = sum_paid = sum_due = 0
#
#         # Customer statement lines
#         for line in self.customer_statement_ids:
#             sheet.write(row, 0, line.move_id.invoice_date, date_format)
#             sheet.write(row, 1, line.reference)
#             sheet.write(row, 2, line.move_id.invoice_date_due, date_format)
#             sheet.write(row, 3, line.debit, currency_format)
#             sheet.write(row, 4, line.credit, currency_format)
#             sheet.write(row, 5, line.balance, currency_format)
#
#             row += 1
#
#         # Close workbook
#         workbook.close()
#
#         # Save Excel to binary field
#         output.seek(0)
#         xls_data = output.read()
#         output.close()
#
#         # Create an attachment
#         attachment = self.env['ir.attachment'].create({
#             'name': f'{self.name}_statement.xlsx',
#             'type': 'binary',
#             'datas': base64.b64encode(xls_data),
#             'res_model': 'res.partner',
#             'res_id': self.id
#         })
#
#         return {
#             'type': 'ir.actions.act_url',
#             'url': f'/web/content/{attachment.id}?download=true',
#             'target': 'new',
#         }
#
#     def do_print_supp_state_excel(self):
#         """Generate Excel report and download it"""
#         output = io.BytesIO()
#         workbook = xlsxwriter.Workbook(output)
#         sheet = workbook.add_worksheet('Customer Statement')
#
#         # Formatting
#         bold = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'border': 1})
#         date_format = workbook.add_format({'num_format': 'yyyy-mm-dd'})
#         currency_format = workbook.add_format({'num_format': '#,##0.00'})
#
#         # Title and customer info
#         sheet.merge_range('A1:I1', 'Supplier Statement', bold)
#         sheet.write('A2', 'Print Date:', bold)
#         sheet.write('B2', fields.Datetime.now().strftime('%Y-%m-%d %H:%M'))
#         sheet.write('A3', 'Customer Name:', bold)
#         sheet.write('B3', self.name)
#         sheet.write('A4', 'Customer Ref:', bold)
#         sheet.write('B4', self.ref or '')
#
#         # VAT and Project Filters
#         row = 5
#
#         if self.supp_from_date and self.supp_to_date:
#             sheet.write(row, 0, 'Date From:', bold)
#             sheet.write(row, 1, self.supp_from_date,date_format)
#             sheet.write(row + 1, 0, 'Date To:', bold)
#             sheet.write(row + 1, 1, self.supp_to_date,date_format)
#             row += 2
#
#         # Table headers
#         headers = [
#             'Invoice Date', 'Reference', 'Due Date', 'Debit', 'Credit', 'Balance'
#         ]
#
#         for col, header in enumerate(headers):
#             sheet.write(row, col, header, bold)
#
#         row += 1
#
#         # Totals
#         sum_amount = sum_paid = sum_due = 0
#
#         # Supplier statement lines
#         for line in self.supplier_statement_ids:
#             sheet.write(row, 0, line.move_id.invoice_date, date_format)
#             sheet.write(row, 1, line.reference)
#             sheet.write(row, 2, line.move_id.invoice_date_due, date_format)
#             sheet.write(row, 3, line.debit, currency_format)
#             sheet.write(row, 4, line.credit, currency_format)
#             sheet.write(row, 5, line.balance, currency_format)
#
#             row += 1
#
#         # Close workbook
#         workbook.close()
#
#         # Save Excel to binary field
#         output.seek(0)
#         xls_data = output.read()
#         output.close()
#
#         # Create an attachment
#         attachment = self.env['ir.attachment'].create({
#             'name': f'{self.name}_statement.xlsx',
#             'type': 'binary',
#             'datas': base64.b64encode(xls_data),
#             'res_model': 'res.partner',
#             'res_id': self.id
#         })
#
#         return {
#             'type': 'ir.actions.act_url',
#             'url': f'/web/content/{attachment.id}?download=true',
#             'target': 'new',
#         }
#
#
#     def get_filtered_line_supp_acc_stat_line_ids(self):
#         return self.supp_acc_stat_line_ids.filtered(lambda x: x.paid_amount <= 0)
#
#     def get_filtered_paid_lines(self):
#         return self.supp_acc_stat_line_ids.filtered(lambda x: x.paid_amount > 0)
#
#     def _compute_supp_statement(self):
#         CustomerStatement = self.env['supplier.statement']
#
#         for rec in self:
#             # Create partner ledger to retrieve move lines
#             partner_ledger = self.env['ins.partner.ledger'].create({
#                 'date_from': rec.supp_from_date,
#                 'date_to': rec.supp_to_date,
#                 'partner_ids': [(6, 0, rec.ids)]
#             })
#
#             result = partner_ledger.build_detailed_move_lines(partner=rec.id)
#
#             if isinstance(result, tuple) and len(result) == 3:
#                 _, _, move_lines = result
#
#                 # Clear existing statements
#                 rec.supplier_statement_ids.unlink()
#
#                 # Create customer statement records from move_lines
#                 statements = []
#                 for line in move_lines:
#                     statement_vals = {
#                         'partner_id': rec.id,
#                         'bill_date': line.get('ldate'),
#                         'month': line.get('ldate').strftime('%B') if line.get('ldate') else False,
#                         'move_id': line.get('move_id'),
#                         'move_line_id': line.get('lid'),
#                         'debit': line.get('debit', 0.0),
#                         'credit': line.get('credit', 0.0),
#                         'balance': line.get('balance', 0.0),
#                         'reference': line.get('move_name', ''),
#                     }
#                     statement = CustomerStatement.create(statement_vals)
#                     statements.append(statement.id)
#
#                 # Assign the newly created records
#                 rec.supplier_statement_ids = [(6, 0, statements)]
#             else:
#                 rec.supplier_statement_ids = False  # Reset if no valid data
#
#
#
#     def _compute_cust_statement(self):
#         CustomerStatement = self.env['supplier.statement']
#
#         for rec in self:
#             # Create partner ledger to retrieve move lines
#             partner_ledger = self.env['ins.partner.ledger'].create({
#                 'date_from': rec.cust_from_date,
#                 'date_to': rec.cust_to_date,
#                 'partner_ids': [(6, 0, rec.ids)]
#             })
#
#             result = partner_ledger.build_detailed_move_lines(partner=rec.id)
#
#             if isinstance(result, tuple) and len(result) == 3:
#                 _, _, move_lines = result
#
#                 # Clear existing statements
#                 rec.customer_statement_ids.unlink()
#
#                 # Create customer statement records from move_lines
#                 statements = []
#                 for line in move_lines:
#                     statement_vals = {
#                         'partner_id': rec.id,
#                         'bill_date': line.get('ldate'),
#                         'month': line.get('ldate').strftime('%B') if line.get('ldate') else False,
#                         'move_id': line.get('move_id'),
#                         'move_line_id': line.get('lid'),
#                         'debit': line.get('debit', 0.0),
#                         'credit': line.get('credit', 0.0),
#                         'balance': line.get('balance', 0.0),
#                         'reference': line.get('move_name', ''),
#                     }
#                     statement = CustomerStatement.create(statement_vals)
#                     statements.append(statement.id)
#
#                 # Assign the newly created records
#                 rec.customer_statement_ids = [(6, 0, statements)]
#             else:
#                 rec.customer_statement_ids = False  # Reset if no valid data
#
#
#     @api.depends('cust_acc_stat_line_ids','cust_acc_stat_line_ids.invoice_date_due','cust_acc_stat_line_ids.amount_residual')
#     def _get_cust_amounts_and_date(self):
#         company = self.env.user.company_id
#         current_date = fields.Date.today()
#         for partner in self:
#             due_date = False
#             amount_due = amount_overdue = 0.0
#             for aml in partner.cust_acc_stat_line_ids:
#                 due_date = aml.invoice_date_due
#                 if (aml.company_id == company):
#                     if not due_date:
#                         due_date = aml.date or aml.invoice_date
#                     amount_due += aml.amount_residual
#                     if (due_date <= current_date):
#                         amount_overdue += aml.amount_residual
#             partner.cust_overall_balance_due = amount_due
#             partner.cust_total_overdue_amount = amount_overdue
#
#     @api.depends('supp_acc_stat_line_ids','supp_acc_stat_line_ids.invoice_date_due','supp_acc_stat_line_ids.amount_residual')
#     def _get_supp_amounts_and_date(self):
#         company = self.env.user.company_id
#         current_date = fields.Date.today()
#         for partner in self:
#             due_date = False
#             amount_due = amount_overdue = 0.0
#             for aml in partner.supp_acc_stat_line_ids:
#                 due_date = aml.invoice_date_due
#                 if (aml.company_id == company):
#                     amount_due += aml.amount_residual
#                     if not due_date:
#                         due_date = aml.date or aml.invoice_date
#                     if (due_date <= current_date):
#                         amount_overdue += aml.amount_residual
#             partner.supp_overall_balance_due = amount_due
#             partner.supp_total_overdue_amount = amount_overdue
#
# #    cust_acc_stat_line_ids = fields.One2many("account.move", "partner_id", string="Customer Account Statement", auto_join=True, domain=[('state','=','posted'),('move_type', 'in', ['out_invoice', 'out_refund', 'out_receipt'])])
#     cust_acc_stat_line_ids = fields.Many2many("account.move", string="Customer Account Statement", compute="compute_cust_statement_lines")
#     supp_acc_stat_line_ids = fields.Many2many("account.move", string="Supplier Account Statement", compute="compute_supplier_statement_lines")
# #    supp_acc_stat_line_ids = fields.One2many("account.move", "partner_id", string="Supplier Account Statement", auto_join=True, domain=[('state','=','posted'),('move_type','in',['in_invoice', 'in_refund','in_receipt'])])
#
#     cust_overall_balance_due = fields.Float(compute='_get_cust_amounts_and_date')
#     cust_total_overdue_amount = fields.Float(compute='_get_cust_amounts_and_date')
#
#     supp_overall_balance_due = fields.Float(compute='_get_supp_amounts_and_date')
#     supp_total_overdue_amount = fields.Float(compute='_get_supp_amounts_and_date')
#     monthly_search = fields.Selection([('January', 'January'), ('February', 'February'),
#                                        ('March', 'March'), ('April', 'April'), ('May', 'May'),
#                                        ('June', 'June'), ('July', 'July'), ('August', 'August'),
#                                        ('September', 'September'), ('October', 'October'),
#                                        ('November', 'November'), ('December', 'December')], 'Search Filter')
#     supplier_monthly_search = fields.Selection([('January', 'January'), ('February', 'February'),
#                                        ('March', 'March'), ('April', 'April'), ('May', 'May'),
#                                        ('June', 'June'), ('July', 'July'), ('August', 'August'),
#                                        ('September', 'September'), ('October', 'October'),
#                                        ('November', 'November'), ('December', 'December')], 'Search Filter')
#     cust_from_date = fields.Date(string="From Date")
#     cust_to_date = fields.Date(string="To Date")
#     supp_from_date = fields.Date(string="From Date")
#     supp_to_date = fields.Date(string="To Date")
#
#     @api.onchange('cust_from_date', 'cust_to_date')
#     @api.depends('cust_from_date', 'cust_to_date')
#     def compute_cust_statement_lines(self):
#         """
#         This method updates the domain for the cust_acc_stat_line_ids based on the search.
#         """
#         for rec in self:
#             if rec.cust_from_date and rec.cust_to_date:
#                 rec.cust_acc_stat_line_ids = [(5, 0, 0)]
#                 new_invoices = self.env['account.move'].search(
#                     [('state', '=', 'posted'), ('move_type', 'in', ['out_invoice', 'out_refund', 'out_receipt']),
#                      ('invoice_date', '>=', rec.cust_from_date), ('invoice_date', '<=', rec.cust_to_date), ('partner_id', '=', rec.id)], order="invoice_date")
#                 rec.cust_acc_stat_line_ids = [(4, invoice.id) for invoice in new_invoices]
#             else:
#                 new_invoices = self.env['account.move'].search(
#                     [('state', '=', 'posted'), ('move_type', 'in', ['out_invoice', 'out_refund', 'out_receipt']),
#                      ('partner_id', '=', self.id)], order="invoice_date")
#                 rec.cust_acc_stat_line_ids = [(4, invoice.id) for invoice in new_invoices]
#
#
#     @api.onchange('supp_from_date', 'supp_to_date')
#     @api.depends('supp_from_date', 'supp_to_date')
#     def compute_supplier_statement_lines(self):
#         """
#         This method updates the domain for the cust_acc_stat_line_ids based on the search.
#         """
#         for rec in self:
#             if rec.supp_from_date and rec.supp_to_date:
#                 rec.supp_acc_stat_line_ids = [(5, 0, 0)]
#                 new_invoices = self.env['account.move'].search(
#                     [('state', '=', 'posted'), ('move_type', 'in', ['in_invoice', 'in_refund', 'in_receipt']),
#                      ('invoice_date', '>=', rec.supp_from_date), ('invoice_date', '<=', rec.supp_to_date), ('partner_id', '=', rec.id)], order="invoice_date")
#                 rec.supp_acc_stat_line_ids = [(4, invoice.id) for invoice in new_invoices]
#             else:
#                 new_invoices = self.env['account.move'].search(
#                     [('state', '=', 'posted'), ('move_type', 'in', ['in_invoice', 'in_refund', 'in_receipt']),
#                      ('partner_id', '=', self.id)], order="invoice_date")
#                 rec.supp_acc_stat_line_ids = [(4, invoice.id) for invoice in new_invoices]
#
#     # @api.onchange('monthly_search')
#     # @api.depends('monthly_search')
#     # def compute_cust_statement_lines(self):
#     #     """
#     #     This method updates the domain for the cust_acc_stat_line_ids based on the search.
#     #     """
#     #     for rec in self:
#     #         if rec.monthly_search:
#     #             rec.cust_acc_stat_line_ids = [(5, 0, 0)]  # Clear existing lines
#     #             new_invoices = self.env['account.move'].search(
#     #                 [('state', '=', 'posted'), ('move_type', 'in', ['out_invoice', 'out_refund', 'out_receipt']),
#     #                  ('month', 'ilike', self.monthly_search), ('partner_id', '=', self.id)])
#     #             if new_invoices:
#     #                 rec.cust_acc_stat_line_ids = [(4, invoice.id) for invoice in new_invoices]
#     #         else:
#     #             rec.cust_acc_stat_line_ids = [(5, 0, 0)]
#     #             new_invoices = self.env['account.move'].search(
#     #                 [('state', '=', 'posted'), ('move_type', 'in', ['out_invoice', 'out_refund', 'out_receipt']),
#     #                  ('partner_id', '=', self.id)])
#     #             if new_invoices:
#     #                 rec.cust_acc_stat_line_ids = [(4, invoice.id) for invoice in new_invoices]
#
#
#     # @api.onchange('supplier_monthly_search')
#     # @api.depends('supplier_monthly_search')
#     # def compute_supplier_statement_lines(self):
#     #     """
#     #     This method updates the domain for the cust_acc_stat_line_ids based on the search.
#     #     """
#     #     for rec in self:
#     #         if rec.supplier_monthly_search:
#     #             rec.supp_acc_stat_line_ids = [(5, 0, 0)]  # Clear existing lines
#     #             new_bills = self.env['account.move'].search(
#     #                 [('state', '=', 'posted'), ('move_type', 'in', ['in_invoice', 'in_refund', 'in_receipt']),
#     #                  ('month', 'ilike', self.supplier_monthly_search), ('partner_id', '=', self.id)])
#     #             if new_bills:
#     #                 rec.supp_acc_stat_line_ids = [(4, bill.id) for bill in new_bills]
#     #         else:
#     #             rec.supp_acc_stat_line_ids = [(5, 0, 0)]
#     #             new_bills = self.env['account.move'].search(
#     #                 [('state', '=', 'posted'), ('move_type', 'in', ['in_invoice', 'in_refund', 'in_receipt']),
#     #                  ('partner_id', '=', self.id)])
#     #             if new_bills:
#     #                 rec.supp_acc_stat_line_ids = [(4, bill.id) for bill in new_bills]
#
#
#     def do_print_cust_due_state(self):
#         return self.env.ref('of_account_statement.action_report_customer_overdue_report').sudo().report_action(self.id)
#     def do_print_cust_state(self):
#         return self.env.ref('of_account_statement.action_report_customer_statement_report').sudo().report_action(self.id)
#
#     def do_print_supp_due_state(self):
#         return self.env.ref('of_account_statement.action_report_supplier_overdue_report').sudo().report_action(self.id)
#     def do_print_supp_state(self):
#         return self.env.ref('of_account_statement.action_report_supplier_statement_report').sudo().report_action(self.id)
#
    # def action_cust_due_send(self):
    #     ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
    #     self.ensure_one()
    #     template_id =self.env.ref('of_account_statement.mail_template_cust_overdue').id
    #     lang = self.env.context.get('lang')
    #     template = self.env['mail.template'].browse(template_id)
    #     if template.lang:
    #         lang = template._render_lang(self.ids)[self.id]
    #     ctx = {
    #         'default_model': 'res.partner',
    #         'default_res_id' : self.id,
    #         'default_use_template': bool(template_id),
    #         'default_template_id': template_id,
    #         'default_composition_mode' : 'comment',
    #         'force_email' : True
    #     }
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(False, 'form')],
    #         'view_id': False,
    #         'target': 'new',
    #         'context': ctx,
    #     }

#
    # def action_cust_state_send(self):
    #     ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
    #     self.ensure_one()
    #     template_id =self.env.ref('of_account_statement.mail_template_cust_statement').id
    #     lang = self.env.context.get('lang')
    #     template = self.env['mail.template'].browse(template_id)
    #     if template.lang:
    #         lang = template._render_lang(self.ids)[self.id]
    #     ctx = {
    #         'default_model': 'res.partner',
    #         'default_res_id' : self.id,
    #         'default_use_template': bool(template_id),
    #         'default_template_id': template_id,
    #         'default_composition_mode' : 'comment',
    #         'force_email' : True
    #     }
    #
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'view_mode': 'form',
    #         'res_model': 'mail.compose.message',
    #         'views': [(False, 'form')],
    #         'view_id': False,
    #         'target': 'new',
    #         'context': ctx,
    #     }
#
#
#     def action_supp_state_send(self):
#         ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
#         self.ensure_one()
#         template_id =self.env.ref('of_account_statement.mail_template_supp_statement').id
#         lang = self.env.context.get('lang')
#         template = self.env['mail.template'].browse(template_id)
#         if template.lang:
#             lang = template._render_lang(self.ids)[self.id]
#         ctx = {
#             'default_model': 'res.partner',
#             'default_res_id' : self.id,
#             'default_use_template': bool(template_id),
#             'default_template_id': template_id,
#             'default_composition_mode' : 'comment',
#             'force_email' : True
#         }
#
#         return {
#             'type': 'ir.actions.act_window',
#             'view_mode': 'form',
#             'res_model': 'mail.compose.message',
#             'views': [(False, 'form')],
#             'view_id': False,
#             'target': 'new',
#             'context': ctx,
#         }
