from odoo import models, fields, api
from odoo.models import Index


class TrcfHrAttendance(models.Model):
    _inherit = 'hr.attendance'

    def action_recompute_shift_registration(self):
        """Force recompute shift registration for selected records"""
        self._compute_shift_registration()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Hoàn tất',
                'message': f'Đã liên kết ca cho {len(self)} bản ghi chấm công',
                'type': 'success',
                'sticky': False,
            }
        }

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
    
    # ===== DISPLAY COLUMNS (2 cột gọn) =====
    check_in_status = fields.Char(
        string='Đi',
        compute='_compute_attendance_analysis',
        store=True,
        help='Trạng thái đi làm: Sớm/Trễ/Đúng giờ'
    )
    
    check_out_status = fields.Char(
        string='Về',
        compute='_compute_attendance_analysis',
        store=True,
        help='Trạng thái tan ca: Sớm/Trễ/Đúng giờ'
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

    # ===== GEO ATTENDANCE FIELDS =====
    attendance_source = fields.Selection(
        selection=[
            ('zkteco', 'ZKTeco'),
            ('geo', 'Geolocation (Web)'),
            ('manual', 'Thủ công'),
        ],
        string='Nguồn chấm công',
        default='zkteco',
        index=True,
        help='Nguồn gốc của bản ghi chấm công'
    )

    geo_location_id = fields.Many2one(
        'trcf.geo.location',
        string='Cơ sở check-in',
        ondelete='set null',
        help='Cơ sở gần nhất khớp GPS tại thời điểm check-in'
    )

    geo_check_in_lat = fields.Float(
        string='Latitude Check-in',
        digits=(10, 7),
        help='Vĩ độ GPS tại thời điểm check-in'
    )

    geo_check_in_lon = fields.Float(
        string='Longitude Check-in',
        digits=(10, 7),
        help='Kinh độ GPS tại thời điểm check-in'
    )

    geo_check_in_accuracy = fields.Float(
        string='GPS Accuracy Check-in (m)',
        help='Độ chính xác GPS lúc check-in (mét). < 5m có thể là giả mạo.'
    )

    geo_check_out_lat = fields.Float(
        string='Latitude Check-out',
        digits=(10, 7),
        help='Vĩ độ GPS tại thời điểm check-out'
    )

    geo_check_out_lon = fields.Float(
        string='Longitude Check-out',
        digits=(10, 7),
        help='Kinh độ GPS tại thời điểm check-out'
    )

    geo_check_out_accuracy = fields.Float(
        string='GPS Accuracy Check-out (m)',
        help='Độ chính xác GPS lúc check-out (mét)'
    )

    geo_suspicious = fields.Boolean(
        string='Nghi ngờ GPS?',
        default=False,
        index=True,
        help='True nếu phát hiện dấu hiệu bất thường: accuracy < 5m hoặc velocity > 500km/h'
    )

    geo_suspicious_reason = fields.Char(
        string='Lý do nghi ngờ GPS',
        help='Chi tiết lý do flag: low_accuracy, impossible_velocity hoặc kết hợp'
    )

    request_ip = fields.Char(
        string='IP Check-in/out',
        help='Public IP của thiết bị tại thời điểm check-in/check-out (do server đọc)'
    )

    ip_suspicious = fields.Boolean(
        string='IP đáng ngờ?',
        default=False,
        index=True,
        help='True nếu IP không thuộc danh sách allowed_ips của cơ sở (chế độ cảnh báo)'
    )

    # ===== COMPUTE METHODS =====
    @api.depends('employee_id', 'check_in')
    def _compute_shift_registration(self):
        """Tự động tìm ca đã đăng ký dựa trên giờ check-in"""
        for record in self:
            if not record.employee_id or not record.check_in:
                record.shift_registration_id = False
                continue
            
            # Chuyển đổi check_in sang múi giờ địa phương
            local_check_in = fields.Datetime.context_timestamp(record, record.check_in)
            date = local_check_in.date()
            check_in_hour = local_check_in.hour + local_check_in.minute / 60.0
            
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
            
            # Chỉ match nếu khoảng cách < 3 giờ
            if best_match and min_distance <= 3.0:
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
            record.check_in_status = ''
            record.check_out_status = ''
            
            if not record.shift_id or not record.check_in:
                continue
            
            # Chuyển đổi check_in/check_out sang múi giờ địa phương
            local_check_in = fields.Datetime.context_timestamp(record, record.check_in)
            check_in_hour = local_check_in.hour + local_check_in.minute / 60.0
            
            # Tính đi trễ / đi sớm (ngưỡng 10 phút)
            TOLERANCE = 10 / 60.0  # 10 phút = 0.1667 giờ
            diff_in = check_in_hour - record.shift_start_time
            if diff_in > TOLERANCE:  # Trễ hơn 10 phút
                record.late_minutes = int(diff_in * 60)
                record.is_late = True
                record.check_in_status = f"Trễ {record.late_minutes}p"
            elif diff_in < -TOLERANCE:  # Sớm hơn 10 phút
                early_minutes = int(abs(diff_in) * 60)
                record.check_in_status = f"Sớm {early_minutes}p"
            else:
                record.check_in_status = "Đúng giờ"
            
            # Tính về sớm / về trễ (làm thêm)
            if record.check_out:
                local_check_out = fields.Datetime.context_timestamp(record, record.check_out)
                check_out_hour = local_check_out.hour + local_check_out.minute / 60.0
                
                diff_out = check_out_hour - record.shift_end_time
                if diff_out < -TOLERANCE:  # Về sớm hơn 10 phút
                    record.early_leave_minutes = int(abs(diff_out) * 60)
                    record.check_out_status = f"Sớm {record.early_leave_minutes}p"
                elif diff_out > TOLERANCE:  # Về trễ hơn 10 phút (làm thêm)
                    record.overtime_minutes = int(diff_out * 60)
                    record.is_overtime = True
                    record.check_out_status = f"Trễ {record.overtime_minutes}p"
                else:
                    record.check_out_status = "Đúng giờ"

    @api.depends('worked_hours', 'employee_id.trcf_hourly_salary')
    def _compute_hourly_salary_sum(self):
        """Tính tiền lương = lương theo giờ * số giờ làm việc"""
        for record in self:
            if record.worked_hours and record.employee_id.trcf_hourly_salary:
                record.trcf_hourly_salary_sum = record.worked_hours * record.employee_id.trcf_hourly_salary
            else:
                record.trcf_hourly_salary_sum = 0.0