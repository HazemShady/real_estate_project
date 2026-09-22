
# -*- coding: utf-8 -*-
from odoo import fields, models
from odoo.exceptions import UserError


class Property(models.Model):
    _name = 'real_estate.property'
    _description = 'Real Estate Property'
    _order = 'name'

    # ============================================================
    # Property Information
    # Fields related to the basic property information
    # ============================================================
    name = fields.Char(string='Property Name', required=True, index=True)
    description = fields.Text(string='Description')
    property_image = fields.Binary(string='Property Image')
    property_type = fields.Selection(
        [
            ('apartment', 'Apartment'),
            ('house', 'House'),
            ('villa', 'Villa'),
            ('commercial', 'Commercial'),
        ],
        string='Property Type',
        required=True,
    )
    bedrooms = fields.Integer(string='Bedrooms', default=1)

    # ============================================================
    # Financial Information
    # Fields related to pricing and deposits
    # ============================================================
    price = fields.Float(string='Monthly Rent', required=True)
    deposit = fields.Float(string='Deposit Amount', required=True)
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )

    # ============================================================
    # Status & Availability
    # Fields for tracking property status
    # ============================================================
    available = fields.Boolean(string='Available', default=True, index=True)

    # ============================================================
    # Relationships
    # Relational fields to other models
    # ============================================================
    agent_id = fields.Many2one('res.users', string='Sales Person', index=True)
    lease_ids = fields.One2many('real_estate.lease', 'property_id', string='Leases')

    # ============================================================
    # Constraints & Overrides
    # ============================================================
    def write(self, vals):
        """Prevent editing bedrooms when property is unavailable."""
        if 'bedrooms' in vals:
            # Check if any record in self is unavailable
            for record in self:
                new_available = vals.get('available', record.available)
                if new_available is False and vals.get('bedrooms') != record.bedrooms:
                    raise UserError("You cannot edit bedrooms while the property is unavailable.")
        return super(Property, self).write(vals)

    # ============================================================
    # Actions
    # ============================================================
    def action_show_leases(self):
        """Action to show leases related to the property."""
        self.ensure_one()
        return {
            'name': 'Leases',
            'type': 'ir.actions.act_window',
            'res_model': 'real_estate.lease',
            'view_mode': 'tree,form',
            'domain': [('property_id', '=', self.id)],
            'context': {'default_property_id': self.id},
        }

    def action_toggle_availability(self):
        """Toggle the property availability status."""
        for record in self:
            record.write({'available': not record.available})
            