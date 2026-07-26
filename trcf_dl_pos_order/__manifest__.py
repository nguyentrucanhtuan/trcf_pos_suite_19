# -*- coding: utf-8 -*-
{
    'name': 'TRCF - Xoá cứng đơn hàng POS',
    'version': '19.0.1.0.0',
    'category': 'Sales/Point of Sale',
    'summary': 'Xoá vĩnh viễn đơn hàng POS bằng SQL, chấp nhận dữ liệu mồ côi',
    'description': """
Xoá cứng đơn hàng POS
=====================

Bỏ qua ràng buộc ORM của Odoo (`_unlink_except_draft_or_cancel`) để xoá vĩnh
viễn đơn hàng POS ở mọi trạng thái, kể cả đơn đã thanh toán / đã xuất hoá đơn.

Cơ chế: dò FK trong `pg_constraint` lúc chạy, tự động xử lý mọi bảng phụ thuộc
(kể cả module cài thêm sau này) theo nguyên tắc:

* Cột NOT NULL hoặc ON DELETE CASCADE -> xoá dòng phụ thuộc (đệ quy).
* Cột NULLABLE -> SET NULL, chấp nhận dữ liệu mồ côi.
* Bảng master (res.partner, product, journal, ...) -> không bao giờ bị xoá.

Mọi lần xoá đều ghi nhật ký kèm snapshot JSON trong *Nhật ký xoá cứng POS*.
""",
    'author': 'TRCF',
    'website': 'https://coffeetree.vn',
    'depends': ['point_of_sale', 'account'],
    'data': [
        'security/trcf_dl_pos_order_groups.xml',
        'security/ir.model.access.csv',
        'wizard/trcf_pos_hard_delete_wizard_views.xml',
        'views/pos_order_views.xml',
        'views/trcf_pos_hard_delete_log_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
