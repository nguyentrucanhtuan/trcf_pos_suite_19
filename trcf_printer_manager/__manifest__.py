{
    'name': 'TRCF Printer Manager',
    'version': '1.0',
    'summary': 'Quản lý máy in nội bộ',
    'description': "Quản lý danh sách máy in nội bộ",
    'category': 'Tools',
    'author': 'Tuấn rang cà phê',
    'website': 'https://coffeetree.vn',
    'license': 'LGPL-3',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/trcf_printer_manager_views.xml',
        'views/trcf_printer_manager_menu.xml',
    ],
    'installable': True,
    'application': True,
}
