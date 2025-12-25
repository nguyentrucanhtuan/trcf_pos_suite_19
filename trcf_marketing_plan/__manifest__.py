# -*- coding: utf-8 -*-
{
    'name': 'TRCF Marketing Plan',
    'version': '19.0.1.0.0',
    'category': 'Marketing',
    'summary': 'AI-powered Content Pillars & Angles Generator',
    'description': """
        Tạo Content Pillars và Angles cho các nền tảng:
        - TikTok
        - Instagram
        - Facebook
        - Threads
        
        Tính năng:
        - Dựa trên Customer Persona và Brand Key
        - Workflow duyệt/từ chối content
        - AI học từ feedback để tránh lặp nội dung
    """,
    'author': 'Coffee Tree',
    'website': 'https://coffeetree.vn',
    'license': 'LGPL-3',
    'depends': ['base', 'point_of_sale'],
    'external_dependencies': {
        'python': ['google-adk', 'google-genai']
    },
    'data': [
        'security/ir.model.access.csv',
        'views/trcf_marketing_content_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
