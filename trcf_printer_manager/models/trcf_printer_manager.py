from odoo import models, fields

class TrcfPrinterManager(models.Model):
    _name = 'trcf.printer.manager'
    _description = 'TRCF Printer Manager'

    name = fields.Char(string='Tên máy in', required=True)
    ip_address = fields.Char(string='Địa chỉ IP', required=True)
    port = fields.Integer(string='PORT', default=9100)
    active = fields.Boolean(string='Kích hoạt', default=True)

    # Loại máy in
    printer_type = fields.Selection([
        ('invoice', 'HOÁ ĐƠN'),
        ('label', 'TEM DÁN'),
        ('kitchen_order_ticket', 'PHIẾU YÊU CẦU MÓN')
    ], string='Loại máy in', required=True, default='invoice')

    # Fields cho tem dán (label) - có thể chọn 1 hoặc nhiều
    printer_label_pos_preset_ids = fields.Many2many(
        'pos.preset',
        'trcf_printer_label_pos_preset_rel',
        'printer_id',
        'label_pos_preset_id',
        string='Danh mục nguồn in'
    )

    # Field cho phiếu yêu cầu món (kitchen_order_ticket)
    printer_kot_pos_category_ids = fields.Many2many(
        'pos.category',
        'trcf_printer_kot_pos_category_rel',
        'printer_id',
        'kot_pos_category_id',
        string='Danh mục sản phẩm'
    )

    # Field cấu hình dành cho đơn invoice
    invoice_footer_text = fields.Text(
        string='Chân trang hóa đơn',
        help="Nội dung sẽ được in ở cuối hóa đơn"
    )