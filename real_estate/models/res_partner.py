from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Real-estate specialization used for partner classification.
    specialization = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
    ], string='Specialization')