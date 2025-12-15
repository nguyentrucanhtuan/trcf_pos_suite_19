# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError
import json


class TrcfShiftTaskTemplate(models.Model):
    _name = 'trcf.shift.task.template'
    _description = 'Mẫu công việc ca làm việc'
    _order = 'sequence, name'

    # ===== THÔNG TIN CƠ BẢN =====
    name = fields.Char(
        string='Tên công việc',
        required=True,
        help='VD: Dọn vệ sinh, Kiểm kê tồn kho'
    )
    
    description = fields.Text(
        string='Mô tả công việc',
        help='Mô tả chi tiết các bước cần thực hiện'
    )
    
    sequence = fields.Integer(
        string='Thứ tự',
        default=10
    )

    # ===== CHU KỲ ÁP DỤNG =====
    frequency = fields.Selection([
        ('daily', 'Hàng ngày'),
        ('weekly', 'Thứ trong tuần'),
        ('monthly', 'Ngày trong tháng'),
    ], string='Chu kỳ', default='daily', required=True)
    
    # Nếu weekly: chọn các thứ (lưu JSON: ["0","2","4"] = T2,T4,T6)
    weekdays = fields.Char(
        string='Các thứ trong tuần',
        help='JSON array. 0=T2, 1=T3, 2=T4, 3=T5, 4=T6, 5=T7, 6=CN'
    )
    
    # UI helper fields cho weekdays
    weekday_mon = fields.Boolean('Thứ 2', default=False)
    weekday_tue = fields.Boolean('Thứ 3', default=False)
    weekday_wed = fields.Boolean('Thứ 4', default=False)
    weekday_thu = fields.Boolean('Thứ 5', default=False)
    weekday_fri = fields.Boolean('Thứ 6', default=False)
    weekday_sat = fields.Boolean('Thứ 7', default=False)
    weekday_sun = fields.Boolean('Chủ nhật', default=False)
    
    # Nếu monthly: ngày cụ thể
    day_of_month = fields.Integer(
        string='Ngày trong tháng',
        default=1,
        help='Chọn ngày 1-31'
    )

    # ===== THỜI ĐIỂM HOÀN THÀNH =====
    time_start = fields.Float(
        string='Từ giờ',
        default=8.0,
        help='VD: 15.0 = 15:00'
    )
    
    time_end = fields.Float(
        string='Đến giờ',
        default=9.0,
        help='VD: 15.5 = 15:30'
    )

    # ===== CÁCH GIAO VIỆC =====
    assignment_type = fields.Selection([
        ('specific', 'Chỉ định nhân viên cụ thể'),
        ('position', 'Theo chức vụ'),
        ('rotation', 'Luân phiên trong ca'),
    ], string='Cách giao', default='rotation', required=True)
    
    # Nếu specific: chọn nhân viên
    assigned_employee_ids = fields.Many2many(
        'hr.employee',
        'trcf_task_template_employee_rel',
        'template_id',
        'employee_id',
        string='Nhân viên chỉ định'
    )
    
    # Nếu position: chọn chức vụ
    assigned_job_ids = fields.Many2many(
        'hr.job',
        'trcf_task_template_job_rel',
        'template_id',
        'job_id',
        string='Chức vụ'
    )

    # ===== TRẠNG THÁI =====
    active = fields.Boolean(
        string='Kích hoạt',
        default=True
    )

    # ===== COMPUTED FIELDS =====
    time_display = fields.Char(
        string='Khung giờ',
        compute='_compute_time_display',
        store=True
    )

    @api.depends('time_start', 'time_end')
    def _compute_time_display(self):
        for record in self:
            start_h = int(record.time_start)
            start_m = int((record.time_start - start_h) * 60)
            end_h = int(record.time_end)
            end_m = int((record.time_end - end_h) * 60)
            record.time_display = f"{start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"

    # ===== ONCHANGE =====
    @api.onchange('weekday_mon', 'weekday_tue', 'weekday_wed', 'weekday_thu', 
                  'weekday_fri', 'weekday_sat', 'weekday_sun')
    def _onchange_weekdays(self):
        """Cập nhật weekdays JSON từ các checkbox"""
        weekdays = []
        if self.weekday_mon: weekdays.append('0')
        if self.weekday_tue: weekdays.append('1')
        if self.weekday_wed: weekdays.append('2')
        if self.weekday_thu: weekdays.append('3')
        if self.weekday_fri: weekdays.append('4')
        if self.weekday_sat: weekdays.append('5')
        if self.weekday_sun: weekdays.append('6')
        self.weekdays = json.dumps(weekdays)

    # ===== CONSTRAINTS =====
    @api.constrains('time_start', 'time_end')
    def _check_time_validity(self):
        for record in self:
            if record.time_start >= record.time_end:
                raise ValidationError('Giờ bắt đầu phải nhỏ hơn giờ kết thúc!')

    @api.constrains('day_of_month')
    def _check_day_of_month(self):
        for record in self:
            if record.frequency == 'monthly':
                if record.day_of_month < 1 or record.day_of_month > 31:
                    raise ValidationError('Ngày trong tháng phải từ 1-31!')

    # ===== ACTIONS =====
    def action_create_task_today(self):
        """Tạo task cho ngày hôm nay (manual trigger)"""
        self.ensure_one()
        today = fields.Date.today()
        return self._create_task_instance(today)

    def _create_task_instance(self, date):
        """Tạo task instance cho ngày cụ thể"""
        self.ensure_one()
        
        # Kiểm tra đã có task chưa
        existing = self.env['trcf.shift.task'].search([
            ('template_id', '=', self.id),
            ('date', '=', date),
        ], limit=1)
        
        if existing:
            return existing
        
        # Xác định nhân viên
        employee = self._get_assigned_employee(date)
        
        # Tạo task
        task = self.env['trcf.shift.task'].create({
            'template_id': self.id,
            'name': self.name,
            'description': self.description,
            'date': date,
            'time_start': self.time_start,
            'time_end': self.time_end,
            'assigned_employee_id': employee.id if employee else False,
            'state': 'pending',
        })
        
        return task

    def _get_assigned_employee(self, date):
        """Lấy nhân viên được gán theo cách giao việc"""
        self.ensure_one()
        
        if self.assignment_type == 'specific':
            # Lấy nhân viên đầu tiên trong danh sách chỉ định
            return self.assigned_employee_ids[:1]
        
        elif self.assignment_type == 'position':
            # Lấy nhân viên có chức vụ + đã confirmed trong ca ngày đó
            employees = self.env['hr.employee'].search([
                ('job_id', 'in', self.assigned_job_ids.ids),
                ('active', '=', True),
            ])
            # Lọc chỉ những người confirmed trong ca
            registrations = self.env['trcf.shift.registration'].search([
                ('date', '=', date),
                ('state', '=', 'confirmed'),
                ('employee_id', 'in', employees.ids),
            ])
            return registrations[:1].employee_id if registrations else False
        
        elif self.assignment_type == 'rotation':
            return self._get_rotation_employee(date)
        
        return False

    def _get_rotation_employee(self, date):
        """Lấy nhân viên tiếp theo theo cơ chế luân phiên"""
        self.ensure_one()
        
        # 1. Lấy nhân viên đã confirmed trong ca ngày đó
        registrations = self.env['trcf.shift.registration'].search([
            ('date', '=', date),
            ('state', '=', 'confirmed'),
        ])
        employees = registrations.mapped('employee_id')
        
        if not employees:
            return False
        
        # 2. Sắp xếp theo tên (A-Z)
        employees = employees.sorted(key=lambda e: e.name)
        
        # 3. Tìm ai làm task này lần cuối
        last_task = self.env['trcf.shift.task'].search([
            ('template_id', '=', self.id),
            ('assigned_employee_id', 'in', employees.ids),
            ('state', '!=', 'cancelled'),
        ], order='date desc, id desc', limit=1)
        
        # 4. Chọn người tiếp theo
        if last_task and last_task.assigned_employee_id in employees:
            employee_list = list(employees)
            last_index = employee_list.index(last_task.assigned_employee_id)
            next_index = (last_index + 1) % len(employees)
        else:
            next_index = 0
        
        return employees[next_index]

    # ===== TẠO TASK THEO TUẦN =====
    @api.model
    def action_generate_week_tasks(self, start_date=None):
        """Tạo tasks cho cả tuần (gọi từ wizard hoặc button)"""
        from datetime import timedelta
        
        if not start_date:
            # Mặc định: tuần tiếp theo (bắt đầu từ T2)
            today = fields.Date.today()
            days_until_next_monday = (7 - today.weekday()) % 7
            if days_until_next_monday == 0:
                days_until_next_monday = 7
            start_date = today + timedelta(days=days_until_next_monday)
        
        templates = self.search([('active', '=', True)])
        created_tasks = self.env['trcf.shift.task']
        
        for i in range(7):  # T2 -> CN
            current_date = start_date + timedelta(days=i)
            weekday = str(current_date.weekday())  # 0=T2, 6=CN
            day = current_date.day
            
            for template in templates:
                should_create = False
                
                if template.frequency == 'daily':
                    should_create = True
                elif template.frequency == 'weekly':
                    weekdays = json.loads(template.weekdays or '[]')
                    should_create = weekday in weekdays
                elif template.frequency == 'monthly':
                    should_create = day == template.day_of_month
                
                if should_create:
                    task = template._create_task_instance(current_date)
                    if task:
                        created_tasks |= task
        
        return created_tasks

    # ===== CRON JOB - Chủ nhật 23:00 =====
    @api.model
    def _cron_generate_weekly_tasks(self):
        """Chạy Chủ nhật tối để tạo tasks cho tuần tiếp theo"""
        from datetime import timedelta
        
        today = fields.Date.today()
        
        # Tính ngày T2 tuần tới
        days_until_next_monday = (7 - today.weekday()) % 7
        if days_until_next_monday == 0:
            days_until_next_monday = 7
        next_monday = today + timedelta(days=days_until_next_monday)
        
        # Kiểm tra đã tạo chưa
        existing = self.env['trcf.shift.task'].search([
            ('date', '>=', next_monday),
            ('date', '<=', next_monday + timedelta(days=6)),
        ], limit=1)
        
        if not existing:
            self.action_generate_week_tasks(next_monday)

