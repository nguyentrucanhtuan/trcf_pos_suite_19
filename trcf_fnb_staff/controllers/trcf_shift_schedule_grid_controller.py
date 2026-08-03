# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
from markupsafe import Markup
import json

from ..i18n import get_translator


class TrcfShiftScheduleGridController(http.Controller):

    @http.route('/shift-schedule', type='http', auth='user', website=True, allow_frames=True)
    def shift_schedule_grid_page(self, start_date=None, **kwargs):
        """Trang xếp ca theo tuần cho Admin - dùng trcf.shift.registration"""
        t = get_translator(request)

        # Kiểm tra quyền HR
        if not request.env.user.has_group('hr.group_hr_user'):
            return request.render('trcf_fnb_staff.shift_schedule_access_denied', {'t': t})
        
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
        weekdays = [t('Thứ 2'), t('Thứ 3'), t('Thứ 4'), t('Thứ 5'), t('Thứ 6'), t('Thứ 7'), t('Chủ nhật')]
        
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
        
        return request.render('trcf_fnb_staff.shift_schedule_grid', {
            't': t,
            'schedule_data': schedule_data,
            'employees': employees_list,
            # Markup(): t-raw/t-out HTML-escape plain strings, which corrupts
            # JSON embedded in a <script> tag (entities aren't decoded there) --
            # mark this pre-serialized JSON as already-safe raw output.
            'schedule_data_json': Markup(json.dumps(schedule_data)),
            'employees_json': Markup(json.dumps(employees_list)),
        })
    
    @http.route('/shift-schedule/add-employee', type='jsonrpc', auth='user', methods=['POST'])
    def add_employee_to_shift(self, **kwargs):
        """API thêm nhân viên vào ca (tạo registration)"""
        t = get_translator(request)
        try:
            if not request.env.user.has_group('hr.group_hr_user'):
                return {'success': False, 'message': t('Bạn không có quyền thực hiện thao tác này')}

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
                return {'success': False, 'message': t('Nhân viên đã được xếp vào ca này')}
            
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
    
    @http.route('/shift-schedule/remove-employee', type='jsonrpc', auth='user', methods=['POST'])
    def remove_employee_from_shift(self, **kwargs):
        """API xóa nhân viên khỏi ca (xóa registration)"""
        t = get_translator(request)
        try:
            if not request.env.user.has_group('hr.group_hr_user'):
                return {'success': False, 'message': t('Bạn không có quyền thực hiện thao tác này')}

            registration_id = kwargs.get('registration_id')

            registration = request.env['trcf.shift.registration'].sudo().browse(int(registration_id))
            if registration.exists():
                registration.unlink()
                return {'success': True}

            return {'success': False, 'message': t('Không tìm thấy đăng ký')}

        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/shift-schedule/approve', type='jsonrpc', auth='user', methods=['POST'])
    def approve_registration(self, **kwargs):
        """API duyệt registration"""
        t = get_translator(request)
        try:
            if not request.env.user.has_group('hr.group_hr_user'):
                return {'success': False, 'message': t('Bạn không có quyền thực hiện thao tác này')}

            registration_id = kwargs.get('registration_id')

            registration = request.env['trcf.shift.registration'].sudo().browse(int(registration_id))
            if registration.exists():
                registration.action_confirm()
                return {'success': True}

            return {'success': False, 'message': t('Không tìm thấy đăng ký')}

        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/shift-schedule/reject', type='jsonrpc', auth='user', methods=['POST'])
    def reject_registration(self, **kwargs):
        """API từ chối registration"""
        t = get_translator(request)
        try:
            if not request.env.user.has_group('hr.group_hr_user'):
                return {'success': False, 'message': t('Bạn không có quyền thực hiện thao tác này')}

            registration_id = kwargs.get('registration_id')

            registration = request.env['trcf.shift.registration'].sudo().browse(int(registration_id))
            if registration.exists():
                registration.action_reject()
                return {'success': True}

            return {'success': False, 'message': t('Không tìm thấy đăng ký')}

        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/shift-schedule/approve-all', type='jsonrpc', auth='user', methods=['POST'])
    def approve_all_registrations(self, **kwargs):
        """API duyệt tất cả registration trong tuần"""
        t = get_translator(request)
        try:
            if not request.env.user.has_group('hr.group_hr_user'):
                return {'success': False, 'message': t('Bạn không có quyền thực hiện thao tác này')}

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

            return {'success': True, 'message': t('Đã duyệt {count} đăng ký ca!').format(count=count)}

        except Exception as e:
            return {'success': False, 'message': str(e)}
