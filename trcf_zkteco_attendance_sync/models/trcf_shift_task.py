# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TrcfShiftTask(models.Model):
    _name = 'trcf.shift.task'
    _description = 'Công việc ca làm việc'
    _order = 'date desc, time_start'
    _rec_name = 'display_name'

    # ===== THÔNG TIN CƠ BẢN =====
    template_id = fields.Many2one(
        'trcf.shift.task.template',
        string='Mẫu công việc',
        ondelete='set null'
    )
    
    name = fields.Char(
        string='Tên công việc',
        required=True
    )
    
    description = fields.Text(
        string='Mô tả công việc'
    )
    
    date = fields.Date(
        string='Ngày',
        required=True,
        default=fields.Date.today
    )
    
    time_start = fields.Float(
        string='Từ giờ',
        default=8.0
    )
    
    time_end = fields.Float(
        string='Đến giờ',
        default=9.0
    )

    # ===== PHÂN CÔNG =====
    assigned_employee_id = fields.Many2one(
        'hr.employee',
        string='Nhân viên phụ trách'
    )

    # ===== TRẠNG THÁI =====
    state = fields.Selection([
        ('pending', 'Chờ thực hiện'),
        ('in_progress', 'Đang thực hiện'),
        ('done', 'Hoàn thành'),
        ('overdue', 'Quá hạn'),
        ('cancelled', 'Đã hủy'),
    ], string='Trạng thái', default='pending')
    
    completed_at = fields.Datetime(
        string='Thời điểm hoàn thành'
    )
    
    completed_by = fields.Many2one(
        'hr.employee',
        string='Người hoàn thành'
    )
    
    note = fields.Text(
        string='Ghi chú hoàn thành'
    )

    # ===== COMPUTED FIELDS =====
    display_name = fields.Char(
        string='Tên hiển thị',
        compute='_compute_display_name',
        store=True
    )
    
    time_display = fields.Char(
        string='Khung giờ',
        compute='_compute_time_display',
        store=True
    )
    
    is_overdue = fields.Boolean(
        string='Quá hạn',
        compute='_compute_is_overdue'
    )

    @api.depends('name', 'date', 'assigned_employee_id')
    def _compute_display_name(self):
        for record in self:
            emp_name = record.assigned_employee_id.name if record.assigned_employee_id else "Chưa gán"
            record.display_name = f"{record.name} - {record.date} ({emp_name})"

    @api.depends('time_start', 'time_end')
    def _compute_time_display(self):
        for record in self:
            start_h = int(record.time_start)
            start_m = int((record.time_start - start_h) * 60)
            end_h = int(record.time_end)
            end_m = int((record.time_end - end_h) * 60)
            record.time_display = f"{start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"

    def _compute_is_overdue(self):
        """Kiểm tra task có quá hạn không"""
        now = fields.Datetime.now()
        today = fields.Date.today()
        current_hour = now.hour + now.minute / 60.0
        
        for record in self:
            if record.state in ('done', 'cancelled'):
                record.is_overdue = False
            elif record.date < today:
                record.is_overdue = True
            elif record.date == today and current_hour > record.time_end:
                record.is_overdue = True
            else:
                record.is_overdue = False

    # ===== ACTIONS =====
    def action_start(self):
        """Bắt đầu thực hiện"""
        for record in self:
            record.state = 'in_progress'

    def action_done(self):
        """Đánh dấu hoàn thành"""
        employee = self.env.user.employee_id
        for record in self:
            record.write({
                'state': 'done',
                'completed_at': fields.Datetime.now(),
                'completed_by': employee.id if employee else False,
            })

    def action_cancel(self):
        """Hủy công việc"""
        for record in self:
            record.state = 'cancelled'

    def action_reset(self):
        """Đặt lại trạng thái"""
        for record in self:
            record.write({
                'state': 'pending',
                'completed_at': False,
                'completed_by': False,
            })

    # ===== CRON JOB =====
    @api.model
    def _cron_check_overdue_tasks(self):
        """Chạy mỗi giờ để cập nhật trạng thái quá hạn"""
        overdue_tasks = self.search([
            ('state', 'in', ['pending', 'in_progress']),
            ('date', '<=', fields.Date.today()),
        ])
        
        now = fields.Datetime.now()
        current_hour = now.hour + now.minute / 60.0
        today = fields.Date.today()
        
        for task in overdue_tasks:
            if task.date < today:
                task.state = 'overdue'
            elif task.date == today and current_hour > task.time_end:
                task.state = 'overdue'
