from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class LeaseReportSummary(models.AbstractModel):
    _name = 'report.real_estate.report_lease_summary'
    _description = 'Lease Summary Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        leases = self.env['real_estate.lease'].browse(docids).exists()
        today = fields.Date.today()
        maintenance_period_start = today - relativedelta(months=6)

        payments_received = {lease.id: 0.0 for lease in leases}
        payments = self.env['lease.payment'].search([
            ('lease_id', 'in', leases.ids),
            ('state', 'in', ['paid', 'reconciled']),
        ])
        for payment in payments:
            payments_received[payment.lease_id.id] += payment.total_amount or 0.0

        maintenance_costs = {lease.id: 0.0 for lease in leases}
        maintenance_requests = self.env['maintenance.request'].search([
            ('lease_id', 'in', leases.ids),
            ('state', '=', 'done'),
            ('completion_date', '>=', maintenance_period_start),
            ('completion_date', '<=', today),
        ])
        for request in maintenance_requests:
            maintenance_costs[request.lease_id.id] += request.actual_cost or 0.0

        return {
            'doc_ids': leases.ids,
            'doc_model': 'real_estate.lease',
            'docs': leases,
            'payments_received': payments_received,
            'maintenance_costs': maintenance_costs,
            'maintenance_period_start': maintenance_period_start,
            'maintenance_period_end': today,
        }
