# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TrcfInventoryCheckTemplate(models.Model):
    """
    Mẫu phiếu kiểm kho - Template for inventory check sheets.
    
    Cho phép tạo các mẫu phiếu kiểm kho với danh sách sản phẩm và đơn vị tính
    được định nghĩa sẵn, giúp nhân viên kiểm kho nhanh chóng và chính xác.
    """
    _name = 'trcf.inventory.check.template'
    _description = 'Mẫu Phiếu Kiểm Kho'
    _order = 'name'
    
    name = fields.Char(
        string='Tên phiếu kiểm',
        required=True,
        help='Tên mẫu phiếu kiểm kho (ví dụ: Phiếu kiểm kho chính, Phiếu kiểm quầy)'
    )
    
    location_id = fields.Many2one(
        'stock.location',
        string='Kho/Vị trí',
        required=True,
        domain=[('usage', '=', 'internal')],
        help='Kho hoặc vị trí cần kiểm kho'
    )
    
    line_ids = fields.One2many(
        'trcf.inventory.check.template.line',
        'template_id',
        string='Danh sách sản phẩm',
        help='Danh sách sản phẩm cần kiểm trong phiếu này'
    )
    
    
    note = fields.Text(
        string='Ghi chú',
        help='Ghi chú hoặc hướng dẫn cho phiếu kiểm này'
    )
    
    product_count = fields.Integer(
        string='Số sản phẩm',
        compute='_compute_product_count',
        store=True,
        help='Tổng số sản phẩm trong phiếu kiểm'
    )
    
    @api.depends('line_ids')
    def _compute_product_count(self):
        """Tính tổng số sản phẩm trong phiếu kiểm"""
        for template in self:
            template.product_count = len(template.line_ids)
    
    _sql_constraints = [
        ('name_unique', 'unique(name)', 'Tên phiếu kiểm đã tồn tại! Vui lòng chọn tên khác.'),
    ]


class TrcfInventoryCheckTemplateLine(models.Model):
    """
    Chi tiết sản phẩm trong mẫu phiếu kiểm kho.
    
    Lưu trữ thông tin sản phẩm và đơn vị tính đã được chọn sẵn
    để sử dụng khi kiểm kho thực tế.
    """
    _name = 'trcf.inventory.check.template.line'
    _description = 'Chi Tiết Mẫu Phiếu Kiểm Kho'
    _order = 'sequence, id'
    
    template_id = fields.Many2one(
        'trcf.inventory.check.template',
        string='Mẫu phiếu kiểm',
        required=True,
        ondelete='cascade',
        help='Mẫu phiếu kiểm kho chứa dòng này'
    )
    
    product_id = fields.Many2one(
        'product.product',
        string='Sản phẩm',
        required=True,
        domain=[('type', 'in', ['product', 'consu'])],
        help='Sản phẩm cần kiểm kho'
    )
    
    # Related fields for convenience
    product_uom_id = fields.Many2one(
        'uom.uom',
        related='product_id.uom_id',
        string='Đơn vị mặc định',
        readonly=True,
        help='Đơn vị tính mặc định của sản phẩm'
    )
    
    compatible_uom_ids = fields.Many2many(
        'uom.uom',
        compute='_compute_compatible_uom_ids',
        string='Đơn vị tính tương thích',
        help='Danh sách đơn vị tính có thể chuyển đổi với đơn vị mặc định'
    )
    
    uom_id = fields.Many2one(
        'uom.uom',
        string='Đơn vị tính',
        required=True,
        domain="[('id', 'in', compatible_uom_ids)]",
        help='Đơn vị tính sử dụng khi kiểm kho (chỉ chọn đơn vị cùng loại với đơn vị mặc định)'
    )
    
    sequence = fields.Integer(
        string='Thứ tự',
        default=10,
        help='Thứ tự hiển thị sản phẩm trong phiếu kiểm'
    )
    
    @api.depends('product_id', 'product_id.uom_id')
    def _compute_compatible_uom_ids(self):
        """Tính danh sách đơn vị tính tương thích với đơn vị mặc định của sản phẩm"""
        for line in self:
            if line.product_id and line.product_id.uom_id:
                base_uom = line.product_id.uom_id
                all_uoms = self.env['uom.uom'].search([])
                compatible_uoms = self.env['uom.uom']
                
                # Kiểm tra từng UOM xem có chung reference với base UOM không
                for uom in all_uoms:
                    # Sử dụng method _has_common_reference để kiểm tra
                    if base_uom._has_common_reference(uom):
                        compatible_uoms |= uom
                
                line.compatible_uom_ids = compatible_uoms
            else:
                line.compatible_uom_ids = self.env['uom.uom'].search([])
    
    _sql_constraints = [
        ('product_template_unique', 
         'unique(template_id, product_id)', 
         'Sản phẩm đã tồn tại trong phiếu kiểm này!'),
    ]
    
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Tự động set đơn vị tính mặc định khi chọn sản phẩm"""
        if self.product_id and not self.uom_id:
            self.uom_id = self.product_id.uom_id
    
    @api.onchange('uom_id')
    def _onchange_uom_id(self):
        """Cảnh báo nếu chọn đơn vị tính không tương thích"""
        if self.product_id and self.uom_id and self.product_id.uom_id:
            # Kiểm tra xem 2 UOM có thể chuyển đổi cho nhau không
            try:
                # Thử chuyển đổi 1 đơn vị để kiểm tra tính tương thích
                self.product_id.uom_id._compute_quantity(1.0, self.uom_id)
            except Exception:
                return {
                    'warning': {
                        'title': 'Đơn vị tính không tương thích',
                        'message': f'Đơn vị tính "{self.uom_id.name}" không tương thích với đơn vị mặc định "{self.product_id.uom_id.name}" của sản phẩm này. Vui lòng chọn đơn vị cùng loại.'
                    }
                }
