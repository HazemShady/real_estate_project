# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError


class LeasePayment(models.Model):
    _name = 'lease.payment'
    _description = 'Lease Payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'due_date desc, id desc'

    # ============================================================
    # Basic Information
    # ============================================================
    name = fields.Char(
        string='Payment Reference',
        required=True,
        copy=False,
        readonly=True,
        default='New',
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('pending', 'Pending'),
            ('paid', 'Paid'),
            ('reconciled', 'Reconciled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )

    # ============================================================
    # Relationships
    # ============================================================
    lease_id = fields.Many2one(
        'real_estate.lease',
        string='Lease',
        required=True,
        ondelete='cascade',
        index=True,
    )
    tenant_id = fields.Many2one(
        related='lease_id.tenant_id',
        string='Tenant',
        store=True,
        readonly=True,
    )
    property_id = fields.Many2one(
        related='lease_id.property_id',
        string='Property',
        store=True,
        readonly=True,
    )

    # ============================================================
    # Payment Details
    # ============================================================
    due_date = fields.Date(string='Due Date', required=True, tracking=True)
    payment_date = fields.Date(string='Payment Date', tracking=True)
    payment_method = fields.Selection(
        [
            ('cash', 'Cash'),
            ('check', 'Check'),
            ('bank_transfer', 'Bank Transfer'),
            ('credit_card', 'Credit Card'),
            ('other', 'Other'),
        ],
        string='Payment Method',
    )

    # ============================================================
    # Financial Amounts
    # ============================================================
    amount = fields.Float(string='Amount Due', required=True, tracking=True)
    late_fee = fields.Float(string='Late Fee', tracking=True)
    late_fee_applied = fields.Boolean(string='Late Fee Applied', default=False)
    total_amount = fields.Float(string='Total Amount', compute='_compute_total_amount', store=True)

    # ============================================================
    # Additional Information
    # ============================================================
    notes = fields.Text(string='Notes')

    # ============================================================
    # CRUD Overrides
    # ============================================================
    @api.model
    def create(self, vals):
        """Generate payment reference from sequence on create."""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('lease.payment') or 'New'
        return super(LeasePayment, self).create(vals)

    # ============================================================
    # Computed Fields
    # ============================================================
    @api.depends('amount', 'late_fee')
    def _compute_total_amount(self):
        """Compute total amount including late fee."""
        for record in self:
            record.total_amount = record.amount + record.late_fee

    # ============================================================
    # State Transition Actions
    # ============================================================
    def action_set_pending(self):
        """Mark payment as pending."""
        self.write({'state': 'pending'})

    def action_set_paid(self):
        """Mark payment as paid and set payment date if not set."""
        vals = {'state': 'paid'}
        for record in self:
            if not record.payment_date:
                vals['payment_date'] = fields.Date.today()
        self.write(vals)

    def action_set_reconciled(self):
        """Mark payment as reconciled."""
        self.write({'state': 'reconciled'})

    def action_reset_to_draft(self):
        """Reset payment to draft state."""
        self.write({'state': 'draft'})
    
    def _cron_auto_mark_paid(self):
        """Scheduled action - mark payments with amount as paid"""
        pending_payments = self.search([
            ('amount', '>', 0),
            ('state', 'in', ['draft', 'pending']),
        ])
        for payment in pending_payments:
            payment.write({'state': 'paid'})