# -*- coding: utf-8 -*-
from odoo import http, fields
from odoo.http import request
from odoo.exceptions import UserError
from odoo.tools.translate import _
from datetime import datetime, timedelta
from markupsafe import Markup
import calendar
import json
import math

from ..i18n import get_translator


class TrcfShiftRegistrationController(http.Controller):
    
    @http.route('/dang-ky-ca', type='http', auth='user', website=True)
    def shift_registration_page(self, **kwargs):
        """Trang đăng ký ca làm việc cho nhân viên"""
        t = get_translator(request)

        # Lấy nhân viên hiện tại
        employee = request.env.user.employee_id
        if not employee:
            return request.render('trcf_fnb_staff.shift_registration_no_employee', {'t': t})
        
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
                'weekday': self._get_weekday_name(current_date.weekday(), t),
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
        
        # === GEO ATTENDANCE: Lấy danh sách cơ sở active cho tab Chấm Công ===
        geo_locations_qs = request.env['trcf.geo.location'].sudo().search([
            ('active', '=', True),
            ('company_id', 'in', [request.env.company.id, False]),
        ])
        # Markup(): t-out HTML-escapes plain strings, which corrupts JSON
        # embedded in a <script> tag (entities aren't decoded there) --
        # mark this pre-serialized JSON as already-safe raw output.
        geo_locations_json = Markup(json.dumps([{
            'id': loc.id,
            'name': loc.name,
            'lat': loc.latitude,
            'lon': loc.longitude,
            'radius': loc.radius,
        } for loc in geo_locations_qs]))

        # === GEO ATTENDANCE: Trạng thái check-in hôm nay ===
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        open_attendance = request.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', fields.Datetime.to_string(today_start)),
            ('check_in', '<', fields.Datetime.to_string(today_end)),
            ('check_out', '=', False),
        ], limit=1)
        done_attendance = request.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', fields.Datetime.to_string(today_start)),
            ('check_in', '<', fields.Datetime.to_string(today_end)),
            ('check_out', '!=', False),
            ('attendance_source', '=', 'geo'),
        ], order='check_out desc', limit=1)

        if open_attendance:
            local_in = fields.Datetime.context_timestamp(open_attendance, open_attendance.check_in)
            current_attendance = {
                'status': 'checked_in',
                'attendance_id': open_attendance.id,
                'check_in_display': local_in.strftime('%H:%M'),
                'location_name': open_attendance.geo_location_id.name if open_attendance.geo_location_id else '',
            }
        elif done_attendance:
            local_in = fields.Datetime.context_timestamp(done_attendance, done_attendance.check_in)
            local_out = fields.Datetime.context_timestamp(done_attendance, done_attendance.check_out)
            wh = done_attendance.worked_hours or 0.0
            h, m = int(wh), int(round((wh - int(wh)) * 60))
            salary = done_attendance.trcf_hourly_salary_sum or 0.0
            current_attendance = {
                'status': 'done',
                'check_in_display': local_in.strftime('%H:%M'),
                'check_out_display': local_out.strftime('%H:%M'),
                'worked_hours_display': f'{h}h{m:02d}m',
                'salary_display': '{:,.0f}'.format(salary).replace(',', '.'),
            }
        else:
            current_attendance = {'status': 'idle'}

        return request.render('trcf_fnb_staff.shift_registration_form', {
            't': t,
            'employee': employee,
            'shifts': shifts,
            'dates': dates,
            'registered_dict': registered_dict,
            'geo_locations_json': geo_locations_json,
            'current_attendance': current_attendance,
            'staff_i18n_json': Markup(json.dumps(self._get_staff_i18n(t))),
        })

    
    @http.route('/dang-ky-ca/save', type='jsonrpc', auth='user', methods=['POST'])
    def save_shift_registration(self, **kwargs):
        """API lưu đăng ký ca"""
        t = get_translator(request)
        try:
            employee = request.env.user.employee_id
            if not employee:
                return {'success': False, 'message': t('Không tìm thấy thông tin nhân viên')}

            selections = kwargs.get('selections', [])

            if not selections:
                return {'success': False, 'message': t('Vui lòng chọn ít nhất một ca')}

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
                'message': t('Đã đăng ký thành công {count} ca!').format(count=created_count),
                'created_count': created_count
            }

        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @http.route('/dang-ky-ca/remove', type='jsonrpc', auth='user', methods=['POST'])
    def remove_shift_registration(self, **kwargs):
        """API hủy đăng ký ca"""
        t = get_translator(request)
        try:
            employee = request.env.user.employee_id
            if not employee:
                return {'success': False, 'message': t('Không tìm thấy thông tin nhân viên')}

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
                return {'success': True, 'message': t('Đã hủy đăng ký!')}
            else:
                return {'success': False, 'message': t('Không tìm thấy đăng ký hoặc đăng ký đã được duyệt')}

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
        t = get_translator(request)
        employee = request.env.user.employee_id
        if not employee:
            return {'success': False, 'message': t('Không tìm thấy thông tin nhân viên')}

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

            check_in_key, check_in_display = self._translate_status(att.check_in_status, t)
            check_out_key, check_out_display = self._translate_status(att.check_out_status, t)

            records.append({
                'date': local_in.strftime('%d/%m/%Y'),
                'check_in': local_in.strftime('%H:%M'),
                'check_out': local_out.strftime('%H:%M') if local_out else '',
                'worked_hours_display': worked_display,
                'check_in_status': check_in_display,
                'check_in_status_key': check_in_key,
                'check_out_status': check_out_display,
                'check_out_status_key': check_out_key,
                'salary_display': '{:,.0f}'.format(salary).replace(',', '.'),
                'attendance_source': att.attendance_source or 'zkteco',
            })


        return {
            'success': True,
            'month': month,
            'year': year,
            'records': records,
            'total_salary_display': '{:,.0f}'.format(total_salary).replace(',', '.'),
            'is_provisional': True,
        }

    def _get_weekday_name(self, weekday, t=None):
        """Trả về tên thứ trong tuần"""
        weekdays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
        name = weekdays[weekday]
        return t(name) if t else name

    def _translate_status(self, status, t):
        """Phân tích chuỗi trạng thái ('Trễ 15p' / 'Sớm 5p' / 'Đúng giờ') thành
        (status_key, display_text) -- status_key dùng để gán CSS class ở JS
        (không phụ thuộc ngôn ngữ), display_text đã được dịch để hiển thị.
        """
        if not status:
            return 'none', '–'
        if status == 'Đúng giờ':
            return 'ontime', t('Đúng giờ')
        parts = status.split(' ', 1)
        prefix, minutes = parts[0], parts[1] if len(parts) > 1 else ''
        if prefix == 'Trễ':
            return 'late', t('Trễ {mins}').format(mins=minutes)
        if prefix == 'Sớm':
            return 'early', t('Sớm {mins}').format(mins=minutes)
        return 'none', t(status)

    def _get_staff_i18n(self, t):
        """Chuỗi dịch dùng bởi geo_attendance.js (static asset, không thể
        gọi t() trực tiếp) -- được nhúng vào trang qua window.TRCF_STAFF_I18N.
        """
        return {
            'gps_valid': t('Hợp lệ ✓'),
            'gps_invalid': t('Ngoài vùng ✗'),
            'meters_from_nearest': t('mét so với cơ sở gần nhất'),
            'km_from_nearest': t('km so với cơ sở gần nhất'),
            'gps_error_default': t('Không thể xác định vị trí GPS.'),
            'gps_error_permission_denied': t('Bạn đã từ chối quyền truy cập vị trí. Vui lòng bật lại trong cài đặt trình duyệt.'),
            'gps_error_unavailable': t('Tín hiệu GPS không khả dụng. Vui lòng thử lại.'),
            'gps_error_timeout': t('Hết thời gian chờ GPS. Đang thử lại...'),
            'checkin_success': t('Check-in thành công lúc {time} tại {location}'),
            'ip_suspicious_warning': t('⚠️ Cảnh báo: Thiết bị không kết nối đúng mạng WiFi văn phòng.'),
            'checkout_success': t('Check-out thành công! Tổng giờ làm: {hours}'),
            'connection_error': t('Lỗi kết nối. Vui lòng thử lại.'),
            'error_out_of_range': t('Bạn đang ở ngoài vùng cho phép. Khoảng cách: {distance}m (bán kính: {radius}m)'),
            'error_ip_blocked': t('Thiết bị không kết nối đúng mạng WiFi văn phòng.'),
            'error_already_checked_in': t('Bạn đã check-in lúc {time}. Vui lòng check-out trước.'),
            'error_no_open_session': t('Không có phiên làm việc đang mở. Vui lòng check-in trước.'),
            'error_no_location_configured': t('Cơ sở chưa được cấu hình vị trí GPS. Vui lòng liên hệ quản trị.'),
            'error_no_employee': t('Không tìm thấy thông tin nhân viên. Vui lòng liên hệ HR.'),
            'error_default': t('Đã xảy ra lỗi. Vui lòng thử lại.'),
        }

    # ===================================================================
    # GEO ATTENDANCE ROUTES (Phase 2-3)
    # ===================================================================

    @http.route('/dang-ky-ca/geo-checkin', type='jsonrpc', auth='user', methods=['POST'])
    def geo_check_in(self, lat, lon, accuracy, **kwargs):
        """API check-in bằng GPS + IP WiFi.

        Args:
            lat (float): Vĩ độ GPS từ browser.
            lon (float): Kinh độ GPS từ browser.
            accuracy (float): Độ chính xác GPS (mét).

        Returns:
            dict: {success, attendance_id, location_name, check_in, geo_suspicious, ip_suspicious}
                  hoặc {success: False, error: str, ...}
        """
        employee = request.env.user.employee_id
        if not employee:
            return {'success': False, 'error': 'no_employee'}

        # Lấy IP đáng tin từ request (rightmost trusted hop)
        client_ip = self._get_client_ip()

        # Query tất cả cơ sở active
        locations = request.env['trcf.geo.location'].sudo().search([
            ('active', '=', True),
        ])
        if not locations:
            return {'success': False, 'error': 'no_location_configured'}

        # Tìm cơ sở trong geofence, chọn gần nhất
        matched = []
        for loc in locations:
            dist = self._haversine(lat, lon, loc.latitude, loc.longitude)
            if dist <= loc.radius:
                matched.append((loc, dist))

        if not matched:
            closest_loc = None
            closest_dist = float('inf')
            for loc in locations:
                dist = self._haversine(lat, lon, loc.latitude, loc.longitude)
                if dist < closest_dist:
                    closest_dist = dist
                    closest_loc = loc
            return {
                'success': False,
                'error': 'out_of_range',
                'distance_m': round(closest_dist),
                'radius_m': closest_loc.radius if closest_loc else 0,
            }

        # Tiebreaker: chọn cơ sở gần nhất
        geo_location = min(matched, key=lambda x: x[1])[0]

        # Kiểm tra IP (có thể raise UserError nếu strict mode)
        try:
            ip_suspicious = self._check_ip(geo_location, client_ip)
        except UserError as e:
            return {'success': False, 'error': 'ip_blocked', 'message': str(e.args[0])}

        # Kiểm tra đã check-in chưa
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        existing = request.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', fields.Datetime.to_string(today_start)),
            ('check_in', '<', fields.Datetime.to_string(today_end)),
            ('check_out', '=', False),
        ], limit=1)
        if existing:
            local_in = fields.Datetime.context_timestamp(existing, existing.check_in)
            return {'success': False, 'error': 'already_checked_in', 'check_in': local_in.strftime('%H:%M')}

        # Phát hiện GPS suspicious
        geo_suspicious, geo_suspicious_reason = self._check_geo_suspicious(
            accuracy, employee.id, lat, lon
        )

        # Tạo bản ghi chấm công
        now_utc = fields.Datetime.now()
        attendance = request.env['hr.attendance'].create({
            'employee_id': employee.id,
            'check_in': now_utc,
            'attendance_source': 'geo',
            'geo_location_id': geo_location.id,
            'geo_check_in_lat': lat,
            'geo_check_in_lon': lon,
            'geo_check_in_accuracy': accuracy,
            'geo_suspicious': geo_suspicious,
            'geo_suspicious_reason': geo_suspicious_reason,
            'request_ip': client_ip,
            'ip_suspicious': ip_suspicious,
        })

        local_check_in = fields.Datetime.context_timestamp(attendance, now_utc)
        return {
            'success': True,
            'attendance_id': attendance.id,
            'location_name': geo_location.name,
            'check_in': local_check_in.strftime('%H:%M'),
            'geo_suspicious': geo_suspicious,
            'ip_suspicious': ip_suspicious,
        }

    @http.route('/dang-ky-ca/geo-checkout', type='jsonrpc', auth='user', methods=['POST'])
    def geo_check_out(self, lat, lon, accuracy, **kwargs):
        """API check-out bằng GPS + IP WiFi (cùng quy tắc với check-in).

        Args:
            lat (float): Vĩ độ GPS từ browser.
            lon (float): Kinh độ GPS từ browser.
            accuracy (float): Độ chính xác GPS (mét).

        Returns:
            dict: {success, check_out, worked_hours_display, salary_display}
                  hoặc {success: False, error: str}
        """
        employee = request.env.user.employee_id
        if not employee:
            return {'success': False, 'error': 'no_employee'}

        client_ip = self._get_client_ip()

        # Tìm phiên đang mở
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        attendance = request.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', fields.Datetime.to_string(today_start)),
            ('check_in', '<', fields.Datetime.to_string(today_end)),
            ('check_out', '=', False),
        ], limit=1)
        if not attendance:
            return {'success': False, 'error': 'no_open_session'}

        # Lấy geo_location từ bản ghi đang mở (FK đã lưu lúc check-in)
        geo_location = attendance.geo_location_id
        if geo_location:
            # Validate GPS vs cơ sở đã check-in
            dist = self._haversine(lat, lon, geo_location.latitude, geo_location.longitude)
            if dist > geo_location.radius:
                return {
                    'success': False,
                    'error': 'out_of_range',
                    'distance_m': round(dist),
                    'radius_m': geo_location.radius,
                }
            # Validate IP
            try:
                ip_suspicious_out = self._check_ip(geo_location, client_ip)
            except UserError as e:
                return {'success': False, 'error': 'ip_blocked', 'message': str(e.args[0])}
        else:
            ip_suspicious_out = False

        # Cập nhật check_out
        now_utc = fields.Datetime.now()
        attendance.write({
            'check_out': now_utc,
            'geo_check_out_lat': lat,
            'geo_check_out_lon': lon,
            'geo_check_out_accuracy': accuracy,
            'request_ip': client_ip,  # Ghi đè IP bằng IP checkout (IP cuối cùng)
        })

        local_out = fields.Datetime.context_timestamp(attendance, now_utc)
        wh = attendance.worked_hours or 0.0
        h, m = int(wh), int(round((wh - int(wh)) * 60))
        salary = attendance.trcf_hourly_salary_sum or 0.0

        return {
            'success': True,
            'check_out': local_out.strftime('%H:%M'),
            'worked_hours_display': f'{h}h{m:02d}m',
            'salary_display': '{:,.0f}'.format(salary).replace(',', '.'),
        }

    @http.route('/dang-ky-ca/geo-status', type='http', auth='user', methods=['GET'])
    def geo_status(self, **kwargs):
        """Trả về trạng thái check-in hôm nay của nhân viên hiện tại.

        Returns:
            JSON response: {status: idle|checked_in|done, ...details}
        """
        employee = request.env.user.employee_id
        if not employee:
            return request.make_response(
                json.dumps({'status': 'idle'}),
                headers=[('Content-Type', 'application/json')]
            )

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)

        open_att = request.env['hr.attendance'].search([
            ('employee_id', '=', employee.id),
            ('check_in', '>=', fields.Datetime.to_string(today_start)),
            ('check_in', '<', fields.Datetime.to_string(today_end)),
            ('check_out', '=', False),
        ], limit=1)

        if open_att:
            local_in = fields.Datetime.context_timestamp(open_att, open_att.check_in)
            elapsed = datetime.utcnow() - open_att.check_in.replace(tzinfo=None)
            eh = int(elapsed.total_seconds() // 3600)
            em = int((elapsed.total_seconds() % 3600) // 60)
            result = {
                'status': 'checked_in',
                'attendance_id': open_att.id,
                'check_in_display': local_in.strftime('%H:%M'),
                'location_name': open_att.geo_location_id.name if open_att.geo_location_id else '',
                'elapsed_display': f'{eh}h{em:02d}m',
            }
        else:
            done_att = request.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '>=', fields.Datetime.to_string(today_start)),
                ('check_in', '<', fields.Datetime.to_string(today_end)),
                ('check_out', '!=', False),
                ('attendance_source', '=', 'geo'),
            ], order='check_out desc', limit=1)

            if done_att:
                local_in = fields.Datetime.context_timestamp(done_att, done_att.check_in)
                local_out = fields.Datetime.context_timestamp(done_att, done_att.check_out)
                wh = done_att.worked_hours or 0.0
                h, m = int(wh), int(round((wh - int(wh)) * 60))
                salary = done_att.trcf_hourly_salary_sum or 0.0
                result = {
                    'status': 'done',
                    'check_in_display': local_in.strftime('%H:%M'),
                    'check_out_display': local_out.strftime('%H:%M'),
                    'worked_hours_display': f'{h}h{m:02d}m',
                    'salary_display': '{:,.0f}'.format(salary).replace(',', '.'),
                }
            else:
                result = {'status': 'idle'}

        return request.make_response(
            json.dumps(result),
            headers=[('Content-Type', 'application/json')]
        )

    # ===================================================================
    # PRIVATE HELPER METHODS
    # ===================================================================

    def _get_client_ip(self):
        """Trích xuất public IP đáng tin từ request.

        Ưu tiên rightmost hop trong X-Forwarded-For (gắn bởi nginx/proxy đáng tin),
        fallback về REMOTE_ADDR. Client không thể giả mạo rightmost hop vì nginx append vào.

        Returns:
            str: IP address string.
        """
        xff = request.httprequest.environ.get('HTTP_X_FORWARDED_FOR', '')
        if xff:
            # Rightmost hop là IP do proxy đáng tin gắn vào cuối cùng
            return xff.split(',')[-1].strip()
        return request.httprequest.remote_addr or '0.0.0.0'

    def _check_ip(self, location, client_ip):
        """Kiểm tra IP của request so với danh sách IP cho phép của cơ sở.

        Args:
            location (trcf.geo.location): Cơ sở đang kiểm tra.
            client_ip (str): IP của client (đã trusted từ _get_client_ip).

        Returns:
            bool: True nếu IP đáng ngờ (không khớp) trong chế độ 'warning'.
                  False nếu IP khớp hoặc không cấu hình.

        Raises:
            UserError: Nếu ip_check_mode = 'strict' và IP không khớp.
        """
        if not location.allowed_ips or location.ip_check_mode == 'none':
            return False
        allowed = location.get_allowed_ip_list()
        if client_ip in allowed:
            return False
        if location.ip_check_mode == 'strict':
            raise UserError(_("Thiết bị không kết nối đúng mạng WiFi văn phòng."))
        # 'warning' mode: flag nhưng cho phép check-in
        return True

    def _haversine(self, lat1, lon1, lat2, lon2):
        """Tính khoảng cách metres giữa 2 điểm GPS dùng công thức Haversine.

        Args:
            lat1 (float): Vĩ độ điểm 1 (decimal degrees).
            lon1 (float): Kinh độ điểm 1 (decimal degrees).
            lat2 (float): Vĩ độ điểm 2 (decimal degrees).
            lon2 (float): Kinh độ điểm 2 (decimal degrees).

        Returns:
            float: Khoảng cách tính bằng mét.
        """
        R = 6371000  # Bán kính Trái đất (mét)
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        d_phi = math.radians(lat2 - lat1)
        d_lambda = math.radians(lon2 - lon1)
        a = (math.sin(d_phi / 2) ** 2
             + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2)
        return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def _check_geo_suspicious(self, accuracy, employee_id, lat, lon):
        """Phát hiện dấu hiệu GPS giả mạo.

        Kiểm tra:
        1. accuracy < 5m → bất thường (GPS thực thường 5-20m)
        2. velocity > 500 km/h kể từ check-out gần nhất → không thể di chuyển

        Args:
            accuracy (float): GPS accuracy từ browser (mét).
            employee_id (int): ID nhân viên.
            lat (float): Vĩ độ hiện tại.
            lon (float): Kinh độ hiện tại.

        Returns:
            tuple: (geo_suspicious: bool, geo_suspicious_reason: str)
        """
        suspicious = False
        reasons = []

        # Check 1: GPS accuracy bất thường thấp
        if accuracy < 5:
            suspicious = True
            reasons.append('low_accuracy')

        # Check 2: Velocity giữa check-out trước và check-in hiện tại
        IMPOSSIBLE_SPEED_KMH = 500
        last_checkout = request.env['hr.attendance'].search([
            ('employee_id', '=', employee_id),
            ('check_out', '!=', False),
            ('geo_check_out_lat', '!=', 0),
        ], order='check_out desc', limit=1)

        if last_checkout:
            dist_m = self._haversine(
                last_checkout.geo_check_out_lat, last_checkout.geo_check_out_lon,
                lat, lon
            )
            now_utc = datetime.utcnow()
            last_co = last_checkout.check_out.replace(tzinfo=None)
            time_diff_h = (now_utc - last_co).total_seconds() / 3600
            if time_diff_h > 0:
                speed_kmh = (dist_m / 1000) / time_diff_h
                if speed_kmh > IMPOSSIBLE_SPEED_KMH:
                    suspicious = True
                    reasons.append(f'impossible_velocity:{speed_kmh:.0f}km/h')

        return suspicious, ','.join(reasons)
