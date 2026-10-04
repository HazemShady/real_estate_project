# -*- coding: utf-8 -*-
import io
import base64
import xlsxwriter

from odoo import models, fields
from odoo.exceptions import UserError


class MaintenanceReportWizard(models.TransientModel):
    _name = 'maintenance.report.wizard'
    _description = 'Maintenance Report Wizard'

    # Optional filters applied to maintenance requests.
    property_id = fields.Many2one('real_estate.property', string='Property')
    issue_type = fields.Selection([
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('air_condition', 'Air Condition'),
        ('appliance', 'Appliance'),
        ('other', 'Other'),
    ], string='Issue Type')
    urgency = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    ], string='Urgency')
    tenant_id = fields.Many2one('real_estate.tenant', string='Tenant')
    filter_actual_cost = fields.Boolean(string='Filter by Actual Cost')
    actual_cost_from = fields.Float(string='Actual Cost From')
    actual_cost_to = fields.Float(string='Actual Cost To')
    excel_file = fields.Binary(string='Excel File', readonly=True)
    excel_filename = fields.Char(string='File Name', readonly=True)

    # Generate a workbook from the selected requests.
    def action_generate_report(self):
        self.ensure_one()
        if self.filter_actual_cost and self.actual_cost_from > self.actual_cost_to:
            raise UserError('Actual Cost From must be less than or equal to Actual Cost To.')

        domain = []
        if self.property_id:
            domain.append(('property_id', '=', self.property_id.id))
        if self.issue_type:
            domain.append(('issue_type', '=', self.issue_type))
        if self.urgency:
            domain.append(('urgency', '=', self.urgency))
        if self.tenant_id:
            domain.append(('lease_id.tenant_id', '=', self.tenant_id.id))
        if self.filter_actual_cost:
            domain.extend([
                ('actual_cost', '>=', self.actual_cost_from),
                ('actual_cost', '<=', self.actual_cost_to),
            ])

        requests = self.env['maintenance.request'].search(domain, order='property_id, id')
        request_model = self.env['maintenance.request']
        issue_labels = dict(request_model._fields['issue_type'].selection)
        urgency_labels = dict(request_model._fields['urgency'].selection)
        state_labels = dict(request_model._fields['state'].selection)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Maintenance Report')

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
        })
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9E1F2',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })
        category_format = workbook.add_format({
            'bold': True,
            'bg_color': '#D9EAD3',
            'border': 1,
            'font_size': 11,
            'valign': 'vcenter',
        })
        data_format = workbook.add_format({'border': 1, 'valign': 'top'})
        description_format = workbook.add_format({
            'border': 1,
            'valign': 'top',
            'text_wrap': True,
        })
        date_format = workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'border': 1,
            'align': 'center',
            'valign': 'top',
        })
        currency_format = workbook.add_format({
            'num_format': '#,##0.00',
            'border': 1,
            'align': 'right',
            'valign': 'top',
        })
        total_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E2EFDA',
            'border': 1,
            'valign': 'vcenter',
        })
        total_currency_format = workbook.add_format({
            'bold': True,
            'bg_color': '#E2EFDA',
            'num_format': '#,##0.00',
            'border': 1,
            'align': 'right',
        })
        grand_total_format = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': '#70AD47',
            'font_color': 'white',
            'border': 2,
            'valign': 'vcenter',
        })
        grand_total_currency_format = workbook.add_format({
            'bold': True,
            'bg_color': '#70AD47',
            'font_color': 'white',
            'num_format': '#,##0.00',
            'border': 2,
            'align': 'right',
        })
        label_format = workbook.add_format({'bold': True, 'border': 1})

        headers = [
            'Request', 'Property', 'Tenant', 'Issue Type', 'Urgency', 'Status',
            'Description', 'Scheduled Date', 'Completion Date', 'Assigned To',
            'Actual Cost', 'Currency',
        ]
        worksheet.set_column('A:A', 18)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 22)
        worksheet.set_column('D:F', 17)
        worksheet.set_column('G:G', 42)
        worksheet.set_column('H:I', 15)
        worksheet.set_column('J:J', 23)
        worksheet.set_column('K:K', 18)
        worksheet.set_column('L:L', 12)

        row = 0
        worksheet.merge_range(row, 0, row, 11, 'MAINTENANCE REPORT', title_format)
        worksheet.set_row(row, 25)
        row += 2

        for col, header in enumerate(headers):
            worksheet.write(row, col, header, header_format)
        worksheet.set_row(row, 30)
        header_row = row
        row += 1

        # actual_cost has no currency field; use the property's currency and
        # keep amounts with different currencies in separate totals.
        grand_totals = {}
        issue_groups = {}
        for request in requests:
            issue_groups.setdefault(request.issue_type, []).append(request)

        issue_order = {value: index for index, (value, _) in enumerate(issue_labels.items())}
        for issue_value, issue_requests in sorted(
            issue_groups.items(), key=lambda group: issue_order.get(group[0], len(issue_order))
        ):
            issue_label = issue_labels.get(issue_value, issue_value or 'Other')
            worksheet.write(row, 0, issue_label.upper(), category_format)
            worksheet.merge_range(row, 1, row, 11, '', category_format)
            worksheet.set_row(row, 21)
            row += 1

            subtotals = {}
            for request in issue_requests:
                property_record = request.property_id
                tenant = request.lease_id.tenant_id if request.lease_id else False
                currency = property_record.currency_id if property_record else False
                currency_key = currency.id if currency else False
                cost = request.actual_cost or 0.0
                subtotal = subtotals.setdefault(currency_key, {'currency': currency, 'amount': 0.0})
                subtotal['amount'] += cost
                grand_total = grand_totals.setdefault(
                    currency_key, {'currency': currency, 'amount': 0.0}
                )
                grand_total['amount'] += cost

                worksheet.write(row, 0, request.name or '', data_format)
                worksheet.write(row, 1, property_record.name if property_record else '', data_format)
                worksheet.write(row, 2, tenant.name if tenant else '', data_format)
                worksheet.write(row, 3, issue_label, data_format)
                worksheet.write(row, 4, urgency_labels.get(request.urgency, ''), data_format)
                worksheet.write(row, 5, state_labels.get(request.state, ''), data_format)
                description = request.description or ''
                worksheet.write(row, 6, description, description_format)
                worksheet.write(row, 7, request.scheduled_date or '', date_format)
                worksheet.write(row, 8, request.completion_date or '', date_format)
                worksheet.write(row, 9, request.assigned_to.name if request.assigned_to else '', data_format)
                worksheet.write_number(row, 10, cost, currency_format)
                worksheet.write(row, 11, currency.name if currency else 'Unspecified', data_format)
                description_lines = sum(
                    max(1, (len(line) + 41) // 42) for line in description.splitlines()
                ) or 1
                worksheet.set_row(row, max(30, description_lines * 15))
                row += 1

            for subtotal in sorted(
                subtotals.values(), key=lambda item: item['currency'].name if item['currency'] else ''
            ):
                currency_name = subtotal['currency'].name if subtotal['currency'] else 'Unspecified'
                worksheet.merge_range(row, 0, row, 9, f'{issue_label} Subtotal', total_format)
                worksheet.write_number(row, 10, subtotal['amount'], total_currency_format)
                worksheet.write(row, 11, currency_name, total_format)
                worksheet.set_row(row, 21)
                row += 1

        if not requests:
            worksheet.merge_range(row, 0, row, 11, 'No maintenance requests matched the selected filters.', data_format)
            row += 1

        row += 1
        if grand_totals:
            for total in sorted(
                grand_totals.values(), key=lambda item: item['currency'].name if item['currency'] else ''
            ):
                currency_name = total['currency'].name if total['currency'] else 'Unspecified'
                worksheet.merge_range(row, 0, row, 9, f'GRAND TOTAL ({currency_name})', grand_total_format)
                worksheet.write_number(row, 10, total['amount'], grand_total_currency_format)
                worksheet.write(row, 11, currency_name, grand_total_format)
                worksheet.set_row(row, 23)
                row += 1

        row += 2
        stats_header = workbook.add_format({
            'bold': True,
            'font_size': 11,
            'bg_color': '#D9E1F2',
        })
        worksheet.write(row, 0, 'SUMMARY STATISTICS', stats_header)
        row += 1

        worksheet.write(row, 0, 'Total Requests:', label_format)
        worksheet.write(row, 1, len(requests), data_format)
        row += 1
        for state, label in request_model._fields['state'].selection:
            count = len(requests.filtered(lambda request: request.state == state))
            worksheet.write(row, 0, f'{label}:', label_format)
            worksheet.write(row, 1, count, data_format)
            row += 1

        worksheet.freeze_panes(header_row + 1, 0)
        worksheet.set_landscape()
        worksheet.fit_to_pages(1, 0)
        worksheet.set_margins(0.25, 0.25, 0.5, 0.5)
        workbook.close()

        output.seek(0)
        self.excel_file = base64.b64encode(output.read())
        self.excel_filename = f'Maintenance_Report_{fields.Date.today()}.xlsx'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.report.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
