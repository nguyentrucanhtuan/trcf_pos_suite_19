# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class TrcfExpense(models.Model):
    _name = 'trcf.expense'
    _description = 'Expense'
    _order = 'create_date desc'

    name = fields.Char(
        string='Expense Name',
        required=True,
        help='Short description of the expense'
    )
    
    trcf_reference = fields.Char(
        string='Reference',
        readonly=True,
        copy=False,
        default='New',
        help='Auto-generated expense reference number'
    )
    
    trcf_category_id = fields.Many2one(
        'trcf.expense.category',
        string='Category',
        required=True,
        help='Expense category'
    )
    
    trcf_amount = fields.Float(
        string='Amount',
        required=True,
        help='Total expense amount'
    )
    
    trcf_payment_method_id = fields.Many2one(
        'pos.payment.method',
        string='Payment Method',
        help='Payment method used for this expense'
    )
    
    trcf_payment_date = fields.Datetime(
        string='Payment Date',
        help='Date and time when payment was made'
    )
    
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1),
        readonly=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        readonly=True
    )
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('approved', 'Đã duyệt'),
        ('paid', 'Đã thanh toán')
    ], string='State', default='draft', required=True)
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('trcf_reference', 'New') == 'New':
                vals['trcf_reference'] = self.env['ir.sequence'].next_by_code('trcf.expense') or 'New'
        return super(TrcfExpense, self).create(vals_list)
    
    def action_approve(self):
        """Approve expense"""
        for expense in self:
            if expense.state != 'draft':
                raise UserError(_('Only draft expenses can be approved.'))
            expense.write({'state': 'approved'})
        return True
    
    def action_mark_paid(self):
        """Mark expense as paid"""
        for expense in self:
            if expense.state == 'paid':
                raise UserError(_('Expense is already marked as paid.'))
            if expense.state == 'draft':
                raise UserError(_('Please approve the expense before marking it as paid.'))
            
            expense.write({
                'state': 'paid',
                'trcf_payment_date': fields.Datetime.now()
            })
        return True
    
    def action_reset_to_draft(self):
        """Reset expense to draft"""
        for expense in self:
            expense.write({
                'state': 'draft',
                'trcf_payment_date': False
            })
        return True
    
    def action_reset_to_approved(self):
        """Reset expense to approved (cancel payment)"""
        for expense in self:
            if expense.state != 'paid':
                raise UserError(_('Only paid expenses can be reset to approved.'))
            expense.write({
                'state': 'approved',
                'trcf_payment_date': False
            })
        return True
    
    @api.onchange('state')
    def _onchange_state(self):
        """Auto-set payment date when state changes to paid"""
        if self.state == 'paid' and not self.trcf_payment_date:
            self.trcf_payment_date = fields.Datetime.now()
        elif self.state in ('draft', 'approved'):
            self.trcf_payment_date = False
