from odoo import fields, models


class TenantWizard(models.TransientModel):
    _name = 'real_estate.tenant.wizard'
    _description = 'Create Tenant from CRM'

    crm_id = fields.Many2one(
        'crm.lead',
        string='CRM Opportunity',
        required=True,
        readonly=True,
    )
    name = fields.Char(string='Tenant Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone Number')
    mobile = fields.Char(string='Mobile Number')
    city = fields.Char(string='City')
    date_of_birth = fields.Date(string='Date of Birth')
    age_category = fields.Selection([
        ('a', '1 to 20'),
        ('b', '21 to 40'),
        ('c', '41 and above'),
    ], string='Age Category')
    notes = fields.Text(string='Notes')

    def action_create_tenant(self):
        """Create a tenant and keep a link to the CRM opportunity."""
        self.ensure_one()
        tenant = self.env['real_estate.tenant'].create({
            'crm_id': self.crm_id.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'mobile': self.mobile,
            'city': self.city,
            'date_of_birth': self.date_of_birth,
            'age_category': self.age_category,
            'notes': self.notes,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Tenant',
            'res_model': 'real_estate.tenant',
            'res_id': tenant.id,
            'view_mode': 'form',
            'target': 'current',
        }
