# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class TrcfWorkShift(models.Model):
    _name = 'trcf.work.shift'
    _description = 'Ca làm việc'
    _order = 'time_start'
    _rec_name = 'name'

    # ===== BASIC FIELDS =====
    name = fields.Char(
        string='Tên ca',
        required=True,
        help='Tên ca làm việc (VD: Ca sáng, Ca chiều)'
    )
    
    time_start = fields.Float(
        string='Giờ bắt đầu',
        required=True,
        help='Giờ bắt đầu ca (VD: 7.0 = 07:00, 7.5 = 07:30)'
    )
    
    time_end = fields.Float(
        string='Giờ kết thúc',
        required=True,
        help='Giờ kết thúc ca (VD: 14.0 = 14:00)'
    )
    
    standard_hours = fields.Float(
        string='Số giờ công chuẩn',
        compute='_compute_standard_hours',
        store=True,
        help='Số giờ công chuẩn của ca (tự tính từ giờ bắt đầu và kết thúc)'
    )
    
    max_employees = fields.Integer(
        string='Số NV tối đa',
        default=5,
        help='Số nhân viên tối đa được xếp vào ca này'
    )
    
    min_employees = fields.Integer(
        string='Số NV tối thiểu',
        default=1,
        help='Số nhân viên tối thiểu cần có trong ca'
    )
    
    active = fields.Boolean(
        string='Kích hoạt',
        default=True,
        help='Bật/tắt ca làm việc này'
    )
    
    note = fields.Text(
        string='Ghi chú',
        help='Ghi chú thêm về ca làm việc'
    )

    # ===== COMPUTED FIELDS =====
    @api.depends('time_start', 'time_end')
    def _compute_standard_hours(self):
        """Tính số giờ công chuẩn = giờ kết thúc - giờ bắt đầu"""
        for record in self:
            if record.time_end and record.time_start:
                record.standard_hours = record.time_end - record.time_start
            else:
                record.standard_hours = 0.0

    # ===== CONSTRAINTS =====
    @api.constrains('time_start', 'time_end')
    def _check_time_validity(self):
        """Validation: giờ bắt đầu phải nhỏ hơn giờ kết thúc"""
        for record in self:
            if record.time_start >= record.time_end:
                raise ValidationError('Giờ bắt đầu phải nhỏ hơn giờ kết thúc!')
            if record.time_start < 0 or record.time_start > 24:
                raise ValidationError('Giờ bắt đầu không hợp lệ (phải từ 0 đến 24)!')
            if record.time_end < 0 or record.time_end > 24:
                raise ValidationError('Giờ kết thúc không hợp lệ (phải từ 0 đến 24)!')

    @api.constrains('min_employees', 'max_employees')
    def _check_employee_limits(self):
        """Validation: số NV tối thiểu không được lớn hơn tối đa"""
        for record in self:
            if record.min_employees > record.max_employees:
                raise ValidationError('Số NV tối thiểu không được lớn hơn số NV tối đa!')
            if record.min_employees < 0 or record.max_employees < 0:
                raise ValidationError('Số nhân viên không được âm!')

    # ===== HELPER METHODS =====
    def get_time_display(self):
        """Trả về chuỗi hiển thị thời gian dạng HH:MM - HH:MM"""
        self.ensure_one()
        start_hours = int(self.time_start)
        start_minutes = int((self.time_start - start_hours) * 60)
        end_hours = int(self.time_end)
        end_minutes = int((self.time_end - end_hours) * 60)
        return f"{start_hours:02d}:{start_minutes:02d} - {end_hours:02d}:{end_minutes:02d}"
