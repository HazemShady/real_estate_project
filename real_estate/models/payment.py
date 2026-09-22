from odoo import models, fields, api
from odoo.exceptions import UserError
from datetime import timedelta

class LeasePayment(models.Model):
    _name = 'lease.payment'
    _description = 'Lease Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date desc, id desc'
    
    name = fields.Char(string='Payment Reference', required=True, copy=False, readonly=True, default='New')
    lease_id = fields.Many2one('real_estate.lease', string='Lease', required=True, ondelete='cascade')
    tenant_id = fields.Many2one(related='lease_id.tenant_id', string='Tenant', store=True)
    property_id = fields.Many2one(related='lease_id.property_id', string='Property', store=True)
    
    due_date = fields.Date(string='Due Date', required=True, tracking=True)
    amount = fields.Float(string='Amount Due', required=True, tracking=True)
    late_fee = fields.Float(string='Late Fee', tracking=True)
    late_fee_applied = fields.Boolean(string='Late Fee Applied', default=False)
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)
    
    payment_date = fields.Date(string='Payment Date', tracking=True)
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('other', 'Other')
    ], string='Payment Method')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('reconciled', 'Reconciled')
    ], default='draft', required=True, tracking=True)

    notes = fields.Text(string='Notes')

    @api.depends('amount', 'late_fee')
    def _compute_total_amount(self):
        for record in self:
            record.total_amount = record.amount + record.late_fee