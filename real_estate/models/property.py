
from odoo import fields, models
from odoo.exceptions import UserError


class Property(models.Model):
    _name = 'real_estate.property'
    _description = 'Real Estate Property'

    name = fields.Char(string='Property Name', required=True, index=True)
    description = fields.Text(string='Description')
    price = fields.Float(string='Monthly Rent', required=True)
    bedrooms = fields.Integer(string='Bedrooms', default=1)
    available = fields.Boolean(string='Available', default=True, index=True)
    lease_ids = fields.One2many('real_estate.lease', 'property_id', string='Leases') 
    agent_id = fields.Many2one('res.users', string='Sales Person')
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
    deposit = fields.Float(required=True)

    def mark_as_occupied(self):
        """Mark property as no longer available."""
        for record in self:
            record.write({'available': False, 'price': record.price + 1000})

    def mark_as_available(self):
        """Mark property as available."""
        for record in self:
            record.write({'available': True})

    def add_text(self):
        """Add text to the description field."""
        for record in self:
            record.write({'description': record.description + ' Description '})

    def increse_deposit(self):
        """Increase deposit by 10%."""
        for record in self:
            record.write({'deposit': record.deposit + 1000})

    def add_bedroom(self):
        """Add a bedroom to the property."""
        for record in self:
            record.write({'bedrooms': record.bedrooms + 1})

    def mark_as_villa(self):
        """Change the property type to Villa."""
        for record in self:
            if record.available:
                record.write({'property_type': 'villa'})

    def get_agent_name(self):
        for record in self:
            record.write({'description': record.agent_id.name}) 
    
    def write(self, vals):
        if 'bedrooms' in vals:
            available = vals.get('available', self.available)
            if available is False and vals.get('bedrooms') != self.bedrooms:
                raise UserError("You cannot edit bedrooms while the property is unavailable.")

        return super(Property, self).write(vals)
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
            