# -*- coding: utf-8 -*-
"""
BUSINESS AGENT - Business Logic
✅ CÓ THỂ COMPILE VỚI CYTHON

Refactor từ trcf_business_functions.py
"""
import logging
from datetime import timedelta

_logger = logging.getLogger(__name__)


def get_revenue(env, start_date=None, end_date=None):
    """
    Lấy doanh thu từ POS Order
    
    Args:
        env: Odoo environment
        start_date: Ngày bắt đầu (DD-MM-YYYY)
        end_date: Ngày kết thúc (DD-MM-YYYY)
        
    Returns:
        dict: {total, count, average_per_order, ...}
    """
    try:
        from odoo import fields
        
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
        pos_orders = env['pos.order'].sudo().search([
            ('date_order', '>=', start),
            ('date_order', '<=', end + timedelta(days=1)),
            ('state', 'in', ['paid', 'done', 'invoiced'])
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
            'currency': env.company.currency_id.name,
            'start_date': start.strftime('%d/%m/%Y'),
            'end_date': end.strftime('%d/%m/%Y'),
            'days': days_count,
            'average_per_day': float(average_per_day)
        }
        
        _logger.info(f"✅ POS: {total_revenue:,.0f} VND ({total_count} đơn)")
        
        return result
        
    except Exception as e:
        _logger.error(f"❌ Lỗi khi lấy doanh thu: {e}", exc_info=True)
        return {'error': str(e)}


def format_revenue_output(data):
    """
    Format doanh thu thành text đẹp
    
    Args:
        data: dict từ get_revenue()
        
    Returns:
        str: Formatted text
    """
    if 'error' in data:
        return f"⚠️ {data['error']}"
    
    lines = [
        f"💰 **Báo cáo doanh thu**",
        f"📅 Từ {data['start_date']} đến {data['end_date']}",
        f"",
        f"- Tổng doanh thu: **{data['total']:,.0f} {data['currency']}**",
        f"- Số đơn hàng: **{data['count']}** đơn",
        f"- TB/đơn: {data['average_per_order']:,.0f} {data['currency']}",
        f"- TB/ngày: {data['average_per_day']:,.0f} {data['currency']}"
    ]
    
    return "\n".join(lines)
