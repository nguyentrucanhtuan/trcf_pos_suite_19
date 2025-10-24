{
    'name': 'TRCF Display Kitchen Screen',
    'version': '1.0',
    'summary': 'Màn hình bếp cho POS - Tuấn Rang Cà Phê',
    'description': 'Quản lý màn hình bếp cho hệ thống POS, cho phép lọc danh mục món ăn và gán theo từng POS.',
    'category': 'Point of Sale',
    'author': 'Tuấn Rang Cà Phê',
    'website': 'https://coffeetree.vn',  # có thể thay đổi
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/trcf_kitchen_screen_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trcf_kitchen_screen/static/src/js/trcf_kitchen_dashboard.js',
            'trcf_kitchen_screen/static/src/xml/trcf_kitchen_dashboard.xml',
            'trcf_kitchen_screen/static/src/css/trcf_kitchen_dashboard.css'
        ],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
