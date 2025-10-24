{
    'name': "TRCF Payment MoMo",
    'version': '1.0',
    'category': 'Accounting/Payment',
    'summary': "Tích hợp thanh toán MoMo (Tuấn Rang Cà Phê)",
    'author': "Tuấn Rang Cà Phê",
    'website': "https://coffeetree.vn",
    'depends': ['base', 'payment', 'point_of_sale'],
    'data': [
        'views/trcf_momo_payment_views.xml',
        # 'views/trcf_momo_payment_templates.xml',
    ],
    'assets': {
        'point_of_sale.assets': [
            'trcf_payment_momo/static/src/js/trcf_payment_momo.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'description': """
        Module thanh toán MoMo cho hệ thống POS và E-Commerce.
        Khi chọn MoMo, hiển thị mã QR mẫu cùng số tiền cần thanh toán.
        Tác giả: Tuấn Rang Cà Phê
    """,
}