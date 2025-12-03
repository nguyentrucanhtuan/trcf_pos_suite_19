# -*- coding: utf-8 -*-
{
    'name': 'TRCF PNL Dashboard',
    'version': '1.0',
    'category': 'Point of Sale',
    'summary': 'Track cashflow and P&L for POS sessions',
    'description': """
        TRCF PNL Dashboard
        ==================
        - Track owner withdrawals when closing POS sessions
        - Set opening balance for next session
        - View detailed cashflow per payment method
    """,
    'author': 'TRCF',
    'license': 'LGPL-3',
    'depends': ['point_of_sale', 'trcf_pos_expenses', 'trcf_fnb_inventory'],
    'data': [
        'security/ir.model.access.csv',
        'views/pos_session_views.xml',
        'views/pos_session_payment_count_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'trcf_pnl_dashboard/static/src/css/closing_popup.css',
            'trcf_pnl_dashboard/static/src/app/components/popups/closing_popup_patch.js',
            'trcf_pnl_dashboard/static/src/xml/closing_popup_patch.xml',
        ],
    },
    'installable': True,
    'application': True,
}
