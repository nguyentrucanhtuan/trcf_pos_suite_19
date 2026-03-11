# -*- coding: utf-8 -*-
{
    'name': 'TRCF FnB Staff Management',
    'version': '1.6.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Quản lý nhân viên, ca làm việc và chấm công FnB',
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
        'views/trcf_task_template.xml',
        'views/trcf_geo_location_views.xml',
        'wizard/trcf_generate_week_tasks_wizard_views.xml',
        'views/res_config_settings_views.xml',
        'data/trcf_shift_task_cron.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trcf_fnb_staff/static/src/js/shift_schedule_grid_action.js',
            'trcf_fnb_staff/static/src/js/geo_map_admin.js',
        ],
        'web.assets_frontend': [
            'trcf_fnb_staff/static/src/css/shift_registration.css',
            'trcf_fnb_staff/static/src/css/geo_attendance.css',
            'trcf_fnb_staff/static/src/js/geo_attendance.js',
        ],
    },
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}