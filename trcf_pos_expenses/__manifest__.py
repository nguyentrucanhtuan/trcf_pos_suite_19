# -*- coding: utf-8 -*-
{
    'name': 'TRCF POS Expenses',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Expense Management for COFFEETREE',
    'description': """
        Simple expense management module with:
        - Expense categories
        - Expense tracking
        - POS payment method integration
        - Simple workflow (draft → paid)
    """,
    'author': 'COFFEETREE',
    'depends': ['base', 'point_of_sale', 'mail', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/trcf_expense_sequence.xml',
        'views/trcf_expense_views.xml',
        'views/trcf_expense_category_views.xml',
        'views/trcf_expense_menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
