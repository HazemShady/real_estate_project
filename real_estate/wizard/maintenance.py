from odoo import models, fields, api

class MaintenanceRequestWizard(models.TransientModel):
    _name = 'maintenance.request.wizard'
    _description = 'Maintenance Request Wizard'
    
    lease_id = fields.Many2one('real_estate.lease', required=True)
    property_id = fields.Many2one('real_estate.property', related='lease_id.property_id', readonly=True)
    
    issue_type = fields.Selection([
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('air_condition', 'Air Condition'),
        ('appliance', 'Appliance'),
        ('other', 'Other')
    ], required=True)
    
    description = fields.Text(required=True)
    urgency = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('emergency', 'Emergency')
    ], default='medium', required=True)
    
    preferred_date = fields.Date()
    electricity_bill_date = fields.Date(
        string='Electricity Bill Date',
        required=True,
        default=lambda self: self.env.context.get('default_electricity_bill_date'),
    )
    tenant_phone = fields.Char()
    
    def action_submit_request(self):
        """Create maintenance request and notify manager"""
        self.ensure_one()
        
        # 1. Create maintenance.request record
        maintenance_request = self.env['maintenance.request'].create({
            'property_id': self.property_id.id,
            'lease_id': self.lease_id.id,
            'issue_type': self.issue_type,
            'description': self.description,
            'urgency': self.urgency,
            'electricity_bill_date': self.electricity_bill_date,
            'preferred_date': self.preferred_date,
            'tenant_phone': self.tenant_phone,
            'state': 'submitted',
        })
        
        # 2. Send notification to property manager (Agent)
        # if self.property_id.agent_id:
        #     maintenance_request.activity_schedule(
        #         'mail.mail_activity_data_todo',
        #         user_id=self.property_id.agent_id.id,
        #         summary=f"New {self.issue_type.capitalize()} Maintenance Request",
        #         note=f"Urgency: {self.urgency}\nDescription: {self.description}"
        #     )
        
        # 3. Return action to close wizard and show confirmation
        return {
            'type': 'ir.actions.act_window',
                        'name': 'Maintenance Request',
                        'res_model': 'maintenance.request',
                        'res_id': maintenance_request.id,
                        'view_mode': 'form',
                        'target': 'current',
        }
