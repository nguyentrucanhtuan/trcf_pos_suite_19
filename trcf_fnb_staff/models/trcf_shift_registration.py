# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TrcfShiftRegistration(models.Model):
    _name = 'trcf.shift.registration'
    _description = 'Đăng ký ca làm việc'
    _order = 'date desc, shift_id'
    _rec_name = 'display_name'

    # ===== BASIC FIELDS =====
    employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân viên',
        required=True,
        ondelete='cascade',
        help='Nhân viên đăng ký ca'
    )
    
    shift_id = fields.Many2one(
        'trcf.work.shift',
        string='Ca làm việc',
        required=True,
        ondelete='cascade',
        domain="[('active', '=', True)]",
        help='Ca làm việc đăng ký'
    )
    
    date = fields.Date(
        string='Ngày',
        required=True,
        help='Ngày đăng ký làm việc'
    )
    
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('confirmed', 'Đã duyệt'),
        ('rejected', 'Từ chối'),
    ], string='Trạng thái', default='draft', tracking=True)
    
    note = fields.Text(
        string='Ghi chú',
        help='Ghi chú của nhân viên'
    )

    # ===== COMPUTED FIELDS =====
    display_name = fields.Char(
        string='Tên hiển thị',
        compute='_compute_display_name',
        store=True
    )
    
    shift_time_display = fields.Char(
        string='Thời gian ca',
        compute='_compute_shift_time_display',
        store=True
    )

    @api.depends('employee_id', 'shift_id', 'date')
    def _compute_display_name(self):
        for record in self:
            if record.employee_id and record.shift_id and record.date:
                record.display_name = f"{record.employee_id.name} - {record.shift_id.name} ({record.date})"
            else:
                record.display_name = "Đăng ký mới"

    @api.depends('shift_id', 'shift_id.time_start', 'shift_id.time_end')
    def _compute_shift_time_display(self):
        for record in self:
            if record.shift_id:
                record.shift_time_display = record.shift_id.get_time_display()
            else:
                record.shift_time_display = ""

    # ===== CONSTRAINTS =====
    @api.constrains('employee_id', 'shift_id', 'date')
    def _check_duplicate_registration(self):
        """Không cho phép đăng ký trùng: cùng người, cùng ca, cùng ngày"""
        for record in self:
            existing = self.search([
                ('id', '!=', record.id),
                ('employee_id', '=', record.employee_id.id),
                ('shift_id', '=', record.shift_id.id),
                ('date', '=', record.date),
            ], limit=1)
            if existing:
                raise ValidationError(
                    f"Nhân viên {record.employee_id.name} đã đăng ký "
                    f"ca {record.shift_id.name} vào ngày {record.date}!"
                )

    # ===== ACTIONS =====
    def action_confirm(self):
        """Duyệt đăng ký"""
        for record in self:
            record.state = 'confirmed'

    def action_reject(self):
        """Từ chối đăng ký"""
        for record in self:
            record.state = 'rejected'

    def action_reset_draft(self):
        """Đặt lại về nháp"""
        for record in self:
            record.state = 'draft'
