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
    """
    Lấy danh sách món bán chạy nhất trong N ngày
    
    Args:
        env: Odoo environment
        limit: Số lượng món trả về (default: 5)
        days: Số ngày tính trend (default: 30)
        
    Returns:
        list: [{'name': str, 'qty_sold': int, 'revenue': float}]
    """
    try:
        from odoo import fields
        
        # Lấy trend period từ settings
        trend_days = int(env['ir.config_parameter'].sudo().get_param(
            'trcf_ai.drink_trend_period', days
        ))
        
        today = fields.Date.today()
        start_date = today - timedelta(days=trend_days)
        
        _logger.info(f"📊 Getting trending drinks: {start_date} → {today}")
        
        # Query pos.order.line grouped by product
        order_lines = env['pos.order.line'].sudo().search([
            ('order_id.date_order', '>=', start_date),
            ('order_id.date_order', '<=', today),
            ('order_id.state', 'in', ['paid', 'done', 'invoiced'])
        ])
        
        # Aggregate by product
        product_stats = {}
        for line in order_lines:
            product_id = line.product_id.id
            if product_id not in product_stats:
                product_stats[product_id] = {
                    'name': line.product_id.name,
                    'qty_sold': 0,
                    'revenue': 0.0
                }
            product_stats[product_id]['qty_sold'] += line.qty
            product_stats[product_id]['revenue'] += line.price_subtotal_incl
        
        # Sort by qty_sold DESC
        sorted_products = sorted(
            product_stats.values(),
            key=lambda x: x['qty_sold'],
            reverse=True
        )[:limit]
        
        _logger.info(f"✅ Found {len(sorted_products)} trending drinks")
        return sorted_products
        
    except Exception as e:
        _logger.error(f"❌ Error getting trending drinks: {e}", exc_info=True)
        return []


def get_drink_recipe(env, product_name):
    """
    Lấy công thức của món từ BOM
    
    Args:
        env: Odoo environment
        product_name: Tên món cần tra
        
    Returns:
        dict: {
            'name': str,
            'ingredients': [{'name': str, 'qty': float, 'unit': str, 'cost': float}],
            'total_cost': float
        }
    """
    try:
        # Tìm product theo tên
        products = env['product.product'].sudo().search([
            ('name', 'ilike', product_name)
        ], limit=5)
        
        if not products:
            return {'error': f"Không tìm thấy sản phẩm: {product_name}"}
        
        # Lấy product đầu tiên
        product = products[0]
        
        # Tìm BOM của product
        bom = env['mrp.bom'].sudo().search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id)
        ], limit=1)
        
        if not bom:
            # Không có BOM, trả về thông tin cơ bản
            return {
                'name': product.name,
                'ingredients': [],
                'total_cost': product.standard_price,
                'note': 'Không có công thức BOM'
            }
        
        # Lấy ingredients từ BOM lines
        ingredients = []
        total_cost = 0.0
        
        for line in bom.bom_line_ids:
            ingredient = {
                'name': line.product_id.name,
                'qty': line.product_qty,
                'unit': line.product_uom_id.name,
                'cost': line.product_id.standard_price * line.product_qty
            }
            ingredients.append(ingredient)
            total_cost += ingredient['cost']
        
        result = {
            'name': product.name,
            'ingredients': ingredients,
            'total_cost': total_cost
        }
        
        _logger.info(f"✅ Recipe for {product.name}: {len(ingredients)} ingredients")
        return result
        
    except Exception as e:
        _logger.error(f"❌ Error getting recipe: {e}", exc_info=True)
        return {'error': str(e)}


def get_creativity_rules(env):
    """
    Lấy quy tắc pha chế từ Settings
    
    Args:
        env: Odoo environment
        
    Returns:
        str: Quy tắc pha chế
    """
    return env['ir.config_parameter'].sudo().get_param(
        'trcf_ai.drink_creativity_rules', 
        ''
    )


def format_trending_output(data):
    """
    Format danh sách trending thành text đẹp
    
    Args:
        data: list of dicts
        
    Returns:
        str: Formatted text
    """
    if not data:
        return "Không có dữ liệu bán hàng"
    
    lines = ["🔥 **Top món bán chạy:**\n"]
    
    for i, item in enumerate(data, 1):
        lines.append(
            f"{i}. **{item['name']}**\n"
            f"   - Đã bán: {int(item['qty_sold'])} ly\n"
            f"   - Doanh thu: {item['revenue']:,.0f} VND"
        )
    
    return "\n".join(lines)


def format_recipe_output(recipe):
    """
    Format công thức thành text đẹp
    
    Args:
        recipe: dict with name, ingredients, total_cost
        
    Returns:
        str: Formatted text
    """
    if 'error' in recipe:
        return f"⚠️ {recipe['error']}"
    
    lines = [f"📝 **Công thức: {recipe['name']}**\n"]
    
    if recipe.get('note'):
        lines.append(f"ℹ️ {recipe['note']}\n")
    
    if recipe['ingredients']:
        lines.append("**Nguyên liệu:**")
        for ing in recipe['ingredients']:
            lines.append(
                f"  • {ing['name']}: {ing['qty']} {ing['unit']} "
                f"(~{ing['cost']:,.0f} VND)"
            )
        lines.append(f"\n**Giá vốn ước tính:** {recipe['total_cost']:,.0f} VND")
    else:
        lines.append("Chưa có thông tin nguyên liệu chi tiết")
    
    return "\n".join(lines)
