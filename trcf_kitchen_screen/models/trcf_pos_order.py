from odoo import api, fields, models
from datetime import datetime
import pytz
import pprint
import logging

class TrcfPosOrder(models.Model):
    _inherit = "pos.order"

    trcf_order_status = fields.Selection(string="Order Status",
                                    selection=[("draft", "Đơn mới"),
                                               ("waiting", "Đang làm"),
                                               ("done", "Hoàn thành"),
                                               ("cancel", "Huỷ")],
                                    default='draft',
                                    help='Trạng thái của đơn hàng')

    _logger = logging.getLogger(__name__)

    @api.model_create_multi
    def create(self, vals_list):

        for vals in vals_list:
            if not vals.get("trcf_order_status"):
                vals["trcf_order_status"] = 'draft'

        orders = super().create(vals_list)

        #begin: send message
        channel_name = 'pos_order_created'
        bus_type = 'notification'
        payload_data = {
            'message': 'pos_order_created',
            'res_model': 'pos.order',
            'config_id': orders.config_id.id,
        }
        self.env["bus.bus"]._sendone(channel_name, bus_type, payload_data)
        #end: send message

        return orders
    
    @api.model
    def get_orders_by_config_id(self, config_id):

        pos = self.env["pos.order"].search([
                ("config_id", "=", config_id),
                ("session_id.state", "=", "opened")
        ], order="date_order asc")

        pos_lines = pos.lines
        
        values = {
            "orders": pos.read(), 
            "order_lines": pos_lines.read()
        }
        
        return values

    @api.model 
    def get_orders_by_screen_id(self, screen_id): 
        """Lấy đơn hàng đã lọc theo màn hình và danh mục"""
        
        _logger = logging.getLogger(__name__)
        
        # Lấy thông tin màn hình
        screen = self.env['trcf.kitchenscreen'].browse(screen_id)
        
        if not screen.exists():
            return {'orders': [], 'order_lines': [], 'screen_info': {}}
        
        # ✅ Kiểm tra có config không
        if not screen.pos_config_id:
            return {'orders': [], 'order_lines': [], 'screen_info': {}}
        
        config_id = screen.pos_config_id.id  # ✅ Lấy ID trước
        
        # ✅ Dùng config_id (số nguyên) trong search
        pos_orders = self.env["pos.order"].search([
            ("config_id", "=", config_id),
            ("session_id.state", "=", "opened")
        ], order="date_order asc")

        # ✅ LỌC ORDER LINES THEO CATEGORY
        if screen.pos_categ_ids:
            # Lấy danh sách category IDs từ screen
            screen_category_ids = screen.pos_categ_ids.ids

            filtered_lines = self.env["pos.order.line"].search([
                ("order_id", "in", pos_orders.ids),
                ("product_id.pos_categ_ids", "in", screen_category_ids)
            ])
        else: 
            # Nếu screen không có category nào, hiện tất cả
            filtered_lines = pos_orders.lines
        
        values = {
            "orders": pos_orders.read(), 
            "order_lines": filtered_lines.read(),
            "screen_info": {
                "screen_id": screen_id,
                "screen_name": screen.screen_name,
                "categories": screen.pos_categ_ids.mapped('name'),
                "config_id": config_id
            }
        }

        return values
    
    # ✅ THÊM CÁC METHOD MỚI ĐỂ CẬP NHẬT TRẠNG THÁI
    @api.model
    def update_order_status(self, order_id, new_status):
        """Cập nhật trạng thái đơn hàng và gửi thông báo tới tất cả màn hình"""
        try:
            # Tìm đơn hàng
            order = self.env["pos.order"].browse(order_id)
            
            if not order.exists():
                return {'success': False, 'error': 'Đơn hàng không tồn tại'}
            
            # Lưu trạng thái cũ
            old_status = order.trcf_order_status
            
            # Cập nhật trạng thái mới
            order.write({'trcf_order_status': new_status})
            
            self._logger.info(f"✅ Cập nhật đơn hàng {order.display_name} (ID: {order_id}): {old_status} -> {new_status}")
            
            # ✅ GỬI THÔNG BÁO BUS ĐỂN TẤT CẢ MÀN HÌNH
            channel_name = 'pos_order_status_updated'
            bus_type = 'notification'
            payload_data = {
                'message': 'pos_order_status_updated',
                'res_model': 'pos.order',
                'order_id': order_id,
                'old_status': old_status,
                'new_status': new_status,
                'config_id': order.config_id.id,
                'order_name': order.display_name,
                'timestamp': datetime.now().isoformat(),
            }
            
            self.env["bus.bus"]._sendone(channel_name, bus_type, payload_data)
            self._logger.info(f"📡 Đã gửi bus message: {payload_data}")
            
            return {
                'success': True, 
                'order_id': order_id,
                'old_status': old_status,
                'new_status': new_status,
                'order_name': order.display_name,
            }
            
        except Exception as e:
            self._logger.error(f"❌ Lỗi cập nhật trạng thái đơn hàng {order_id}: {str(e)}")
            return {'success': False, 'error': str(e)}
