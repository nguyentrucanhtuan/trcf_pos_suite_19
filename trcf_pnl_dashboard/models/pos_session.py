# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TrcfPosSession(models.Model):
    _inherit = 'pos.session'
    
    # Số tiền lấy về (owner withdrawal)
    trcf_owner_withdrawal = fields.Monetary(
        string='Số tiền lấy về',
        currency_field='currency_id',
        help='Số tiền owner rút khỏi két sau khi đóng ca',
        default=0.0
    )
    
    # Tiền mặt mở ca sau
    trcf_next_session_opening = fields.Monetary(
        string='Tiền mặt mở ca sau',
        currency_field='currency_id',
        help='Số tiền để lại làm số dư đầu ca cho phiên tiếp theo (= Tiền đếm - Tiền lấy về)',
        default=0.0
    )
    
    @api.model
    def get_payment_income_by_method(self, session_id, start_at, stop_at):
        """
        Calculate payment income grouped by payment method using _read_group
        
        Args:
            session_id: POS session ID
            start_at: Session start datetime (UTC string format: 'YYYY-MM-DD HH:MM:SS')
            stop_at: Session stop datetime (UTC string format: 'YYYY-MM-DD HH:MM:SS')
        
        Returns:
            dict: {payment_method_id: total_amount}
            Example: {4: 1500000.0, 5: 500000.0}
        """
        # Build domain for payments in this session
        # Match Odoo's standard calculation:
        # 1. Filter by session_id
        # 2. Only include payments from closed orders (not draft/cancel) - matching _get_closed_orders()
        # NOTE: Do NOT filter is_change! Odoo includes change payments in the total
        domain = [
            ('session_id', '=', session_id),
            ('pos_order_id.state', 'not in', ['draft', 'cancel']),  # Only closed orders
        ]
        
        # Use _read_group to aggregate by payment method (much more efficient than looping)
        result = self.env['pos.payment']._read_group(
            domain=domain,
            groupby=['payment_method_id'],
            aggregates=['amount:sum']
        )
        
        # Convert to dict {payment_method_id: total_amount}
        # _read_group returns list of tuples: [(payment_method, amount_sum), ...]
        # Filter out pay_later payment methods (like Odoo does in get_closing_control_data line 712)
        payment_income = {}
        for payment_method, amount_sum in result:
            # payment_method is returned as recordset or False
            if payment_method and payment_method.type != 'pay_later':
                payment_income[payment_method.id] = amount_sum or 0
        
        return payment_income
