# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta


class MaintenanceRequest(models.Model):
    _name = 'maintenance.request'
    _description = 'Property Maintenance Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================
    # Basic Information
    # ============================================================
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, default='New')
    description = fields.Text(string='Description', tracking=True)
    state = fields.Selection(
        [
            ('submitted', 'Submitted'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='submitted',
        required=True,
        tracking=True,
    )

    # ============================================================
    # Classification
    # ============================================================
    issue_type = fields.Selection(
        [
            ('plumbing', 'Plumbing'),
            ('electrical', 'Electrical'),
            ('air_condition', 'Air Condition'),
            ('appliance', 'Appliance'),
            ('other', 'Other'),
        ],
        string='Issue Type',
        required=True,
        tracking=True,
    )
    urgency = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('emergency', 'Emergency'),
        ],
        string='Urgency',
        default='medium',
        required=True,
        tracking=True,
    )

    # ============================================================
    # Relationships
    # ============================================================
    lease_id = fields.Many2one(
        'real_estate.lease',
        string='Lease',
        required=True,
        ondelete='cascade',
        index=True,
    )
    property_id = fields.Many2one(
        related='lease_id.property_id',
        string='Property',
        store=True,
        readonly=True,
    )

    # ============================================================
    # Scheduling & Assignment
    # ============================================================
    scheduled_date = fields.Date(string='Scheduled Date', tracking=True)
    completion_date = fields.Date(string='Completion Date', readonly=True)
    preferred_date = fields.Date(string='Preferred Date')
    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True)

    # ============================================================
    # Costs & Billing
    # ============================================================
    actual_cost = fields.Float(string='Actual Cost')
    electricity_bill_date = fields.Date(string='Electricity Bill Date')
    tenant_phone = fields.Char(string='Tenant Phone')

    # ============================================================
    # CRUD Overrides
    # ============================================================
    @api.model
    def create(self, vals):
        """Generate reference from sequence on create."""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('maintenance.request.sequence') or 'New'

        if vals.get('urgency') == 'emergency' and not vals.get('scheduled_date'):
            vals['scheduled_date'] = (fields.Date.today() + timedelta(days=1)).isoformat()

        return super(MaintenanceRequest, self).create(vals)

    def schedule_emergency_request(self):
        """Set an emergency request to be scheduled for tomorrow."""
        for record in self:
            if record.urgency == 'emergency':
                record.scheduled_date = fields.Date.today() + timedelta(days=1)

    @api.onchange('urgency')
    def _onchange_urgency(self):
        """Auto-schedule emergency maintenance requests for tomorrow."""
        if self.urgency == 'emergency':
            self.schedule_emergency_request()

    # ============================================================
    # State Transition Actions
    # ============================================================
    def action_set_in_progress(self):
        """Mark request as in progress."""
        self.write({'state': 'in_progress'})

    def action_set_done(self):
        """Mark request as done and set completion date."""
        self.write({
            'state': 'done',
            'completion_date': fields.Date.today(),
        })

    def action_set_cancelled(self):
        """Cancel the maintenance request."""
        self.write({'state': 'cancelled'})

    def action_reset_to_submitted(self):
        """Reset request back to submitted state."""
        self.write({'state': 'submitted'})