# -*- coding: utf-8 -*-
{
    'name': 'TRCF Ops Audit',
    'version': '1.0',
    'category': 'Productivity/Operations',
    'summary': 'Kiểm soát vận hành: công thức, chi phí, tồn kho',
    'author': 'TRCF',
    'website': 'https://coffeetree.vn',
    'depends': ['base', 'point_of_sale', 'mrp', 'stock', 'trcf_inventory_check_template'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/trcf_ops_dashboard_template.xml',
        'views/trcf_ops_audit_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
