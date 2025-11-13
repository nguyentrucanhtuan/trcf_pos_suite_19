{
    'name': 'TRCF Profit And Lost Dashboard',
    'version': '18.0.1.0.0',
    'category': 'Accounting',
    'summary': 'Profit and Lost Dashboard Management',
    'description': "BÁO CÁO LÃI LỖ CỦA DOANH NGHIỆP",
    'author': 'Tuấn rang cà phê',
    'website': 'https://coffeetree.vn',
    'depends': ['base'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/trcf_pnl_menu_views.xml',
        # 'views/trcf_pnl_dashboard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'trcf_pnl_dashboard/static/src/css/trcf_pnl_dashboard.css',
            'trcf_pnl_dashboard/static/src/js/trcf_pnl_dashboard.js',
            'trcf_pnl_dashboard/static/src/xml/trcf_pnl_dashboard.xml',
        ]
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}