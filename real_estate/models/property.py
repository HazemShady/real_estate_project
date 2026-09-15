
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
            if vals["available"] == True and vals.get('bedrooms') != self.bedrooms :
                raise UserError("You cannot edit Bedrooms while the property is unavailable.")

        return super(Property, self).write(vals)