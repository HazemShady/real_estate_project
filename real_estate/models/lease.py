# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


class Lease(models.Model):
    _name = 'real_estate.lease'
    _description = 'Property Lease Agreement'
    _order = 'create_date desc'

    # ============================================================
    # Basic Information
    # ============================================================
    name = fields.Char(string='Lease Reference', required=True, copy=False, readonly=True, default='New')
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('at_risk', 'At Risk'),
            ('expired', 'Expired'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )

    # ============================================================
    # Relationships
    # ============================================================
    property_id = fields.Many2one(
        'real_estate.property',
        string='Property',
        required=True,
        ondelete='cascade',
        index=True,
    )
    tenant_id = fields.Many2one(
        'real_estate.tenant',
        string='Tenant',
        required=True,
        ondelete='cascade',
        index=True,
    )

    # ============================================================
    # Lease Dates & Duration
    # ============================================================
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    duration_months = fields.Integer(string='Duration (Months)', compute='_compute_duration', store=True)
    is_active = fields.Boolean(string='Currently Active', compute='_compute_is_active')

    # ============================================================
    # Financial Details
    # ============================================================
    monthly_rent = fields.Float(string='Monthly Rent', required=True)
    deposit_paid = fields.Float(string='Deposit Paid')

    # ============================================================
    # Maintenance Costs
    # Computed total from individual cost fields
    # ============================================================
    plumbing_cost = fields.Float(string='Plumbing Cost')
    electrical_cost = fields.Float(string='Electrical Cost')
    air_condition_cost = fields.Float(string='Air Condition Cost')
    appliance_cost = fields.Float(string='Appliance Cost')
    other_cost = fields.Float(string='Other Cost')
    total_cost = fields.Float(string='Total Maintenance Cost', compute='_compute_total_cost', store=True)

    # ============================================================
    # Electricity Bill
    # Single date field for electricity bill scheduling
    # ============================================================
    electricity_bill_date = fields.Date(string='Electricity Bill Date')

    # ============================================================
    # Related Information
    # ============================================================
    maintenance_ids = fields.One2many('maintenance.request', 'lease_id', string='Maintenance Requests')
    payment_ids = fields.One2many('lease.payment', 'lease_id', string='Payments')
    tenant_age = fields.Integer(string='Tenant Age', compute='_compute_tenant_age', store=True)
    notes = fields.Text(string='Notes')

    # ============================================================
    # CRUD Overrides
    # ============================================================
    @api.model
    def create(self, vals):
        """Generate lease reference from sequence on create."""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('real_estate.lease') or 'New'
        return super(Lease, self).create(vals)

    def copy(self, default=None):
        """Prevent duplicating lease records."""
        raise UserError("You cannot copy a lease.")

    # ============================================================
    # State Transition Actions
    # ============================================================
    def action_set_active(self):
        """Mark the lease as active."""
        self.write({'state': 'active'})

    def action_set_at_risk(self):
        """Mark the lease as at risk."""
        self.write({'state': 'at_risk'})

    def set_back_to_draft(self):
        """Set the lease back to draft."""
        self.write({'state': 'draft'})

    # ============================================================
    # Computed Fields
    # ============================================================
    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """Calculate lease duration in months."""
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.duration_months = int(delta.days / 30)
            else:
                record.duration_months = 0

    @api.depends('start_date', 'end_date', 'state')
    def _compute_is_active(self):
        """Check if lease is currently active based on dates and state."""
        today = fields.Date.today()
        for record in self:
            if record.state == 'active' and record.start_date and record.end_date:
                record.is_active = record.start_date <= today <= record.end_date
            else:
                record.is_active = False

    @api.depends('tenant_id.date_of_birth')
    def _compute_tenant_age(self):
        """Compute the age of the tenant based on their date of birth."""
        today = fields.Date.today()
        for record in self:
            if record.tenant_id.date_of_birth:
                birth_date = record.tenant_id.date_of_birth
                age = today.year - birth_date.year - (
                    (today.month, today.day) < (birth_date.month, birth_date.day)
                )
                record.tenant_age = age
            else:
                record.tenant_age = 0

    @api.depends(
        'plumbing_cost',
        'electrical_cost',
        'air_condition_cost',
        'appliance_cost',
        'other_cost',
    )
    def _compute_total_cost(self):
        """Compute total maintenance cost from individual cost components."""
        for lease in self:
            lease.total_cost = sum((
                lease.plumbing_cost,
                lease.electrical_cost,
                lease.air_condition_cost,
                lease.appliance_cost,
                lease.other_cost,
            ))

    # ============================================================
    # Onchange Methods
    # ============================================================
    @api.onchange('property_id')
    def _onchange_property_id(self):
        """Set default rent and deposit when property is selected; validate availability."""
        if self.property_id:
            if not self.property_id.available:
                raise ValidationError("The selected property is not available.")
            if self.property_id.price:
                self.monthly_rent = self.property_id.price
                self.deposit_paid = self.property_id.price * 0.10  # 10% of monthly rent as deposit

    @api.onchange('start_date')
    def _onchange_start_date(self):
        """Set default electricity bill date to 30 days after start date."""
        if self.start_date:
            self.electricity_bill_date = self.start_date + timedelta(days=30)

    # ============================================================
    # Business Actions
    # ============================================================
    def action_create_electricity_bill(self):
        """Create an electrical maintenance request for this lease."""
        self.ensure_one()
        if not self.electricity_bill_date:
            raise UserError("Set the Electricity Bill Date before creating the bill.")

        self.env['maintenance.request'].create({
            'name': f'Electricity Bill - {self.name}',
            'lease_id': self.id,
            'issue_type': 'electrical',
            'description': (
                'Electricity bill created for the lease period '
                f'{self.start_date} to {self.end_date}.'
            ),
            'urgency': 'medium',
            'electricity_bill_date': self.electricity_bill_date,
            'preferred_date': self.electricity_bill_date,
            'tenant_phone': self.tenant_id.phone,
            'state': 'submitted',
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Electricity Bill Created',
                'message': 'The electrical maintenance request was created.',
                'type': 'success',
                'sticky': False,
            },
        }
    def _cron_auto_expire_leases(self):
        """Scheduled action - expire leases whose end date has passed"""
        today = fields.Date.today()
        expired_leases = self.search([
            ('end_date', '<', today),
        ])
        for lease in expired_leases:
            lease.write({'state': 'expired'})    
     
       # === VALIDATION ===
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Ensure end date is after start date"""
        for record in self:
            if record.start_date and record.end_date:
                if record.end_date <= record.start_date:
                    raise ValidationError("End date must be after start date")

    _sql_constraints = [
        ('email_unique', 'UNIQUE(email)', 'Email must be unique! This email is already registered.'),
    ]