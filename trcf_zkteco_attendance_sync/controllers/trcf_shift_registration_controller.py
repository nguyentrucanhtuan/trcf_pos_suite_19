# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import json


class TrcfShiftRegistrationController(http.Controller):
    
    @http.route('/shift-registration', type='http', auth='user', website=True)
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
        
        # Tạo danh sách 14 ngày tiếp theo (2 tuần)
        today = datetime.now().date()
        dates = []
        for i in range(14):
            current_date = today + timedelta(days=i)
            dates.append({
                'date': current_date,
                'date_str': current_date.strftime('%Y-%m-%d'),
                'display': current_date.strftime('%d/%m'),
                'weekday': self._get_weekday_name(current_date.weekday()),
                'is_weekend': current_date.weekday() >= 5,
            })
        
        # Lấy các đăng ký hiện tại của nhân viên
        registrations = request.env['trcf.shift.registration'].sudo().search([
            ('employee_id', '=', employee.id),
            ('date', '>=', today),
            ('date', '<=', today + timedelta(days=13)),
        ])
        
        # Tạo set các đăng ký đã có (date_shift_id)
        registered_set = set()
        for reg in registrations:
            key = f"{reg.date.strftime('%Y-%m-%d')}_{reg.shift_id.id}"
            registered_set.add(key)
        
        return request.render('trcf_zkteco_attendance_sync.shift_registration_form', {
            'employee': employee,
            'shifts': shifts,
            'dates': dates,
            'registered_set': registered_set,
        })
    
    @http.route('/shift-registration/save', type='json', auth='user', methods=['POST'])
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
    
    @http.route('/shift-registration/remove', type='json', auth='user', methods=['POST'])
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
    
    def _get_weekday_name(self, weekday):
        """Trả về tên thứ trong tuần"""
        weekdays = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
        return weekdays[weekday]
