from odoo import models, fields, api


class TrcfHrAttendance(models.Model):
    _inherit = 'hr.attendance'

    # ===== SHIFT REGISTRATION LINK =====
    shift_registration_id = fields.Many2one(
        'trcf.shift.registration',
        string='Ca đã đăng ký',
        compute='_compute_shift_registration',
        store=True,
        help='Ca làm việc đã đăng ký cho ngày này'
    )
    
    shift_id = fields.Many2one(
        'trcf.work.shift',
        related='shift_registration_id.shift_id',
        string='Ca làm việc',
        store=True
    )
    
    shift_name = fields.Char(
        related='shift_id.name',
        string='Tên ca',
        store=True
    )
    
    shift_start_time = fields.Float(
        related='shift_id.time_start',
        string='Giờ vào ca',
        store=True
    )
    
    shift_end_time = fields.Float(
        related='shift_id.time_end',
        string='Giờ tan ca',
        store=True
    )
    
    shift_time_display = fields.Char(
        string='Thời gian ca',
        compute='_compute_shift_time_display',
        store=True
    )

    # ===== ATTENDANCE ANALYSIS =====
    late_minutes = fields.Integer(
        string='Đi trễ (phút)',
        compute='_compute_attendance_analysis',
        store=True,
        help='Số phút đi trễ so với giờ vào ca'
    )
    
    early_leave_minutes = fields.Integer(
        string='Về sớm (phút)',
        compute='_compute_attendance_analysis',
        store=True,
        help='Số phút về sớm so với giờ tan ca'
    )
    
    overtime_minutes = fields.Integer(
        string='Làm thêm (phút)',
        compute='_compute_attendance_analysis',
        store=True,
        help='Số phút làm thêm sau giờ tan ca'
    )
    
    is_late = fields.Boolean(
        string='Đi trễ?',
        compute='_compute_attendance_analysis',
        store=True
    )
    
    is_overtime = fields.Boolean(
        string='Làm thêm?',
        compute='_compute_attendance_analysis',
        store=True
    )

    # ===== SALARY FIELDS (existing) =====
    trcf_hourly_salary_display = fields.Float(
        string='Tiền lương/giờ',
        related='employee_id.trcf_hourly_salary',
        digits='Product Price',
        help='Mức lương theo giờ của nhân viên',
        readonly=True,
        aggregator='max'
    )
    
    trcf_hourly_salary_sum = fields.Float(
        string='Tiền lương',
        digits='Product Price',
        help='Tiền lương cho phiên làm việc này',
        default=0.0,
        compute='_compute_hourly_salary_sum',
        store=True
    )

    # ===== COMPUTE METHODS =====
    @api.depends('employee_id', 'check_in')
    def _compute_shift_registration(self):
        """Tự động tìm ca đã đăng ký dựa trên giờ check-in"""
        for record in self:
            if not record.employee_id or not record.check_in:
                record.shift_registration_id = False
                continue
            
            # Lấy ngày và giờ từ check_in
            date = record.check_in.date()
            check_in_hour = record.check_in.hour + record.check_in.minute / 60.0
            
            # Tìm tất cả shift registration đã confirmed trong ngày
            registrations = self.env['trcf.shift.registration'].search([
                ('employee_id', '=', record.employee_id.id),
                ('date', '=', date),
                ('state', '=', 'confirmed')
            ])
            
            if not registrations:
                record.shift_registration_id = False
                continue
            
            # Tìm ca có giờ bắt đầu gần nhất với giờ check-in
            # Logic: chọn ca có khoảng cách thời gian nhỏ nhất
            best_match = None
            min_distance = float('inf')
            
            for reg in registrations:
                if reg.shift_id:
                    # Tính khoảng cách giữa giờ check-in và giờ bắt đầu ca
                    distance = abs(check_in_hour - reg.shift_id.time_start)
                    
                    # Ưu tiên ca có giờ check-in sau giờ bắt đầu (đúng hơn)
                    # Nếu check-in trước giờ ca → penalty nhẹ
                    if check_in_hour < reg.shift_id.time_start:
                        distance += 0.5  # Penalty 30 phút
                    
                    if distance < min_distance:
                        min_distance = distance
                        best_match = reg
            
            # Chỉ match nếu khoảng cách < 2 giờ
            if best_match and min_distance <= 2.0:
                record.shift_registration_id = best_match.id
            else:
                record.shift_registration_id = False

    
    @api.depends('shift_start_time', 'shift_end_time')
    def _compute_shift_time_display(self):
        """Hiển thị thời gian ca dạng HH:MM - HH:MM"""
        for record in self:
            if record.shift_start_time is not False and record.shift_end_time is not False:
                start_h = int(record.shift_start_time)
                start_m = int((record.shift_start_time - start_h) * 60)
                end_h = int(record.shift_end_time)
                end_m = int((record.shift_end_time - end_h) * 60)
                record.shift_time_display = f"{start_h:02d}:{start_m:02d} - {end_h:02d}:{end_m:02d}"
            else:
                record.shift_time_display = "Không đăng ký"

    @api.depends('check_in', 'check_out', 'shift_start_time', 'shift_end_time')
    def _compute_attendance_analysis(self):
        """Phân tích: đi trễ, về sớm, làm thêm"""
        for record in self:
            # Reset values
            record.late_minutes = 0
            record.early_leave_minutes = 0
            record.overtime_minutes = 0
            record.is_late = False
            record.is_overtime = False
            
            if not record.shift_id or not record.check_in:
                continue
            
            # Convert check_in to float hours (local time)
            check_in_hour = record.check_in.hour + record.check_in.minute / 60.0
            
            # Tính đi trễ
            if check_in_hour > record.shift_start_time:
                record.late_minutes = int((check_in_hour - record.shift_start_time) * 60)
                record.is_late = True
            
            # Tính về sớm / làm thêm
            if record.check_out:
                check_out_hour = record.check_out.hour + record.check_out.minute / 60.0
                
                if check_out_hour < record.shift_end_time:
                    # Về sớm
                    record.early_leave_minutes = int((record.shift_end_time - check_out_hour) * 60)
                elif check_out_hour > record.shift_end_time:
                    # Làm thêm
                    record.overtime_minutes = int((check_out_hour - record.shift_end_time) * 60)
                    record.is_overtime = True

    @api.depends('worked_hours', 'employee_id.trcf_hourly_salary')
    def _compute_hourly_salary_sum(self):
        """Tính tiền lương = lương theo giờ * số giờ làm việc"""
        for record in self:
            if record.worked_hours and record.employee_id.trcf_hourly_salary:
                record.trcf_hourly_salary_sum = record.worked_hours * record.employee_id.trcf_hourly_salary
            else:
                record.trcf_hourly_salary_sum = 0.0