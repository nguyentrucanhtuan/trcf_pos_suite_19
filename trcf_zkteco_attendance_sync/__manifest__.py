# -*- coding: utf-8 -*-
{
    'name': 'TRCF ZKTeco Attendance Sync',
    'version': '1.5.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Đồng bộ dữ liệu chấm công từ thiết bị ZKTeco và quản lý ca làm việc',
    'description': """
        Module đồng bộ dữ liệu chấm công từ thiết bị ZKTeco
        =====================================================
        
        Tính năng chính:
        ----------------
        * Quản lý danh sách thiết bị ZKTeco
        * Kết nối và kiểm tra trạng thái thiết bị
        * Đồng bộ dữ liệu chấm công
        * Quản lý ca làm việc
        * Đăng ký ca cho nhân viên
        * Xếp ca theo tuần (Grid View)
        * Quản lý công việc theo ca
        
        Yêu cầu:
        --------
        * Python library: pyzk (pip install pyzk)
        * Thiết bị ZKTeco hỗ trợ giao thức TCP/IP
    """,
    'author': 'Tuấn Rang Cà Phê',
    'website': 'https://coffeetree.vn',
    'depends': [
        'base',
        'hr',
        'hr_attendance',
        'website',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/trcf_zkteco_device_views.xml',
        'views/trcf_hr_attendance_views.xml',
        'views/trcf_hr_employee_views.xml',
        'views/trcf_work_shift_views.xml',
        'views/trcf_shift_registration_views.xml',
        'views/trcf_shift_registration_templates.xml',
        'views/trcf_shift_schedule_grid_template.xml',
        'views/trcf_shift_schedule_grid_action.xml',
        'views/trcf_shift_task_template_views.xml',
        'views/trcf_shift_task_views.xml',
        'wizard/trcf_generate_week_tasks_wizard_views.xml',
        'data/trcf_ir_model_data.xml',
        'data/trcf_shift_task_cron.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trcf_zkteco_attendance_sync/static/src/js/shift_schedule_grid_action.js',
        ],
        'web.assets_frontend': [
            'trcf_zkteco_attendance_sync/static/src/css/shift_registration.css',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}