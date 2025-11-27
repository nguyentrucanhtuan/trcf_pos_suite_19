# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TrcfInventoryCheck(models.Model):
    _name = 'trcf.inventory.check'
    _description = 'Phiếu Kiểm Kho'
    _order = 'check_date desc, id desc'
    
    name = fields.Char(
        'Mã phiếu', 
        required=True, 
        default='New', 
        readonly=True, 
        copy=False,
        help='Mã phiếu kiểm kho tự động'
    )
    template_id = fields.Many2one(
        'trcf.inventory.check.template', 
        'Template sử dụng',
        readonly=True,
        help='Template được sử dụng để tạo phiếu kiểm này'
    )
    location_id = fields.Many2one(
        'stock.location', 
        'Kho', 
        required=True,
        readonly=True, 
        domain=[('usage', '=', 'internal')],
        help='Kho/vị trí thực hiện kiểm kho'
    )
    check_date = fields.Datetime(
        'Ngày kiểm', 
        required=True,
        default=fields.Datetime.now, 
        readonly=True,
        help='Thời điểm thực hiện kiểm kho'
    )
    user_id = fields.Many2one(
        'res.users', 
        'Người kiểm', 
        required=True,
        default=lambda self: self.env.user, 
        readonly=True,
        help='Nhân viên thực hiện kiểm kho'
    )
    line_ids = fields.One2many(
        'trcf.inventory.check.line', 
        'check_id', 
        'Chi tiết sản phẩm',
        help='Danh sách sản phẩm được kiểm'
    )
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('done', 'Hoàn tất')
    ], 
        default='draft', 
        readonly=True, 
        required=True,
        help='Trạng thái phiếu kiểm'
    )
    note = fields.Text('Ghi chú', help='Ghi chú bổ sung cho phiếu kiểm')
    
    
    @api.model_create_multi
    def create(self, vals_list):
        """Auto-generate sequence name"""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'trcf.inventory.check') or 'New'
        return super().create(vals_list)



class TrcfInventoryCheckLine(models.Model):
    _name = 'trcf.inventory.check.line'
    _description = 'Chi Tiết Phiếu Kiểm Kho'
    _order = 'sequence, id'
    
    check_id = fields.Many2one(
        'trcf.inventory.check', 
        'Phiếu kiểm',
        required=True,
        ondelete='cascade', 
        index=True,
        help='Phiếu kiểm kho chứa dòng này'
    )
    sequence = fields.Integer(
        'Thứ tự', 
        default=10,
        help='Thứ tự hiển thị sản phẩm'
    )
    product_id = fields.Many2one(
        'product.product', 
        'Sản phẩm', 
        required=True,
        help='Sản phẩm được kiểm'
    )
    uom_id = fields.Many2one(
        'uom.uom', 
        'Đơn vị', 
        required=True,
        help='Đơn vị tính sử dụng khi kiểm'
    )
    system_qty = fields.Float(
        'Tồn hệ thống', 
        digits='Product Unit',
        help='Số lượng tồn kho theo hệ thống'
    )
    actual_qty = fields.Float(
        'Tồn thực tế', 
        digits='Product Unit',
        help='Số lượng thực tế đếm được'
    )
    difference_qty = fields.Float(
        'Chênh lệch', 
        compute='_compute_difference',
        store=True, 
        digits='Product Unit',
        help='Chênh lệch giữa thực tế và hệ thống'
    )
    
    @api.depends('system_qty', 'actual_qty')
    def _compute_difference(self):
        """Tính chênh lệch = thực tế - hệ thống"""
        for line in self:
            line.difference_qty = line.actual_qty - line.system_qty
