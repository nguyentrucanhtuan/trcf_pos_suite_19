# -*- coding: utf-8 -*-
{
    'name': 'TRCF AI Business Assistant',
    'version': '1.0',
    'category': 'Productivity/AI',
    'summary': 'Trợ lý kinh doanh thông minh tích hợp Google ADK',
    'author': 'TRCF',
    'website': 'https://coffeetree.vn',
    'depends': ['base', 'mail', 'point_of_sale', 'purchase', 'base_setup'],
    'data': [
        'security/ir.model.access.csv',
        'data/bot_data.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
