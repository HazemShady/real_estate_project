from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class PropertyReportSummary(models.AbstractModel):
    _name = 'report.real_estate.report_property_summary'
    _description = 'Property Summary Report'

    # Prepare occupancy, payment, and maintenance data for the report.
    @api.model
    def _get_report_values(self, docids, data=None):
        properties = self.env['real_estate.property'].browse(docids).exists()
        today = fields.Date.today()
        six_months_ago = today - relativedelta(months=6)

        # Occupancy requires an active lease covering today; costs are recent, payments are lifetime.
        occupancy_rates = {}
        active_leases = {}
        empty_lease = self.env['real_estate.lease']
        for prop in properties:
            active_lease = next((
                lease for lease in prop.lease_ids
                if lease.state == 'active'
                and lease.start_date
                and lease.end_date
                and lease.start_date <= today <= lease.end_date
            ), empty_lease)
            active_leases[prop.id] = active_lease
            occupancy_rates[prop.id] = 100.0 if active_lease else 0.0

        maintenance_costs = {prop.id: 0.0 for prop in properties}
        maintenance_requests = self.env['maintenance.request'].search([
            ('property_id', 'in', properties.ids),
            ('state', '=', 'done'),
            ('completion_date', '>=', six_months_ago),
            ('completion_date', '<=', today),
        ])
        for request in maintenance_requests:
            maintenance_costs[request.property_id.id] += request.actual_cost or 0.0

        payments_received = {prop.id: 0.0 for prop in properties}
        payments = self.env['lease.payment'].search([
            ('property_id', 'in', properties.ids),
            ('state', 'in', ['paid', 'reconciled']),
        ])
        for payment in payments:
            payments_received[payment.property_id.id] += payment.total_amount or 0.0

        return {
            'doc_ids': properties.ids,
            'doc_model': 'real_estate.property',
            'docs': properties,
            'occupancy_rates': occupancy_rates,
            'active_leases': active_leases,
            'maintenance_costs': maintenance_costs,
            'maintenance_period_start': six_months_ago,
            'maintenance_period_end': today,
            'payments_received': payments_received,
        }
