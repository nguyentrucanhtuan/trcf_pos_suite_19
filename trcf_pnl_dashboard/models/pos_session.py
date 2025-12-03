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
