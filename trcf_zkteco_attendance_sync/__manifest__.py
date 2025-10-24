# -*- coding: utf-8 -*-
{
    'name': 'TRCF ZKTeco Attendance Sync',
    'version': '1.0.0',
    'category': 'Human Resources/Attendances',
    'summary': 'Đồng bộ dữ liệu chấm công từ thiết bị ZKTeco',
    'description': """
        Module đồng bộ dữ liệu chấm công từ thiết bị ZKTeco
        =====================================================
        
        Tính năng chính:
        ----------------
        * Quản lý danh sách thiết bị ZKTeco
        * Kết nối và kiểm tra trạng thái thiết bị
        * Đồng bộ dữ liệu chấm công
        * Tự động cập nhật thông tin thiết bị
        * Theo dõi lịch sử đồng bộ
        
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
    ],
    'external_dependencies': {
        'python': ['pyzk'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/trcf_zkteco_device_views.xml',
        'views/trcf_menu_views.xml',
        'views/trcf_hr_attendance_views.xml',
        'views/trcf_hr_employee_views.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}