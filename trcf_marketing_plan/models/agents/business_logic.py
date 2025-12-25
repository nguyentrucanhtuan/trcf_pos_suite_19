# -*- coding: utf-8 -*-
"""
Business Logic - Tools cho Marketing Agent
"""
from datetime import timedelta
from odoo import fields
import json


def get_customer_persona(env) -> dict:
    """Lấy Customer Persona từ Settings"""
    persona = env['ir.config_parameter'].sudo().get_param(
        'trcf.marketing.content.customer_persona', ''
    )
    if not persona:
        return {'status': 'empty', 'message': '⚠️ Chưa cấu hình Customer Persona trong Settings'}
    return {'status': 'success', 'persona': persona}


def get_brand_key(env) -> dict:
    """Lấy Brand Key từ Settings"""
    brand_key = env['ir.config_parameter'].sudo().get_param(
        'trcf.marketing.content.brand_key', ''
    )
    if not brand_key:
        return {'status': 'empty', 'message': '⚠️ Chưa cấu hình Brand Key trong Settings'}
    return {'status': 'success', 'brand_key': brand_key}


def get_customer_journey(env) -> dict:
    """Lấy Customer Journey từ Settings"""
    journey = env['ir.config_parameter'].sudo().get_param(
        'trcf.marketing.content.customer_journey', ''
    )
    if not journey:
        return {'status': 'empty', 'message': '⚠️ Chưa cấu hình Customer Journey trong Settings'}
    return {'status': 'success', 'journey': journey}


def get_business_goals(env) -> dict:
    """Lấy Business Goals từ Settings"""
    goals = env['ir.config_parameter'].sudo().get_param(
        'trcf.marketing.content.goals_current', ''
    )
    if not goals:
        return {'status': 'empty', 'message': '⚠️ Chưa cấu hình Business Goals trong Settings'}
    return {'status': 'success', 'goals': goals}


def get_trending_products(env, limit=5) -> dict:
    """Lấy top sản phẩm bán chạy từ POS"""
    try:
        today = fields.Date.today()
        start_date = today - timedelta(days=7)
        
        order_lines = env['pos.order.line'].sudo().search([
            ('order_id.date_order', '>=', start_date),
            ('order_id.state', 'in', ['paid', 'done'])
        ])
        
        product_stats = {}
        for line in order_lines:
            pid = line.product_id.id
            name = line.product_id.name
            if pid not in product_stats:
                product_stats[pid] = {'name': name, 'qty': 0}
            product_stats[pid]['qty'] += line.qty
        
        trending = sorted(
            product_stats.values(),
            key=lambda x: x['qty'],
            reverse=True
        )[:limit]
        
        return {
            'status': 'success',
            'trending_products': trending,
            'period': '7 ngày qua'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def get_approved_content_history(env, limit=10) -> dict:
    """Lấy content đã duyệt để AI học phong cách"""
    try:
        history = env['trcf.marketing.content'].get_approved_history(limit)
        return {
            'status': 'success',
            'approved_content': history,
            'count': len(history),
            'instruction': 'Đây là content ĐÃ ĐƯỢC DUYỆT. Học phong cách này!'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def get_rejected_content_history(env, limit=10) -> dict:
    """Lấy content bị từ chối để AI tránh lặp"""
    try:
        history = env['trcf.marketing.content'].get_rejected_history(limit)
        return {
            'status': 'success',
            'rejected_content': history,
            'count': len(history),
            'instruction': 'Đây là content BỊ TỪ CHỐI. TRÁNH tạo nội dung tương tự!'
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
