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
            
        try:
            order_line = self.env["pos.order.line"].browse(order_line_id)

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
            }
            
            self.env["bus.bus"]._sendone(channel_name, bus_type, payload_data)

            return {'success': True}

        except Exception as e:
            self._logger.error(f"❌ Lỗi cập nhật trạng thái đơn hàng {order_line_id}: {str(e)}")
            return {'success': False, 'error': str(e)}


    @api.model
    def check_order_done(self, order_id):
        """Kiểm tra và cập nhật trạng thái đơn hàng thành done nếu tất cả order lines đều ready"""
        try:
            order = self.env['pos.order'].browse(order_id)
            
            if order and order.lines:
                # Đếm số line không phải 'ready'
                not_ready_count = len(order.lines.filtered(lambda line: line.trcf_order_status != 'ready'))
                if not_ready_count == 0:
                    order.write({'trcf_order_status': 'done'})  # ✅ LƯU VÀO DB
                    return True
            return False
            
        except Exception as e:
            self._logger.error(f"❌ Lỗi kiểm tra order {order_id}: {str(e)}")
            return False