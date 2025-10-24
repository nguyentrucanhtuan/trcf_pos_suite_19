# -*- coding: utf-8 -*-
{
    'name': 'TRCF - MInvoice VAT',
    'version': '1.0.0',
    'category': 'Point of Sale',
    'summary': 'Xuất hóa đơn điện tử qua MInvoice API',
    'author': 'Tuấn Rang Cà Phê',
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/minvoice_res_config_settings_views.xml',
        'views/trcf_order_pending_vat_views.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}