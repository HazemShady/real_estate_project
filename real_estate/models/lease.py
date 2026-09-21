from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from datetime import timedelta

class Lease(models.Model):
    _name = 'real_estate.lease'
    _description = 'Property Lease Agreement'
    maintenance_ids = fields.One2many('maintenance.request', 'lease_id', string='Maintenance') 
    total_cost = fields.Float(string='Total Maintenance Cost', compute='_compute_total_cost', store=True)
    electricity_bill_ids = fields.Date(string='Electricity Bill Dates', onchange='_onchange_electricity_bill_ids')
    name = fields.Char(string='Lease Reference', required=True)
    property_id = fields.Many2one(
        'real_estate.property',
        string='Property',
        required=True,
        ondelete='cascade',
        index=True,
    )
    notes = fields.Text(string='Notes')
    tenant_id = fields.Many2one(
        'real_estate.tenant',
        string='Tenant',
        required=True,
        ondelete='cascade',
        index=True,
    )
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    monthly_rent = fields.Float(string='Monthly Rent', required=True)
    deposit_paid = fields.Float(string='Deposit Paid')
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
    )

    def action_set_active(self):
        """Mark the lease as active."""
        for record in self:
            record.write({'state': 'active'})

    def action_set_at_risk(self):
        """Mark the lease as at risk."""
        for record in self:
            record.write({'state': 'at_risk'})

    def set_back_to_draft(self):
        """Set the lease back to draft."""
        for record in self:
            record.write({'state': 'draft'})

    def copy(self, default=None):
        """Prevent duplicating lease records."""
        raise UserError("You cant copy a lease")

    # def copy(self, default=None):
    #     """Old copy behavior kept for reference."""
    #     return super(Lease, self).copy(default=default)

    @api.model
    def create(self, vals):
        """Override create to generate lease reference"""
        vals['name'] = self.env['ir.sequence'].next_by_code('real_estate.lease')
        return super(Lease, self).create(vals)
    tenant_age = fields.Integer(string='Tenant Age', compute='_compute_tenant_age', store=True)
    duration_months = fields.Integer(string='Duration (Months)', compute='_compute_duration', store=True)
    is_active = fields.Boolean(string='Currently Active', compute='_compute_is_active')

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """Calculate lease duration in months"""
        for record in self:
            if record.start_date and record.end_date:
                delta = record.end_date - record.start_date
                record.duration_months = int(delta.days / 30)
            else:
                record.duration_months = 0

    @api.depends('start_date', 'end_date', 'state')
    def _compute_is_active(self):
        """Check if lease is currently active"""
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
                age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
                record.tenant_age = age
            else:
                record.tenant_age = 0                
    @api.onchange('property_id')
    def _onchange_property_id(self):
        """Set default price when property is selected and validate availability"""
        if self.property_id and not self.property_id.available:
            raise ValidationError("The selected property is not available.")
        if self.property_id and self.property_id.price:
            self.monthly_rent = self.property_id.price 
            self.deposit_paid= self.property_id.price * 0.1  # Assuming deposit is 10% of the price
            
    @api.onchange('start_date')
    def _onchange_electricity_bill_ids(self):
        """Set default end date when start date is selected."""
        if self.start_date:
            self.electricity_bill_ids = self.start_date + timedelta(days=30)  # Assuming 30-day lease term
    
    def action_create_electricity_bill(self):
        """Create an electrical maintenance request for this lease."""
        self.ensure_one()
        if not self.electricity_bill_ids:
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
            'electricity_bill_date': self.electricity_bill_ids,
            'preferred_date': self.electricity_bill_ids,
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
   
    @api.depends('maintenance_ids.actual_cost')
    def _compute_total_cost(self):
        for lease in self:
            # 1
             lease.total_cost = sum(maintenance.actual_cost for maintenance in lease.maintenance_ids)

            # 2
            # lease.total_cost = 0
            # total_cost = 0
            # for maintenance in lease.maintenance_ids:
            #     if maintenance.actual_cost:
            #         total_cost += maintenance.actual_cost
            # lease.total_cost = total_cost   

            # 3
            #lease_maintenance_ids = self.env['maintenance.request'].search([('lease_id', '=', lease.id)])  
            #lease.total_cost = 0
            #for maintenance in lease_maintenance_ids:
                #if maintenance.actual_cost:
                    #lease.total_cost += maintenance.actual_cost