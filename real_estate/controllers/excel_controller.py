import io
from datetime import datetime

from odoo import http
from odoo.http import request, content_disposition
from odoo.tools.misc import xlsxwriter

class RealEstateController(http.Controller):

    # Property workbook export.
    @http.route('/real_estate/property/excel_export/<int:property_id>', type='http', auth='user')
    def property_excel_export(self, property_id, **kwargs):
        """Export a polished property report to Excel."""
        property_obj = request.env['real_estate.property'].browse(property_id)

        if not property_obj.exists():
            return request.not_found()

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Property Report')

        def safe_value(value):
            if value is None:
                return ''
            if isinstance(value, bool):
                return 'Yes' if value else 'No'
            return value

        header_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
            'bg_color': '#1F4E78',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 20,
            'bg_color': '#D9EAF7',
            'font_color': '#1F1F1F',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
        })

        section_format = workbook.add_format({
            'bold': True,
            'font_size': 12,
            'bg_color': '#E2EFD9',
            'font_color': '#1F1F1F',
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
        })

        label_format = workbook.add_format({
            'bold': True,
            'bg_color': '#F2F2F2',
            'border': 1,
            'align': 'left',
        })

        data_format = workbook.add_format({
            'border': 1,
            'align': 'left',
        })

        value_format = workbook.add_format({
            'border': 1,
            'align': 'center',
        })

        currency = property_obj.currency_id
        currency_symbol = (currency.symbol or currency.name or '').replace('"', '""')
        currency_number_format = (
            f'#,##0.00 "{currency_symbol}"'
            if currency.position == 'after'
            else f'"{currency_symbol}"#,##0.00'
        )
        currency_format = workbook.add_format({
            'num_format': currency_number_format,
            'border': 1,
            'align': 'center',
        })

        date_format = workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'border': 1,
            'align': 'center',
        })

        note_format = workbook.add_format({
            'text_wrap': True,
            'valign': 'top',
            'border': 1,
            'align': 'left',
        })

        table_header_format = workbook.add_format({
            'bold': True,
            'font_color': 'white',
            'bg_color': '#4472C4',
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'text_wrap': True,
        })

        alternate_format = workbook.add_format({
            'bg_color': '#F5F8FC',
            'border': 1,
            'valign': 'vcenter',
        })

        alternate_currency_format = workbook.add_format({
            'num_format': currency_number_format,
            'bg_color': '#F5F8FC',
            'border': 1,
            'align': 'center',
        })

        alternate_date_format = workbook.add_format({
            'num_format': 'yyyy-mm-dd',
            'bg_color': '#F5F8FC',
            'border': 1,
            'align': 'center',
        })

        worksheet.set_column('A:A', 25)
        worksheet.set_column('B:B', 22)
        worksheet.set_column('C:C', 18)
        worksheet.set_column('D:D', 18)
        worksheet.set_column('E:E', 18)
        worksheet.set_column('F:F', 20)
        worksheet.set_column('G:G', 16)
        worksheet.set_column('H:H', 18)
        worksheet.set_column('I:I', 16)
        worksheet.set_default_row(21)
        worksheet.set_landscape()
        worksheet.fit_to_pages(1, 0)
        worksheet.set_margins(0.3, 0.3, 0.5, 0.5)

        worksheet.freeze_panes(5, 0)

        report_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        active_leases = property_obj.lease_ids.filtered(lambda lease: lease.state == 'active')
        total_rent = sum(lease.monthly_rent for lease in property_obj.lease_ids)
        annual_estimate = (property_obj.price or 0) * 12

        worksheet.merge_range('A1:I1', 'PROPERTY REPORT', title_format)
        worksheet.merge_range('A2:I2', safe_value(property_obj.name), header_format)
        worksheet.write('A3', 'Report Date', label_format)
        worksheet.write('B3', report_date, data_format)
        worksheet.write('D3', 'Status', label_format)
        worksheet.write('E3', 'Available' if property_obj.available else 'Occupied', value_format)
        worksheet.write('A4', 'Agent', label_format)
        worksheet.write('B4', safe_value(property_obj.agent_id.name or 'Not assigned'), data_format)
        worksheet.write('D4', 'Property Type', label_format)
        worksheet.write('E4', dict(property_obj._fields['property_type'].selection).get(property_obj.property_type, ''), value_format)

        row = 6
        worksheet.merge_range(row, 0, row, 1, 'PROPERTY INFORMATION', section_format)
        row += 1

        property_data = [
            ('Property Name', property_obj.name),
            ('Address / Location', safe_value(getattr(property_obj, 'location', '') or 'Not specified')),
            ('Bedrooms', property_obj.bedrooms),
            ('Bathrooms', property_obj.bathrooms),
            ('Square Feet', property_obj.square_feet),
            ('Availability', 'Available' if property_obj.available else 'Occupied'),
            ('Created On', property_obj.create_date),
            ('Last Updated', property_obj.write_date),
        ]

        for idx, (label, value) in enumerate(property_data):
            if idx % 2 == 0:
                worksheet.write(row, 0, label, label_format)
                worksheet.write(row, 1, safe_value(value), data_format)
            else:
                worksheet.write(row, 2, label, label_format)
                worksheet.write(row, 3, safe_value(value), data_format)
                row += 1

        if len(property_data) % 2 != 0:
            row += 1

        if property_obj.description:
            worksheet.merge_range(row, 0, row, 3, 'DESCRIPTION', section_format)
            row += 1
            worksheet.merge_range(row, 0, row, 3, property_obj.description or 'No description provided.', note_format)
            row += 2
        else:
            row += 1

        worksheet.merge_range(row, 0, row, 1, 'FINANCIAL SUMMARY', section_format)
        row += 1

        finance_data = [
            ('Monthly Rent', property_obj.price or 0),
            ('Deposit Amount', property_obj.deposit or 0),
            ('Required Deposit', property_obj.deposit_required or 0),
            ('Annual Rent Estimate', annual_estimate),
            ('Active Leases', len(active_leases)),
            ('Total Lease Rent', total_rent),
        ]

        for idx, (label, value) in enumerate(finance_data):
            if idx % 2 == 0:
                worksheet.write(row, 0, label, label_format)
                worksheet.write(row, 1, value, currency_format if isinstance(value, (int, float)) and label not in ('Active Leases',) else value_format)
            else:
                worksheet.write(row, 2, label, label_format)
                worksheet.write(row, 3, value, currency_format if isinstance(value, (int, float)) and label not in ('Active Leases',) else value_format)
                row += 1

        if len(finance_data) % 2 != 0:
            row += 1

        row += 1
        worksheet.merge_range(row, 0, row, 4, 'LEASE HISTORY', header_format)
        row += 1

        headers = ['Tenant', 'Rent', 'Start Date', 'End Date', 'Status']
        for col, header in enumerate(headers):
            worksheet.write(row, col, header, table_header_format)
        lease_header_row = row
        row += 1

        if property_obj.lease_ids:
            for lease in property_obj.lease_ids.sorted(key=lambda rec: rec.start_date, reverse=True):
                is_alternate = (row - lease_header_row) % 2 == 0
                row_format = alternate_format if is_alternate else data_format
                row_currency_format = alternate_currency_format if is_alternate else currency_format
                row_date_format = alternate_date_format if is_alternate else date_format
                worksheet.write(row, 0, safe_value(lease.tenant_id.name or 'Unknown'), row_format)
                worksheet.write(row, 1, lease.monthly_rent or 0, row_currency_format)
                worksheet.write(row, 2, lease.start_date or '', row_date_format)
                worksheet.write(row, 3, lease.end_date or '', row_date_format)
                worksheet.write(row, 4, dict(lease._fields['state'].selection).get(lease.state, ''), row_format)
                row += 1
        else:
            worksheet.merge_range(row, 0, row, 4, 'No lease history available for this property.', note_format)
            row += 1

        if property_obj.lease_ids:
            worksheet.autofilter(lease_header_row, 0, row - 1, 4)

        # Payment rows contain financial details and are included only for property managers.
        if request.env.user.has_group('real_estate.group_property_manager'):
            row += 2
            worksheet.merge_range(row, 0, row, 8, 'PAYMENT DETAILS', header_format)
            row += 1

            payment_headers = [
                'Tenant', 'Lease Reference', 'Due Date', 'Payment Date',
                'Amount Due', 'Late Fee', 'Total Amount', 'Payment Method', 'Status',
            ]
            for col, header in enumerate(payment_headers):
                worksheet.write(row, col, header, table_header_format)
            payment_header_row = row
            row += 1

            payments = property_obj.lease_ids.mapped('payment_ids').sorted(
                key=lambda payment: (payment.payment_date or payment.due_date, payment.id),
                reverse=True,
            )
            if payments:
                for payment in payments:
                    is_alternate = (row - payment_header_row) % 2 == 0
                    row_format = alternate_format if is_alternate else data_format
                    row_currency_format = alternate_currency_format if is_alternate else currency_format
                    row_date_format = alternate_date_format if is_alternate else date_format
                    method_label = dict(payment._fields['payment_method'].selection).get(
                        payment.payment_method, 'Not specified'
                    )
                    state_label = dict(payment._fields['state'].selection).get(payment.state, '')

                    worksheet.write(row, 0, safe_value(payment.tenant_id.name or 'Unknown'), row_format)
                    worksheet.write(row, 1, safe_value(payment.lease_id.name), row_format)
                    worksheet.write(row, 2, payment.due_date or '', row_date_format)
                    worksheet.write(row, 3, payment.payment_date or '', row_date_format)
                    worksheet.write(row, 4, payment.amount or 0, row_currency_format)
                    worksheet.write(row, 5, payment.late_fee or 0, row_currency_format)
                    worksheet.write(row, 6, payment.total_amount or 0, row_currency_format)
                    worksheet.write(row, 7, method_label, row_format)
                    worksheet.write(row, 8, state_label, row_format)
                    row += 1
            else:
                worksheet.merge_range(row, 0, row, 8, 'No payment records available for this property.', note_format)
                row += 1

            if payments:
                worksheet.autofilter(payment_header_row, 0, row - 1, 8)

        workbook.close()
        output.seek(0)
        filename = f'Property_{property_obj.name.replace(" ", "_")}.xlsx'

        return request.make_response(
            output.read(),
            headers=[
                ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
                ('Content-Disposition', content_disposition(filename)),
            ],
        )