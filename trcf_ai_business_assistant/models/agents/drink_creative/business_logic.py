# -*- coding: utf-8 -*-
"""
DRINK CREATIVE - Business Logic
✅ CÓ THỂ COMPILE VỚI CYTHON

Chứa các hàm xử lý dữ liệu thức uống từ Odoo
"""
import logging
from datetime import timedelta
_logger = logging.getLogger(__name__)

def get_trending_drinks(env, limit=5, days=30):
    """Lấy danh sách món bán chạy nhất từ POS"""
    try:
        from odoo import fields
        today = fields.Date.today()
        start_date = today - timedelta(days=days)
        
        order_lines = env['pos.order.line'].sudo().search([
            ('order_id.date_order', '>=', start_date),
            ('order_id.state', 'in', ['paid', 'done', 'invoiced'])
        ])
        
        product_stats = {}
        for line in order_lines:
            pid = line.product_id.id
            if pid not in product_stats:
                product_stats[pid] = {'name': line.product_id.name, 'qty': 0, 'rev': 0.0}
            product_stats[pid]['qty'] += line.qty
            product_stats[pid]['rev'] += line.price_subtotal_incl
            
        return sorted(product_stats.values(), key=lambda x: x['qty'], reverse=True)[:limit]
    except Exception as e:
        _logger.error(f"Error logic trending: {e}")
        return []

def get_shop_fundamentals(env):
    """Lấy nguyên liệu và BoM mẫu"""
    try:
        products = env['product.product'].sudo().search([
            ('detailed_type', '=', 'consu'),
            ('standard_price', '>', 0)
        ], limit=15)
        
        ingredient_data = [{'name': p.name, 'price': p.standard_price, 'uom': p.uom_id.name} for p in products]
        
        boms = env['mrp.bom'].sudo().search([], limit=5)
        bom_patterns = [{'product': b.product_tmpl_id.name, 'ingredients': [l.product_id.name for l in b.bom_line_ids]} for b in boms]

        return {'ingredients': ingredient_data, 'patterns': bom_patterns}
    except Exception as e:
        return {'error': str(e)}

def get_barista_conventions(env):
    """Lấy quy tắc pha chế từ Settings"""
    try:
        rules = env['ir.config_parameter'].sudo().get_param('trcf.barista_rules', '')
        if not rules:
            # Fallback to old param name or default
            rules = env['ir.config_parameter'].sudo().get_param('trcf_ai.drink_creativity_rules', 'Pha chế chuẩn TRCF.')
        return {'rules': rules}
    except Exception as e:
        return {'error': str(e)}

def format_trending_output(data):
    if not data: return "Không có dữ liệu bán hàng."
    lines = ["🔥 **Món bán chạy nhất quán:**"]
    for i, item in enumerate(data, 1):
        lines.append(f"{i}. {item['name']} ({int(item['qty'])} ly)")
    return "\n".join(lines)

def format_fundamentals(data):
    if 'error' in data: return f"⚠️ Lỗi Odoo: {data['error']}"
    lines = ["📋 **Dữ liệu thực tế tại quán:**"]
    lines.append("*Nguyên liệu & Giá vốn:*")
    for ing in data['ingredients']:
        lines.append(f"• {ing['name']}: {ing['price']:,.0f}đ/{ing['uom']}")
    return "\n".join(lines)

def format_rules(data):
    if 'error' in data: return f"⚠️ Lỗi: {data['error']}"
    return f"⚖️ **Quy tắc pha chế:** {data['rules']}"
