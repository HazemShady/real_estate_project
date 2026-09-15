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
