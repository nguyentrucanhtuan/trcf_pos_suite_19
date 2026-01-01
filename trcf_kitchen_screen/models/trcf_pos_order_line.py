from odoo import api, fields, models

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    trcf_order_status = fields.Selection(
        selection=[('draft', 'Draft'), ('waiting', 'Cooking'),
                   ('ready', 'Ready'), ('cancel', 'Cancel')], default='draft',
        help='Trạng thái hoàn thành của sản phẩm')
    
    @api.model
    def update_order_line_status(self, order_line_id, new_status): 
        """Cập nhật trạng thái sản phẩm và gửi thông báo tới tất cả màn hình"""
        
        import logging
        from datetime import datetime
        _logger = logging.getLogger(__name__)
            
        try:
            order_line = self.env["pos.order.line"].browse(order_line_id)
            
            if not order_line.exists():
                return {'success': False, 'error': 'Order line không tồn tại'}
            
            # Lưu trạng thái cũ
            old_status = order_line.trcf_order_status

            # Cập nhật trạng thái mới
            order_line.write({'trcf_order_status': new_status})

            # ✅ KIỂM TRA VÀ CẬP NHẬT ORDER STATUS
            self.check_order_done(order_line.order_id.id)
            
            # ✅ GỬI THÔNG BÁO BUS ĐỂN TẤT CẢ MÀN HÌNH
            channel_name = 'pos_order_line_status_updated'
            bus_type = 'notification'
            payload_data = {
                'message': 'pos_order_line_status_updated',
                'res_model': 'pos.order.line',
                'line_id': order_line_id,  # ✅ THÊM line_id
                'old_status': old_status,   # ✅ THÊM old_status
                'new_status': new_status,   # ✅ THÊM new_status
                'order_id': order_line.order_id.id,  # ✅ THÊM order_id
                'timestamp': datetime.now().isoformat(),  # ✅ THÊM timestamp
            }
            
            self.env["bus.bus"]._sendone(channel_name, bus_type, payload_data)

            return {'success': True}

        except Exception as e:
            _logger.error(f"❌ Lỗi cập nhật trạng thái order line {order_line_id}: {str(e)}")
            return {'success': False, 'error': str(e)}

    @api.model
    def update_order_lines_status_batch(self, order_line_ids, new_status):
        """Cập nhật trạng thái cho nhiều sản phẩm cùng lúc và gửi thông báo"""
        import logging
        from datetime import datetime
        _logger = logging.getLogger(__name__)

        try:
            lines = self.env["pos.order.line"].browse(order_line_ids)
            valid_lines = lines.exists()
            
            if not valid_lines:
                return {'success': False, 'error': 'Không tìm thấy sản phẩm nào'}

            # Lưu danh sách order_ids để kiểm tra hoàn thành đơn sau
            order_ids = valid_lines.mapped('order_id').ids

            # Cập nhật trạng thái
            valid_lines.write({'trcf_order_status': new_status})

            # Kiểm tra và cập nhật trạng thái đơn hàng (đơn nào xong hết thì auto complete)
            for order_id in set(order_ids):
                self.check_order_done(order_id)

            # Gửi thông báo bus cho từng line (hoặc có thể gom lại nếu cần tối ưu hơn)
            # Hiện tại gửi từng line để UI hiện tại của client (onBusMessage) dễ xử lý
            for line in valid_lines:
                channel_name = 'pos_order_line_status_updated'
                bus_type = 'notification'
                payload_data = {
                    'message': 'pos_order_line_status_updated',
                    'res_model': 'pos.order.line',
                    'line_id': line.id,
                    'new_status': new_status,
                    'order_id': line.order_id.id,
                    'timestamp': datetime.now().isoformat(),
                }
                self.env["bus.bus"]._sendone(channel_name, bus_type, payload_data)

            return {'success': True, 'count': len(valid_lines)}

        except Exception as e:
            _logger.error(f"❌ Lỗi cập nhật hàng loạt order lines: {str(e)}")
            return {'success': False, 'error': str(e)}


    @api.model
    def check_order_done(self, order_id):
        """Kiểm tra và cập nhật trạng thái đơn hàng thành done nếu tất cả order lines đều ready"""
        
        import logging
        from datetime import datetime
        _logger = logging.getLogger(__name__)
        
        try:
            order = self.env['pos.order'].browse(order_id)
            
            if order and order.lines:
                # Đếm số line không phải 'ready'
                not_ready_count = len(order.lines.filtered(lambda line: line.trcf_order_status != 'ready'))
                
                if not_ready_count == 0:
                    # ✅ TẤT CẢ MÓN ĐÃ XONG → AUTO COMPLETE ĐƠN
                    old_status = order.trcf_order_status
                    order.write({'trcf_order_status': 'done'})
                    
                    # ✅ GỬI BUS MESSAGE ĐỂ UPDATE UI
                    channel_name = 'pos_order_status_updated'
                    bus_type = 'notification'
                    payload_data = {
                        'message': 'pos_order_status_updated',
                        'res_model': 'pos.order',
                        'order_id': order_id,
                        'old_status': old_status,
                        'new_status': 'done',
                        'config_id': order.config_id.id,
                        'order_name': order.display_name,
                        'timestamp': datetime.now().isoformat(),
                        'auto_completed': True,  # ✅ Đánh dấu là auto-complete
                    }
                    
                    self.env["bus.bus"]._sendone(channel_name, bus_type, payload_data)
                    
                    return True
            return False
            
        except Exception as e:
            _logger.error(f"❌ Lỗi kiểm tra order {order_id}: {str(e)}")
            return False