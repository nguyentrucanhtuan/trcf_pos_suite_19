# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import json


class TrcfShiftScheduleGridController(http.Controller):
    
    @http.route('/shift-schedule', type='http', auth='user', website=True)
    def shift_schedule_grid_page(self, start_date=None, **kwargs):
        """Trang xếp ca theo tuần cho Admin - dùng trcf.shift.registration"""
        
        # Kiểm tra quyền HR
        if not request.env.user.has_group('hr.group_hr_user'):
            return request.render('trcf_zkteco_attendance_sync.shift_schedule_access_denied')
        
        # Tính toán tuần
        if not start_date:
            today = datetime.now().date()
            start_date = today - timedelta(days=today.weekday())
        elif isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        
        end_date = start_date + timedelta(days=6)
        
        # Lấy tất cả ca làm việc active
        shifts = request.env['trcf.work.shift'].sudo().search([
            ('active', '=', True)
        ], order='time_start')
        
        # Lấy registrations trong tuần
        registrations = request.env['trcf.shift.registration'].sudo().search([
            ('date', '>=', start_date),
            ('date', '<=', end_date),
        ])
        
        # Lấy danh sách nhân viên
        employees = request.env['hr.employee'].sudo().search([], order='name')
        employees_list = [{'id': e.id, 'name': e.name} for e in employees]
        
        # Tạo cấu trúc dữ liệu
        weekdays = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
        
        dates = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            dates.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'display': current_date.strftime('%d/%m'),
                'weekday': weekdays[i],
                'is_today': current_date == datetime.now().date(),
            })
        
        shifts_data = []
        for shift in shifts:
            shifts_data.append({
                'id': shift.id,
                'name': shift.name,
                'time_display': shift.get_time_display(),
                'min_employees': shift.min_employees,
                'max_employees': shift.max_employees,
            })
        
        # Tạo grid data
        grid_data = {}
        for date_info in dates:
            date_str = date_info['date']
            grid_data[date_str] = {}
            
            for shift in shifts:
                # Lấy registrations cho ngày + ca này
                regs = registrations.filtered(
                    lambda r: r.date.strftime('%Y-%m-%d') == date_str and r.shift_id.id == shift.id
                )
                
                employees_data = []
                for reg in regs:
                    employees_data.append({
                        'id': reg.employee_id.id,
                        'name': reg.employee_id.name,
                        'registration_id': reg.id,
                        'state': reg.state,
                    })
                
                grid_data[date_str][shift.id] = {
                    'employees': employees_data,
                    'total': len(employees_data),
                    'min': shift.min_employees,
                    'max': shift.max_employees,
                }
        
        schedule_data = {
            'start_date': start_date.strftime('%Y-%m-%d'),
            'end_date': end_date.strftime('%Y-%m-%d'),
            'dates': dates,
            'shifts': shifts_data,
            'grid_data': grid_data,
        }
        
        return request.render('trcf_zkteco_attendance_sync.shift_schedule_grid', {
            'schedule_data': schedule_data,
            'employees': employees_list,
            'schedule_data_json': json.dumps(schedule_data),
            'employees_json': json.dumps(employees_list),
        })
    
    @http.route('/shift-schedule/add-employee', type='json', auth='user', methods=['POST'])
    def add_employee_to_shift(self, **kwargs):
        """API thêm nhân viên vào ca (tạo registration)"""
        try:
            if not request.env.user.has_group('hr.group_hr_user'):
                return {'success': False, 'message': 'Bạn không có quyền thực hiện thao tác này'}
            
            date = kwargs.get('date')
            shift_id = kwargs.get('shift_id')
            employee_id = kwargs.get('employee_id')
            
            # Kiểm tra đã có registration chưa
            existing = request.env['trcf.shift.registration'].sudo().search([
                ('date', '=', date),
                ('shift_id', '=', int(shift_id)),
                ('employee_id', '=', int(employee_id)),
            ], limit=1)
            
            if existing:
                return {'success': False, 'message': 'Nhân viên đã được xếp vào ca này'}
            
            # Tạo registration mới với state = draft
            registration = request.env['trcf.shift.registration'].sudo().create({
                'date': date,
                'shift_id': int(shift_id),
                'employee_id': int(employee_id),
                'state': 'draft',
            })
            
            return {
                'success': True,
                'registration_id': registration.id,
            }
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @http.route('/shift-schedule/remove-employee', type='json', auth='user', methods=['POST'])
    def remove_employee_from_shift(self, **kwargs):
        """API xóa nhân viên khỏi ca (xóa registration)"""
        try:
            if not request.env.user.has_group('hr.group_hr_user'):
                return {'success': False, 'message': 'Bạn không có quyền thực hiện thao tác này'}
            
            registration_id = kwargs.get('registration_id')
            
            registration = request.env['trcf.shift.registration'].sudo().browse(int(registration_id))
            if registration.exists():
                registration.unlink()
                return {'success': True}
            
            return {'success': False, 'message': 'Không tìm thấy đăng ký'}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @http.route('/shift-schedule/approve', type='json', auth='user', methods=['POST'])
    def approve_registration(self, **kwargs):
        """API duyệt registration"""
        try:
            if not request.env.user.has_group('hr.group_hr_user'):
                return {'success': False, 'message': 'Bạn không có quyền thực hiện thao tác này'}
            
            registration_id = kwargs.get('registration_id')
            
            registration = request.env['trcf.shift.registration'].sudo().browse(int(registration_id))
            if registration.exists():
                registration.action_confirm()
                return {'success': True}
            
            return {'success': False, 'message': 'Không tìm thấy đăng ký'}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @http.route('/shift-schedule/approve-all', type='json', auth='user', methods=['POST'])
    def approve_all_registrations(self, **kwargs):
        """API duyệt tất cả registration trong tuần"""
        try:
            if not request.env.user.has_group('hr.group_hr_user'):
                return {'success': False, 'message': 'Bạn không có quyền thực hiện thao tác này'}
            
            start_date = kwargs.get('start_date')
            
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            
            end_date = start_date + timedelta(days=6)
            
            registrations = request.env['trcf.shift.registration'].sudo().search([
                ('date', '>=', start_date),
                ('date', '<=', end_date),
                ('state', '=', 'draft'),
            ])
            
            count = 0
            for registration in registrations:
                registration.action_confirm()
                count += 1
            
            return {'success': True, 'message': f'Đã duyệt {count} đăng ký ca!'}
            
        except Exception as e:
            return {'success': False, 'message': str(e)}
