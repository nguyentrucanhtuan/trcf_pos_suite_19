# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from datetime import datetime, timedelta
import calendar
import json


class TrcfShiftRegistrationController(http.Controller):
    
    @http.route('/dang-ky-ca', type='http', auth='user', website=True)
    def shift_registration_page(self, **kwargs):
        """Trang đăng ký ca làm việc cho nhân viên"""
        
        # Lấy nhân viên hiện tại
        employee = request.env.user.employee_id
        if not employee:
            return request.render('trcf_zkteco_attendance_sync.shift_registration_no_employee')
        
        # Lấy danh sách ca làm việc active
        shifts = request.env['trcf.work.shift'].sudo().search([
            ('active', '=', True)
        ], order='time_start')
        
        # Tính ngày thứ 2 tuần kế tiếp
        today = datetime.now().date()
        # weekday(): 0=Monday, 1=Tuesday, ..., 6=Sunday
        days_until_next_monday = (7 - today.weekday()) % 7
        if days_until_next_monday == 0:  # Nếu hôm nay là thứ 2
            days_until_next_monday = 7  # Lấy thứ 2 tuần sau
        
        start_date = today + timedelta(days=days_until_next_monday)
        
        # Tạo danh sách 14 ngày kể từ thứ 2 tuần kế tiếp
        dates = []
        for i in range(14):
            current_date = start_date + timedelta(days=i)
            dates.append({
                'date': current_date,
                'date_str': current_date.strftime('%Y-%m-%d'),
                'display': current_date.strftime('%d/%m'),
                'weekday': self._get_weekday_name(current_date.weekday()),
                'is_weekend': current_date.weekday() >= 5,
            })
        
        # Lấy các đăng ký hiện tại của nhân viên trong khoảng thời gian hiển thị
        end_date = start_date + timedelta(days=13)
        registrations = request.env['trcf.shift.registration'].sudo().search([
            ('employee_id', '=', employee.id),
            ('date', '>=', start_date),
            ('date', '<=', end_date),
        ])
        
        # Tạo dict các đăng ký đã có với state (date_shift_id: state)
        registered_dict = {}
        for reg in registrations:
            key = f"{reg.date.strftime('%Y-%m-%d')}_{reg.shift_id.id}"
            registered_dict[key] = reg.state
        
        return request.render('trcf_zkteco_attendance_sync.shift_registration_form', {
            'employee': employee,
            'shifts': shifts,
            'dates': dates,
            'registered_dict': registered_dict,
        })
    
    @http.route('/dang-ky-ca/save', type='jsonrpc', auth='user', methods=['POST'])
    def save_shift_registration(self, **kwargs):
        """API lưu đăng ký ca"""
        try:
            employee = request.env.user.employee_id
            if not employee:
                return {'success': False, 'message': 'Không tìm thấy thông tin nhân viên'}
            
            selections = kwargs.get('selections', [])
            
            if not selections:
                return {'success': False, 'message': 'Vui lòng chọn ít nhất một ca'}
            
            created_count = 0
            for sel in selections:
                date_str = sel.get('date')
                shift_id = sel.get('shift_id')
                
                # Kiểm tra đã đăng ký chưa
                existing = request.env['trcf.shift.registration'].sudo().search([
                    ('employee_id', '=', employee.id),
                    ('shift_id', '=', int(shift_id)),
                    ('date', '=', date_str),
                ], limit=1)
                
                if not existing:
                    request.env['trcf.shift.registration'].sudo().create({
                        'employee_id': employee.id,
                        'shift_id': int(shift_id),
                        'date': date_str,
                        'state': 'draft',
                    })
                    created_count += 1
            
            return {
                'success': True, 
                'message': f'Đã đăng ký thành công {created_count} ca!',
                'created_count': created_count
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @http.route('/dang-ky-ca/remove', type='jsonrpc', auth='user', methods=['POST'])
    def remove_shift_registration(self, **kwargs):
        """API hủy đăng ký ca"""
        try:
            employee = request.env.user.employee_id
            if not employee:
                return {'success': False, 'message': 'Không tìm thấy thông tin nhân viên'}
            
            date_str = kwargs.get('date')
            shift_id = kwargs.get('shift_id')
            
            # Tìm và xóa đăng ký
            registration = request.env['trcf.shift.registration'].sudo().search([
                ('employee_id', '=', employee.id),
                ('shift_id', '=', int(shift_id)),
                ('date', '=', date_str),
                ('state', '=', 'draft'),  # Chỉ xóa được đăng ký nháp
            ], limit=1)
            
            if registration:
                registration.unlink()
                return {'success': True, 'message': 'Đã hủy đăng ký!'}
            else:
                return {'success': False, 'message': 'Không tìm thấy đăng ký hoặc đăng ký đã được duyệt'}
                
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @http.route('/dang-ky-ca/gio-cong', type='json', auth='user', methods=['POST'])
    def get_attendance_data(self, month=None, year=None, **kwargs):
        """Trả về dữ liệu giờ công tháng của nhân viên đang đăng nhập.

        Args:
            month (int, optional): Tháng cần xem (1-12). Mặc định: tháng hiện tại.
            year (int, optional):  Năm cần xem. Mặc định: năm hiện tại.

        Returns:
            dict: {success, month, year, records[], total_salary_display, is_provisional}
        """
        employee = request.env.user.employee_id
        if not employee:
            return {'success': False, 'message': 'Không tìm thấy thông tin nhân viên'}

        today = datetime.now()
        month = int(month) if month else today.month
        year = int(year) if year else today.year

        # Tính khoảng thời gian đầu/cuối tháng
        first_day = datetime(year, month, 1)
        last_day_num = calendar.monthrange(year, month)[1]
        next_month_first = datetime(year, month, last_day_num) + timedelta(days=1)

        # Query với domain chặt chẽ — không dùng sudo() để enforce security
        attendances = request.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', first_day),
            ('check_in', '<', next_month_first),
        ], order='check_in asc')

        records = []
        total_salary = 0.0
        for att in attendances:
            # Chuyển sang giờ địa phương
            local_in = fields.Datetime.context_timestamp(att, att.check_in)
            local_out = (
                fields.Datetime.context_timestamp(att, att.check_out)
                if att.check_out else None
            )

            worked = att.worked_hours or 0.0
            h = int(worked)
            m = int(round((worked - h) * 60))
            worked_display = f'{h}h{m:02d}m' if worked else '–'

            salary = att.trcf_hourly_salary_sum or 0.0
            total_salary += salary

            records.append({
                'date': local_in.strftime('%d/%m/%Y'),
                'check_in': local_in.strftime('%H:%M'),
                'check_out': local_out.strftime('%H:%M') if local_out else '',
                'worked_hours_display': worked_display,
                'check_in_status': att.check_in_status or '–',
                'check_out_status': att.check_out_status or '–',
                'salary_display': '{:,.0f}'.format(salary).replace(',', '.'),
            })

        return {
            'success': True,
            'month': month,
            'year': year,
            'records': records,
            'total_salary_display': '{:,.0f}'.format(total_salary).replace(',', '.'),
            'is_provisional': True,
        }

    def _get_weekday_name(self, weekday):
        """Trả về tên thứ trong tuần"""
        weekdays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
        return weekdays[weekday]
