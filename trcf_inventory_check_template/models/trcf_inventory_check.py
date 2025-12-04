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
        'Vị trí kho',
        required=True,
        readonly=True,
        domain=[('usage', '=', 'internal')],
        help='Vị trí kho thực hiện kiểm kho'
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
    
    # Monetary fields
    total_system_value = fields.Float(
        'Tổng giá trị HT', 
        compute='_compute_totals',
        store=True,
        digits='Product Price',
        help='Tổng giá trị tồn kho theo hệ thống'
    )
    total_actual_value = fields.Float(
        'Tổng giá trị TT', 
        compute='_compute_totals',
        store=True,
        digits='Product Price',
        help='Tổng giá trị tồn kho thực tế'
    )
    total_difference_value = fields.Float(
        'Tổng chênh lệch', 
        compute='_compute_totals',
        store=True,
        digits='Product Price',
        help='Tổng giá trị chênh lệch'
    )
    loss_percentage = fields.Float(
        '% Hao hụt', 
        compute='_compute_totals',
        store=True,
        digits=(16, 2),
        help='Phần trăm hao hụt (chỉ tính chênh lệch âm)'
    )
    
    @api.depends('line_ids.system_qty', 'line_ids.actual_qty', 'line_ids.product_cost')
    def _compute_totals(self):
        """Tính tổng giá trị và phần trăm hao hụt"""
        for check in self:
            total_system = 0.0
            total_actual = 0.0
            total_diff = 0.0
            loss_value = 0.0
            
            for line in check.line_ids:
                cost = line.product_cost or 0.0
                line_system_val = line.system_qty * cost
                line_actual_val = line.actual_qty * cost
                line_diff_val = line.difference_qty * cost
                
                total_system += line_system_val
                total_actual += line_actual_val
                total_diff += line_diff_val
                
                # Chỉ tính hao hụt cho các dòng có chênh lệch âm
                if line.difference_qty < 0:
                    loss_value += abs(line_diff_val)
            
            check.total_system_value = total_system
            check.total_actual_value = total_actual
            check.total_difference_value = total_diff
            
            # Tính % hao hụt = (Tổng giá trị mất đi / Tổng giá trị hệ thống) * 100
            if total_system > 0:
                check.loss_percentage = (loss_value / total_system) * 100
            else:
                check.loss_percentage = 0.0    
    
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
    
    product_cost = fields.Float(
        'Giá vốn',
        digits='Product Price',
        help='Giá vốn sản phẩm tại thời điểm kiểm'
    )
    
    difference_value = fields.Float(
        'Giá trị chênh lệch',
        compute='_compute_difference',
        store=True,
        digits='Product Price',
        help='Giá trị chênh lệch = Số lượng chênh lệch * Giá vốn'
    )
    
    @api.depends('system_qty', 'actual_qty', 'product_cost')
    def _compute_difference(self):
        """Tính chênh lệch số lượng và giá trị"""
        for line in self:
            line.difference_qty = line.actual_qty - line.system_qty
            line.difference_value = line.difference_qty * (line.product_cost or 0.0)
