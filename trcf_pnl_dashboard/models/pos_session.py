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
        help='Số tiền để lại làm số dư đầu ca cho phiên tiếp theo',
        compute='_compute_next_session_opening',
        store=True,
        readonly=False
    )
    
    @api.depends('cash_register_balance_end_real', 'trcf_owner_withdrawal')
    def _compute_next_session_opening(self):
        """Tính tiền mặt mở ca sau = Tiền cuối ca - Tiền lấy về"""
        for session in self:
            session.trcf_next_session_opening = session.cash_register_balance_end_real - session.trcf_owner_withdrawal
