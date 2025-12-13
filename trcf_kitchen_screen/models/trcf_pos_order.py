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

        # ✅ GỬI FULL DATA TRONG BUS MESSAGE - TRÁNH FETCH LẠI
        for order in orders:
            # Lấy order lines data
            order_lines_data = []
            for line in order.lines:
                line_data = {
                    'id': line.id,
                    'product_id': [line.product_id.id, line.product_id.name],
                    'product_id_pos_categ_ids': line.product_id.product_tmpl_id.pos_categ_ids.ids,  # ✅ Category IDs để filter
                    'qty': line.qty,
                    'note': line.note or '',
                    'trcf_order_status': line.trcf_order_status,  # ✅ Đúng field name
                    'public_description': line.product_id.product_tmpl_id.public_description or '',
                    'order_id': [order.id, order.name]
                }
                order_lines_data.append(line_data)
            
            # Gửi bus message với full data
            channel_name = 'pos_order_created'
            bus_type = 'notification'
            payload_data = {
                'message': 'pos_order_created',
                'res_model': 'pos.order',
                'config_id': order.config_id.id,
                # ✅ THÊM FULL ORDER DATA
                'order_data': {
                    'id': order.id,
                    'name': order.name,
                    'pos_reference': order.pos_reference,
                    'date_order': order.date_order.isoformat() if order.date_order else None,
                    'trcf_order_status': order.trcf_order_status,
                    'amount_total': order.amount_total,
                    'partner_id': [order.partner_id.id, order.partner_id.name] if order.partner_id else False,
                },
                'order_lines': order_lines_data,
                'timestamp': datetime.now().isoformat(),  # ✅ Thêm timestamp để tracking
            }
            self.env["bus.bus"]._sendone(channel_name, bus_type, payload_data)

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
        """Lấy danh sách đơn hàng theo màn hình kitchen"""
        
        # ✅ Import logging ở đầu function
        import logging
        _logger = logging.getLogger(__name__)
        
        screen = self.env['trcf.kitchenscreen'].browse(screen_id)
        
        if not screen.exists() or not screen.pos_config_id:
            return {'orders': [], 'order_lines': [], 'screen_info': {}}
        
        config_id = screen.pos_config_id.id  # ✅ Lấy ID trước
        
        # ✅ Dùng config_id (số nguyên) trong search
        pos_orders = self.env["pos.order"].search([
            ("config_id", "=", config_id),
            ("session_id.state", "=", "opened")
        ], order="date_order asc")

        # ✅ LỌC ORDER LINES THEO CATEGORY
        
        if screen.pos_categ_ids:
            # ✅ CÓ CATEGORY → LỌC THEO CATEGORY
            screen_category_ids = screen.pos_categ_ids.ids
            
            filtered_lines = self.env["pos.order.line"].search([
                ("order_id", "in", pos_orders.ids),
                ("product_id.pos_categ_ids", "in", screen_category_ids)
            ])
            
        else: 
            # ✅ KHÔNG CÓ CATEGORY → KHÔNG HIỆN GÌ
            # Screen phải chọn ít nhất 1 category mới hiện món
            filtered_lines = self.env["pos.order.line"]  # Empty recordset
        
        # ✅ THÊM public_description (công thức) vào order_lines
        order_lines_data = []
        for line in filtered_lines:
            line_data = line.read()[0]  # Lấy data mặc định
            # Thêm public_description từ product template
            line_data['public_description'] = line.product_id.product_tmpl_id.public_description or ''
            order_lines_data.append(line_data)
        
        values = {
            "orders": pos_orders.read(), 
            "order_lines": order_lines_data,
            "screen_info": {
                "screen_id": screen_id,
                "screen_name": screen.screen_name,
                "categories": screen.pos_categ_ids.ids,  # ✅ Trả về IDs thay vì names
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
