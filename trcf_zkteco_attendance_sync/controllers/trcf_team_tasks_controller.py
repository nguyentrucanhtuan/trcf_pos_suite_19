# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime


class TrcfTeamTasksController(http.Controller):
    
    @http.route('/team-tasks', type='http', auth='public', website=True)
    def team_tasks_page(self, **kwargs):
        """Trang tổng hợp công việc của tất cả nhân viên trong ca"""
        
        # Lấy TẤT CẢ tasks hôm nay (có assigned_employee_id)
        today = datetime.now().date()
        tasks = request.env['trcf.shift.task'].sudo().search([
            ('assigned_employee_id', '!=', False),  # Có gán nhân viên
            ('date', '=', today),
        ], order='assigned_employee_id, time_start, id')
        
        # Nhóm tasks theo nhân viên
        employees_tasks = {}
        current_time = datetime.now()
        current_hour = current_time.hour + current_time.minute / 60.0
        
        for task in tasks:
            emp_id = task.assigned_employee_id.id
            emp_name = task.assigned_employee_id.name
            
            if emp_id not in employees_tasks:
                employees_tasks[emp_id] = {
                    'name': emp_name,
                    'tasks': []
                }
            
            task_info = {
                'id': task.id,
                'name': task.name,
                'description': task.description,
                'time_start': task.time_start,
                'time_end': task.time_end,
                'time_display': task.time_display,
                'state': task.state,
                'completed_at': task.completed_at,
                'is_upcoming': task.time_start <= current_hour + 0.25 and task.state == 'pending',
            }
            employees_tasks[emp_id]['tasks'].append(task_info)
        
        # Chuyển dict thành list để dễ render
        employees_list = [
            {'id': emp_id, 'name': data['name'], 'tasks': data['tasks']}
            for emp_id, data in employees_tasks.items()
        ]
        
        return request.render('trcf_zkteco_attendance_sync.team_tasks_page', {
            'employees': employees_list,
            'today': today,
        })
    
    @http.route('/team-tasks/start', type='json', auth='public', methods=['POST'])
    def start_task(self, task_id, **kwargs):
        """API bắt đầu task"""
        try:
            task = request.env['trcf.shift.task'].sudo().browse(int(task_id))
            if task.exists():
                task.action_start()
                return {'success': True}
            return {'success': False, 'message': 'Không tìm thấy công việc'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @http.route('/team-tasks/complete', type='json', auth='public', methods=['POST'])
    def complete_task(self, task_id, **kwargs):
        """API hoàn thành task"""
        try:
            task = request.env['trcf.shift.task'].sudo().browse(int(task_id))
            if task.exists():
                task.action_done()
                return {'success': True}
            return {'success': False, 'message': 'Không tìm thấy công việc'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
