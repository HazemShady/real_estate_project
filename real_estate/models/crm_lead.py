from odoo import models, fields


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    property_type = fields.Selection([
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('villa', 'Villa'),
        ('commercial', 'Commercial'),
    ], string='Property Type', required=True)

    def action_add_name_to_notes(self):
        for lead in self:
            lead_name = lead.name or 'Unnamed Lead'

            if lead.description and lead_name in lead.description:
                continue

            if lead.description:
                lead.description = f"{lead.description}\n\n{lead_name}"
            else:
                lead.description = lead_name

    def action_open_tenant_wizard(self):
        """Open a tenant form pre-linked to this CRM opportunity."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Tenant',
            'res_model': 'real_estate.tenant.wizard',
            'view_mode': 'form',
            'view_id': self.env.ref(
                'real_estate.view_real_estate_tenant_wizard_form'
            ).id,
            'target': 'new',
            'context': {
                'default_crm_id': self.id,
                'default_name': self.contact_name or self.partner_name or '',
                'default_email': self.email_from or '',
                'default_phone': self.phone or '',
                'default_mobile': self.mobile or '',
                'default_city': self.city or '',
            },
        }
