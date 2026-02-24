# -*- coding: utf-8 -*-
{
    'name': 'TRCF Ops Audit',
    'version': '1.0',
    'category': 'Productivity/Operations',
    'summary': 'Kiểm soát vận hành: công thức, chi phí, tồn kho',
    'author': 'TRCF',
    'website': 'https://coffeetree.vn',
    'depends': ['base', 'point_of_sale', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'views/trcf_ops_dashboard_template.xml',
        'views/trcf_ops_audit_menus.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
