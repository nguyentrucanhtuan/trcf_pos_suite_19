# -*- coding: utf-8 -*-
from odoo import models, api, fields
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


class TrcfBusinessFunctions(models.AbstractModel):
    """Các hàm xử lý dữ liệu kinh doanh cho AI Assistant"""
    _name = 'trcf.business.functions'
    _description = 'Business Functions for AI Assistant'

    def _get_function_declarations(self):
        """Định nghĩa các functions cho Gemini"""
        
        # PHẢI KHAI BÁO CÁC BIẾN TRƯỚC KHI SỬ DỤNG
        today = fields.Date.today()
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        return [
            {
                "name": "get_revenue",
                "description": f"""Lấy doanh thu bán hàng trong khoảng thời gian từ start_date đến end_date.

HÔM NAY: {today.strftime('%d-%m-%Y')}

CHỨC NĂNG:
- Tính tổng doanh thu từ đơn hàng đã xác nhận (state='sale'/'done')
- Đếm số lượng đơn hàng
- Tính trung bình doanh thu/ngày

KHI NÀO GỌI FUNCTION:
✓ "Doanh thu hôm nay?" → start_date='{today.strftime('%d-%m-%Y')}', end_date='{today.strftime('%d-%m-%Y')}'
✓ "Hôm qua bán được bao nhiêu?" → start_date='{yesterday.strftime('%d-%m-%Y')}', end_date='{yesterday.strftime('%d-%m-%Y')}'
✓ "Tuần này doanh thu thế nào?" → start_date='{week_start.strftime('%d-%m-%Y')}', end_date='{today.strftime('%d-%m-%Y')}'
✓ "Tháng này bán được bao nhiêu?" → start_date='{month_start.strftime('%d-%m-%Y')}', end_date='{today.strftime('%d-%m-%Y')}'

KẾT QUẢ:
- total: Tổng doanh thu (float)
- count: Số đơn hàng (int)
- currency: Đơn vị tiền (VND)
- days: Số ngày
- average_per_day: Trung bình/ngày

LƯU Ý:
- Nếu không truyền tham số → mặc định lấy hôm nay
- Format: DD-MM-YYYY (14-10-2025)""",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": f"Ngày bắt đầu (DD-MM-YYYY). Nếu user hỏi 'hôm nay' thì dùng: {today.strftime('%d-%m-%Y')}"
                        },
                        "end_date": {
                            "type": "string",
                            "description": f"Ngày kết thúc (DD-MM-YYYY). Nếu user hỏi 'hôm nay' thì dùng: {today.strftime('%d-%m-%Y')}"
                        }
                    },
                    "required": []
                }
            }
        ]

    @api.model
    def _get_revenue(self, start_date=None, end_date=None):
        """Lấy doanh thu từ POS Order"""
        try:
            today = fields.Date.today()
            
            # Xử lý tham số
            if not start_date:
                start_date = today.strftime('%d-%m-%Y')
            if not end_date:
                end_date = today.strftime('%d-%m-%Y')
            
            # Convert DD-MM-YYYY to date object
            start = fields.Date.from_string(
                f"{start_date[6:]}-{start_date[3:5]}-{start_date[0:2]}"
            )
            end = fields.Date.from_string(
                f"{end_date[6:]}-{end_date[3:5]}-{end_date[0:2]}"
            )
            
            _logger.info(f"📅 Lấy doanh thu POS từ {start} đến {end}")
            
            # Lấy doanh thu từ POS Order
            pos_orders = self.env['pos.order'].sudo().search([
                ('date_order', '>=', start),
                ('date_order', '<=', end + timedelta(days=1)),
                ('state', 'in', ['paid', 'done', 'invoiced'])  # Chỉ lấy đơn đã thanh toán
            ])
            
            # Tính toán
            total_revenue = sum(pos_orders.mapped('amount_total'))
            total_count = len(pos_orders)
            average_per_order = total_revenue / total_count if total_count > 0 else 0
            
            # Tính số ngày và trung bình/ngày
            days_count = (end - start).days + 1
            average_per_day = total_revenue / days_count if days_count > 0 else 0
            
            result = {
                'total': float(total_revenue),
                'count': total_count,
                'average_per_order': float(average_per_order),
                'currency': self.env.company.currency_id.name,
                'start_date': start.strftime('%d/%m/%Y'),
                'end_date': end.strftime('%d/%m/%Y'),
                'days': days_count,
                'average_per_day': float(average_per_day)
            }
            
            _logger.info(f"✅ POS: {total_revenue:,.0f} VND ({total_count} đơn, TB: {average_per_order:,.0f}/đơn)")
            
            return result
            
        except Exception as e:
            _logger.error(f"❌ Lỗi khi lấy doanh thu POS: {e}", exc_info=True)
            return {'error': str(e)}