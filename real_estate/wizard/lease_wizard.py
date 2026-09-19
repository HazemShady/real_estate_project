from odoo import api, fields, models


class LeaseWizard(models.TransientModel):
    _name = 'real_estate.lease.wizard'
    _description = 'Create Lease Wizard'

    property_id = fields.Many2one(
        'real_estate.property',
        string='Property',
        required=True,
    )
    tenant_id = fields.Many2one(
        'real_estate.tenant',
        string='Tenant',
        required=True,
    )
    start_date = fields.Date(
        string='Start Date',
        required=True,
        default=fields.Date.context_today,
    )
    end_date = fields.Date(
        string='End Date',
        required=True,
    )
    monthly_rent = fields.Float(
        string='Monthly Rent',
        required=True,
    )
    deposit_paid = fields.Float(
        string='Deposit Paid',
        default=0.0,
    )

    @api.onchange('property_id')
    def _onchange_property_id(self):
        if self.property_id:
            self.monthly_rent = self.property_id.price

    def action_create_lease(self):
        self.ensure_one()
        self.env['real_estate.lease'].create({
            'property_id': self.property_id.id,
            'tenant_id': self.tenant_id.id,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'monthly_rent': self.monthly_rent,
            'deposit_paid': self.deposit_paid,
            'state': 'draft',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'real_estate.property',
            'view_mode': 'tree,form',
            'target': 'current',
        }