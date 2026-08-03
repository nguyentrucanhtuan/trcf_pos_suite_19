from odoo import http, fields
from odoo.http import request
from datetime import datetime
from itertools import groupby
from markupsafe import Markup
import json

from ..i18n import get_translator


class TrcfTaskController(http.Controller):
    
    # --- Team Tasks Routes ---
    
    @http.route('/team-tasks', type='http', auth='public', website=True, allow_frames=True)
    def team_tasks_page(self, minimal=False, **kwargs):
        """Trang tổng hợp công việc của tất cả nhân viên trong ca"""
        t = get_translator(request)
        TaskModel = request.env['trcf.shift.task'].sudo()
        today = fields.Date.context_today(TaskModel)
        tasks = TaskModel.search([
            ('assigned_employee_id', '!=', False),
            ('date', '=', today),
        ], order='assigned_employee_id, time_start, id')
        
        employees_data = []
        for emp, emp_tasks in groupby(tasks, lambda t: t.assigned_employee_id):
            employees_data.append({
                'id': emp.id,
                'name': emp.name,
                'tasks': [{
                    'id': t.id,
                    'name': t.name,
                    'description': t.description,
                    'state': t.state,
                    'time_start': t.time_start,
                    'time_display': t.time_display,
                } for t in emp_tasks]
            })

        return request.render('trcf_fnb_staff.task_dashboard_page', {
            't': t,
            'title': t('Bảng công việc chung'),
            'subtitle': t('Tất cả nhân viên'),
            'is_team_view': True,
            'today': today,
            'employees': employees_data,
            'minimal': minimal,
            'refresh_url': '/team-tasks/refresh',
            'start_url': '/team-tasks/start',
            'complete_url': '/team-tasks/complete',
            'task_i18n_json': Markup(json.dumps(self._get_task_i18n(t))),
        })
    
    @http.route('/team-tasks/refresh', type='jsonrpc', auth='public', methods=['POST'])
    def refresh_team_tasks(self, **kwargs):
        """API lấy dữ liệu tasks mới nhất để update UI ngầm"""
        try:
            TaskModel = request.env['trcf.shift.task'].sudo()
            today = fields.Date.context_today(TaskModel)
            tasks = TaskModel.search([
                ('assigned_employee_id', '!=', False),
                ('date', '=', today),
            ], order='assigned_employee_id, time_start, id')
            
            employees_data = []
            for emp, emp_tasks in groupby(tasks, lambda t: t.assigned_employee_id):
                employees_data.append({
                    'id': emp.id,
                    'name': emp.name,
                    'tasks': [{
                        'id': t.id,
                        'name': t.name,
                        'description': t.description,
                        'state': t.state,
                        'time_start': t.time_start,
                        'time_display': t.time_display,
                    } for t in emp_tasks]
                })

            return {
                'success': True,
                'employees': employees_data,
                'completed_tasks': sum(len([t for t in emp['tasks'] if t['state'] == 'done']) for emp in employees_data),
                'total_tasks': sum(len(emp['tasks']) for emp in employees_data),
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @http.route('/team-tasks/start', type='jsonrpc', auth='public', methods=['POST'])
    def team_start_task(self, task_id, **kwargs):
        return self._start_task(task_id)

    @http.route('/team-tasks/complete', type='jsonrpc', auth='public', methods=['POST'])
    def team_complete_task(self, task_id, **kwargs):
        return self._complete_task(task_id)

    # --- My Tasks Routes ---

    @http.route('/my-tasks', type='http', auth='user', website=True)
    def my_tasks_page(self, **kwargs):
        """Trang công việc của nhân viên hiện tại"""
        t = get_translator(request)
        employee = request.env.user.employee_id
        if not employee:
            return request.render('trcf_fnb_staff.task_no_employee', {
                't': t,
                'message': t('Tài khoản của bạn chưa được liên kết với nhân viên.')
            })

        TaskModel = request.env['trcf.shift.task'].sudo()
        today = fields.Date.context_today(TaskModel)

        return request.render('trcf_fnb_staff.task_dashboard_page', {
            't': t,
            'title': t('Công việc của tôi'),
            'subtitle': employee.name,
            'is_team_view': False,
            'today': today,
            'refresh_url': '/my-tasks/refresh',
            'start_url': '/my-tasks/start',
            'complete_url': '/my-tasks/complete',
            'task_i18n_json': Markup(json.dumps(self._get_task_i18n(t))),
        })

    @http.route('/my-tasks/refresh', type='jsonrpc', auth='user', methods=['POST'])
    def refresh_my_tasks(self, **kwargs):
        """API lấy dữ liệu tasks mới nhất của nhân viên"""
        t = get_translator(request)
        try:
            employee = request.env.user.employee_id
            if not employee:
                return {'success': False, 'message': t('Không tìm thấy nhân viên')}
                
            TaskModel = request.env['trcf.shift.task'].sudo()
            today = fields.Date.context_today(TaskModel)
            tasks = TaskModel.search([
                ('assigned_employee_id', '=', employee.id),
                ('date', '=', today),
            ], order='time_start, id')
            
            return {
                'success': True,
                'total_tasks': len(tasks),
                'completed_tasks': len([t for t in tasks if t.state == 'done']),
                'employees': [{
                    'id': employee.id,
                    'name': employee.name,
                    'tasks': [{
                        'id': t.id,
                        'name': t.name,
                        'description': t.description,
                        'state': t.state,
                        'time_start': t.time_start,
                        'time_display': t.time_display,
                    } for t in tasks]
                }]
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/my-tasks/start', type='jsonrpc', auth='user', methods=['POST'])
    def my_start_task(self, task_id, **kwargs):
        return self._start_task(task_id)

    @http.route('/my-tasks/complete', type='jsonrpc', auth='user', methods=['POST'])
    def my_complete_task(self, task_id, **kwargs):
        return self._complete_task(task_id)

    # --- Common Helpers ---

    def _start_task(self, task_id):
        t = get_translator(request)
        try:
            task = request.env['trcf.shift.task'].sudo().browse(int(task_id))
            if task.exists():
                task.action_start()
                return {'success': True}
            return {'success': False, 'message': t('Không tìm thấy công việc')}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def _complete_task(self, task_id):
        t = get_translator(request)
        try:
            task = request.env['trcf.shift.task'].sudo().browse(int(task_id))
            if task.exists():
                task.action_done()
                return {'success': True}
            return {'success': False, 'message': t('Không tìm thấy công việc')}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def _get_task_i18n(self, t):
        """Chuỗi dịch cho phần JS render động (task_dashboard_page dùng CDATA
        script nên không thể gọi t() trực tiếp) -- nhúng qua window.TRCF_TASK_I18N.
        """
        return {
            'unknown_error': t('Không xác định'),
            'error_prefix': t('Lỗi:'),
            'confirm_complete': t('Xác nhận hoàn thành?'),
            'progress_overall': t('Tiến độ chung'),
            'progress_today': t('Tiến độ hôm nay'),
            'tasks_completed_suffix': t('công việc hoàn thành'),
            'state_pending': t('Đang chờ'),
            'state_in_progress': t('Đang làm'),
            'state_done': t('Hoàn thành'),
            'state_overdue': t('Quá hạn'),
            'upcoming_soon': t('⚠️ Sắp tới'),
            'urgent_now': t('🚨 Cần làm ngay'),
            'btn_start': t('Bắt đầu'),
            'btn_complete': t('Hoàn thành'),
            'tasks_count_suffix': t('công việc'),
            'no_tasks_today_team': t('Chưa có công việc hôm nay'),
            'no_tasks_today_mine': t('Không có công việc hôm nay'),
            'no_employees_assigned': t('Chưa có nhân viên nào được gán công việc'),
            'no_tasks_assigned_mine': t('Bạn chưa được gán công việc nào'),
        }
