# -*- coding: utf-8 -*-
"""
PNL ANALYST - Business Logic
✅ CÓ THỂ COMPILE VỚI CYTHON
"""
import logging
from datetime import datetime, timedelta
from odoo import fields

_logger = logging.getLogger(__name__)

def _get_date_range(period='month'):
    """Xác định khoảng thời gian dựa trên period"""
    today = fields.Date.today()
    
    if period == 'day':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=today.weekday())
        end_date = today
    elif period == 'month':
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = today.replace(day=1)
        end_date = today
        
    return start_date, end_date

def get_pnl_report(env, period: str = 'month') -> str:
    """
    Lấy báo cáo P&L (Lợi nhuận & Lỗ) chi tiết.
    
    Args:
        period: Khoảng thời gian ('day', 'week', 'month')
        
    Returns:
        Báo cáo P&L chi tiết dưới dạng Markdown
    """
    try:
        start_date, end_date = _get_date_range(period)
        
        # 1. Doanh thu (POS)
        pos_orders = env['pos.order'].sudo().search([
            ('date_order', '>=', fields.Datetime.to_string(datetime.combine(start_date, datetime.min.time()))),
            ('date_order', '<=', fields.Datetime.to_string(datetime.combine(end_date, datetime.max.time()))),
            ('state', 'in', ['paid', 'done', 'invoiced'])
        ])
        revenue = sum(pos_orders.mapped('amount_total'))
        order_count = len(pos_orders)
        
        # Đếm số lượng sản phẩm bán ra
        product_count = 0
        for order in pos_orders:
            product_count += sum(order.lines.mapped('qty'))
        
        # 2. Giá vốn (COGS - Purchase)
        purchases = env['purchase.order'].sudo().search([
            ('date_approve', '>=', fields.Datetime.to_string(datetime.combine(start_date, datetime.min.time()))),
            ('date_approve', '<=', fields.Datetime.to_string(datetime.combine(end_date, datetime.max.time()))),
            ('state', 'in', ['purchase', 'done'])
        ])
        cogs = sum(purchases.mapped('amount_total'))
        
        # 3. Chi phí hoạt động (Expense)
        # Giả định model trcf.expense tồn tại như trong code dashboard
        expenses = env['trcf.expense'].sudo().search([
            ('create_date', '>=', fields.Datetime.to_string(datetime.combine(start_date, datetime.min.time()))),
            ('create_date', '<=', fields.Datetime.to_string(datetime.combine(end_date, datetime.max.time()))),
            ('state', 'in', ['approved', 'paid'])
        ])
        opex = sum(expenses.mapped('trcf_amount'))
        
        # 4. Tính toán lợi nhuận
        gross_profit = revenue - cogs
        net_profit = gross_profit - opex
        
        # Margins
        gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
        net_margin = (net_profit / revenue * 100) if revenue > 0 else 0
        
        # Format output - Đơn giản hóa để AI dễ chuyển đổi sang checklist
        currency = env.company.currency_id.symbol or 'đ'
        
        period_label = 'ngày'
        if period == 'week':
            period_label = 'tuần'
        elif period == 'month':
            period_label = 'tháng'
            
        lines = [
            f"Kỳ báo cáo: {period_label} từ {start_date.strftime('%d/%m/%Y')} đến {end_date.strftime('%d/%m/%Y')}",
            f"Tổng doanh thu: {revenue:,.0f}{currency}",
            f"Số lượng bán: {int(product_count)} sản phẩm",
            f"Số đơn hàng: {order_count} đơn hàng",
            f"Giá vốn (COGS): {cogs:,.0f}{currency}",
            f"Chi phí (Opex): {opex:,.0f}{currency}",
            f"Lợi nhuận gộp: {gross_profit:,.0f}{currency} (Biên lợi nhuận: {gross_margin:.1f}%)",
            f"Lợi nhuận ròng: {net_profit:,.0f}{currency} (Biên lợi nhuận: {net_margin:.1f}%)",
        ]
        
        if net_profit < 0:
            lines.append("⚠️ Cảnh báo: Hoạt động kinh doanh đang ghi nhận lỗ trong kỳ này.")
        elif net_margin < 10:
            lines.append("⚠️ Lưu ý: Biên lợi nhuận ròng thấp hơn 10%, cần xem xét tối ưu chi phí.")
            
        return "\n".join(lines)
        
    except Exception as e:
        _logger.error(f"Error in get_pnl_report: {e}", exc_info=True)
        return f"⚠️ Lỗi khi trích xuất báo cáo P&L: {str(e)}"

