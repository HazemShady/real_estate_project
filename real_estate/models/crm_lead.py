# -*- coding: utf-8 -*-
from odoo import models, fields
from odoo import api

class CrmLead(models.Model):
    _inherit = 'crm.lead'

    # ============================================================
    # Real Estate Fields
    # Extension of CRM lead for real estate property types
    # ============================================================
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

    # ============================================================
    # Actions
    # ============================================================
    def action_add_name_to_notes(self):
        """Append lead name to description if not already present."""
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
            'view_id': self.env.ref('real_estate.view_real_estate_tenant_wizard_form').id,
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
    @api.model
    def cron_gnerate_tenant_from_lead(self):
        """Scheduled action to convert leads to tenants based on criteria."""
        leads_to_convert = self.search([
            ('type', '=', 'opportunity'),
            ('property_type', '!=', False),
            ('state', '=', 'won'),
        ])
        for lead in leads_to_convert:
            if not self.env['real_estate.tenant'].search([('crm_id', '=', lead.id)]):
                tenant_vals = {
                    'name': lead.contact_name or lead.partner_name or 'Unnamed Tenant',
                    'email': lead.email_from,
                    'phone': lead.phone,
                    'mobile': lead.mobile,
                    'city': lead.city,
                    'crm_id': lead.id,
                }
                self.env['real_estate.tenant'].create(tenant_vals)