{
    'name': 'MOMO Payment Terminal',
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'summary': 'MOMO Payment Terminal for POS',
    'description': """
        Custom MOMO Payment Terminal integration for Odoo POS
        Shows QR code for payment processing
    """,
    'author': 'Your Company',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_payment_method_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'momo_payment_terminal/static/src/**/*',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
