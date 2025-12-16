# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime


class TrcfMyTasksController(http.Controller):
    
    @http.route('/my-tasks', type='http', auth='user', website=True)
    def my_tasks_page(self, **kwargs):
        """Trang công việc của nhân viên"""
        
        # Lấy nhân viên hiện tại
        employee = request.env.user.employee_id
        if not employee:
            return request.render('trcf_zkteco_attendance_sync.my_tasks_no_employee')
        
        # Lấy tasks hôm nay của nhân viên
        today = datetime.now().date()
        tasks = request.env['trcf.shift.task'].sudo().search([
            ('assigned_employee_id', '=', employee.id),
            ('date', '=', today),
        ], order='time_start, id')
        
        # Tạo danh sách tasks
        tasks_list = []
        current_time = datetime.now()
        current_hour = current_time.hour + current_time.minute / 60.0
        
        for task in tasks:
            task_info = {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'time_start': task.time_start,
                'time_end': task.time_end,
                'time_display': task.time_display,
                'state': task.state,
                'completed_at': task.completed_at,
                'is_upcoming': task.time_start <= current_hour + 0.25 and task.state == 'pending',  # 15 phút trước
            }
            tasks_list.append(task_info)
        
        return request.render('trcf_zkteco_attendance_sync.my_tasks_page', {
            'employee': employee,
            'tasks': tasks_list,
            'today': today,
        })
    
    @http.route('/my-tasks/start', type='json', auth='user', methods=['POST'])
    def start_task(self, task_id, **kwargs):
        """API bắt đầu task"""
        try:
            task = request.env['trcf.shift.task'].sudo().browse(int(task_id))
            if task.exists() and task.assigned_employee_id == request.env.user.employee_id:
                task.action_start()
                return {'success': True}
            return {'success': False, 'message': 'Không tìm thấy công việc'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @http.route('/my-tasks/complete', type='json', auth='user', methods=['POST'])
    def complete_task(self, task_id, note=None, **kwargs):
        """API hoàn thành task"""
        try:
            task = request.env['trcf.shift.task'].sudo().browse(int(task_id))
            if task.exists() and task.assigned_employee_id == request.env.user.employee_id:
                if note:
                    task.note = note
                task.action_done()
                return {'success': True}
            return {'success': False, 'message': 'Không tìm thấy công việc'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @http.route('/my-tasks/refresh', type='json', auth='user', methods=['POST'])
    def refresh_tasks(self, **kwargs):
        """API refresh danh sách tasks"""
        try:
            employee = request.env.user.employee_id
            if not employee:
                return {'success': False, 'message': 'Không tìm thấy nhân viên'}
            
            today = datetime.now().date()
            tasks = request.env['trcf.shift.task'].sudo().search([
                ('assigned_employee_id', '=', employee.id),
                ('date', '=', today),
            ], order='time_start, state')
            
            tasks_list = []
            current_time = datetime.now()
            current_hour = current_time.hour + current_time.minute / 60.0
            
            for task in tasks:
                tasks_list.append({
                    'id': task.id,
                    'name': task.name,
                    'description': task.description,
                    'time_start': task.time_start,
                    'time_end': task.time_end,
                    'time_display': task.time_display,
                    'state': task.state,
                    'is_upcoming': task.time_start <= current_hour + 0.25 and task.state == 'pending',  # 15 phút trước
                })
            
            return {'success': True, 'tasks': tasks_list}
        except Exception as e:
            return {'success': False, 'message': str(e)}
