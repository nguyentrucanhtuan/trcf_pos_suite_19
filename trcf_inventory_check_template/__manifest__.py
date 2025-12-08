# -*- coding: utf-8 -*-
{
    'name': 'TRCF Inventory Check Template',
    'author': 'Tuấn Rang Cà Phê',
    'version': '1.1.0',
    'category': 'Inventory',
    'summary': 'Quản lý mẫu phiếu kiểm kho - Template management for inventory checks',
    'description': """
        TRCF Inventory Check Template
        ==============================
        
        Module quản lý mẫu phiếu kiểm kho, cho phép:
        - Tạo các mẫu phiếu kiểm kho với danh sách sản phẩm định sẵn
        - Chọn đơn vị tính riêng cho từng sản phẩm
        - Sắp xếp thứ tự sản phẩm theo vị trí vật lý
        - Tái sử dụng mẫu phiếu khi kiểm kho thực tế
        - Lưu lịch sử kiểm kho với thông tin chi tiết
        
        Giúp nhân viên kiểm kho nhanh chóng và chính xác hơn.
    """,
    'depends': ['base', 'stock', 'product', 'uom'],
    'data': [
        'security/ir.model.access.csv',
        'data/trcf_inventory_check_sequence.xml',
        'views/product_template_views.xml',
        'views/trcf_inventory_check_template_views.xml',
        'views/trcf_inventory_check_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
