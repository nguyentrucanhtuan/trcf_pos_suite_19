# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TRCFPosSessionPaymentCount(models.Model):
    _name = 'trcf.pos.session.payment.count'
    _description = 'Kiểm kê phương thức thanh toán theo ca POS'
    _order = 'session_id desc, payment_method_id'
    
    session_id = fields.Many2one(
        'pos.session',
        string='Ca bán hàng',
        required=True,
        ondelete='cascade',
        index=True
    )
    
    payment_method_id = fields.Many2one(
        'pos.payment.method',
        string='Phương thức thanh toán',
        required=True,
        index=True
    )
    
    payment_method_name = fields.Char(
        related='payment_method_id.name',
        string='Tên phương thức thanh toán',
        readonly=True
    )
    
    opening_amount = fields.Monetary(
        string='Số dư đầu ca',
        currency_field='currency_id',
        help='Số dư đầu ca cho phương thức thanh toán này'
    )
    
    income_amount = fields.Monetary(
        string='Thu vào',
        currency_field='currency_id',
        help='Tổng thu từ các thanh toán'
    )
    
    expense_amount = fields.Monetary(
        string='Chi ra',
        currency_field='currency_id',
        help='Tổng chi trả bằng phương thức thanh toán này'
    )
    
    expected_amount = fields.Monetary(
        string='Số tiền lý thuyết',
        currency_field='currency_id',
        compute='_compute_expected_amount',
        store=True,
        help='Số tiền lý thuyết = Đầu ca + Thu vào - Chi ra'
    )
    
    counted_amount = fields.Monetary(
        string='Số tiền kiểm kê',
        currency_field='currency_id',
        help='Số tiền thực tế kiểm kê do nhân viên nhập'
    )
    
    difference = fields.Monetary(
        string='Chênh lệch',
        currency_field='currency_id',
        compute='_compute_difference',
        store=True,
        help='Chênh lệch = Kiểm kê - Lý thuyết (dương = thừa, âm = thiếu)'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        related='session_id.currency_id',
        string='Tiền tệ',
        store=True
    )
    
    company_id = fields.Many2one(
        'res.company',
        related='session_id.company_id',
        string='Công ty',
        store=True
    )

    session_state = fields.Selection(
        related='session_id.state',
        string='Trạng thái ca',
        store=True
    )

    # Trường để xác định xem có phải phương thức tiền mặt không
    is_cash_pm = fields.Boolean(
        related='payment_method_id.is_cash_count',
        string='Là tiền mặt',
        store=True
    )

    # Số tiền lấy về (chỉ dành cho tiền mặt)
    trcf_owner_withdrawal = fields.Monetary(
        string='Số tiền lấy về',
        currency_field='currency_id',
        compute='_compute_withdrawal_and_opening',
        store=True,
        help='Số tiền owner rút khỏi két (chỉ áp dụng cho tiền mặt)'
    )

    # Tiền mặt mở ca sau (chỉ dành cho tiền mặt)
    trcf_next_session_opening = fields.Monetary(
        string='Tiền mặt mở ca sau',
        currency_field='currency_id',
        compute='_compute_withdrawal_and_opening',
        store=True,
        help='Số tiền để lại làm số dư đầu ca cho phiên tiếp theo (chỉ áp dụng cho tiền mặt)'
    )

    @api.depends('is_cash_pm', 'session_id.trcf_owner_withdrawal', 'session_id.trcf_next_session_opening')
    def _compute_withdrawal_and_opening(self):
        """
        Tính số tiền lấy về và số tiền mở ca sau:
        - Chỉ áp dụng cho tiền mặt, lấy từ session
        - Các phương thức khác: = 0
        """
        for record in self:
            if record.is_cash_pm:
                # Tiền mặt: lấy từ session
                record.trcf_owner_withdrawal = record.session_id.trcf_owner_withdrawal
                record.trcf_next_session_opening = record.session_id.trcf_next_session_opening
            else:
                # Các phương thức khác: không áp dụng
                record.trcf_owner_withdrawal = 0.0
                record.trcf_next_session_opening = 0.0

    @api.depends('opening_amount', 'income_amount', 'expense_amount')
    def _compute_expected_amount(self):
        """Tính số tiền lý thuyết"""
        for record in self:
            record.expected_amount = record.opening_amount + record.income_amount - record.expense_amount

    @api.depends('counted_amount', 'expected_amount')
    def _compute_difference(self):
        """Tính chênh lệch giữa kiểm kê và lý thuyết"""
        for record in self:
            record.difference = record.counted_amount - record.expected_amount
    
    _sql_constraints = [
        ('unique_session_payment_method',
         'UNIQUE(session_id, payment_method_id)',
         'Mỗi phương thức thanh toán chỉ có thể có một bản ghi kiểm kê cho mỗi ca!')
    ]
