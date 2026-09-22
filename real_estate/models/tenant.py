# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class Tenant(models.Model):
    _name = 'real_estate.tenant'
    _description = 'Real Estate Tenant'
    _order = 'name asc'

    # ============================================================
    # Core Information
    # Basic tenant identification fields
    # ============================================================
    name = fields.Char(string='Tenant Name', required=True, index=True)
    email = fields.Char(string='Email', required=True, index=True)
    phone = fields.Char(string='Phone Number')
    mobile = fields.Char(string='Mobile Number')
    city = fields.Char(string='City')
    date_of_birth = fields.Date(string='Date of Birth')
    age_category = fields.Selection([
        ('a', '1 to 20'),
        ('b', '21 to 40'),
        ('c', '41 and above'),
    ], string='Age Category')

    # ============================================================
    # Status & Dates
    # ============================================================
    date_joined = fields.Date(string='Date Joined', default=fields.Date.today, readonly=True)
    active = fields.Boolean(string='Active', default=True)

    # ============================================================
    # Additional Information
    # ============================================================
    notes = fields.Text(string='Notes')

    # ============================================================
    # Relationships
    # ============================================================
    lease_ids = fields.One2many('real_estate.lease', 'tenant_id', string='Leases')
    crm_id = fields.Many2one(
        'crm.lead',
        string='CRM Lead',
        ondelete='set null',
    )

    _sql_constraints = [
        ('email_unique', 'UNIQUE(email)', 'Email must be unique! This email is already registered.'),
    ]

    @api.constrains('date_of_birth')
    def _check_date_of_birth(self):
        """Birth date must be before today."""
        for record in self:
            if record.date_of_birth and record.date_of_birth >= fields.Date.today():
                raise ValidationError('Date of birth must be earlier than today.')

    # ============================================================
    # Actions
    # ============================================================
    def action_toggle_active(self):
        """Toggle the tenant active status."""
        for record in self:
            record.write({'active': not record.active})