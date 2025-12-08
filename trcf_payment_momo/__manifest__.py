{
    'name': "TRCF Payment MoMo",
    'version': '1.0',
    'category': 'Point of Sale',
    'summary': "Tích hợp thanh toán MoMo qua QR code cho POS",
    'author': "Tuấn Rang Cà Phê",
    'website': "https://coffeetree.vn",
    'depends': ['point_of_sale'],
    'data': [
        'views/trcf_momo_payment_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'trcf_payment_momo/static/src/**/*',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'description': """
        Module thanh toán MoMo cho hệ thống POS.
        Khi chọn MoMo, hiển thị mã QR để khách hàng quét thanh toán.
        Xác nhận thanh toán thủ công.
        Tác giả: Tuấn Rang Cà Phê
    """,
}