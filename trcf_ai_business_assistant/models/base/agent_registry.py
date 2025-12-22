# -*- coding: utf-8 -*-
"""
AGENT REGISTRY - Đăng ký và quản lý các agents
"""
import logging

_logger = logging.getLogger(__name__)

# Registry lưu thông tin các agents
AGENTS = {
    'drink_creative': {
        'name': 'Trợ lý Sáng tạo Thức uống',
        'keywords': [
            'sáng tạo', 'công thức', 'pha chế', 'nguyên liệu', 'recipe',
            'giá vốn', 'bom', 'quy tắc', 'món mới', 'xu hướng', 'trend',
            'matcha', 'latte', 'cà phê', 'trà', 'sinh tố', 'smoothie'
        ],
        'module_path': 'odoo.addons.trcf_ai_business_assistant.models.agents.drink_creative.agent',
        'class_name': 'DrinkCreativeAgent',
    },
    'business': {
        'name': 'Trợ lý Kinh doanh',
        'keywords': [
            'doanh thu', 'bán hàng', 'revenue', 'đơn hàng', 
            'tổng', 'hôm nay', 'hôm qua', 'tuần', 'tháng'
        ],
        'module_path': 'odoo.addons.trcf_ai_business_assistant.models.agents.business.agent',
        'class_name': 'BusinessAgent',
    }
}


def get_all_agents():
    """Lấy danh sách tất cả agents đã đăng ký"""
    return AGENTS


def get_agent_by_keyword(text):
    """
    Tìm agent phù hợp dựa trên keywords trong message
    
    Args:
        text: Nội dung tin nhắn từ user
        
    Returns:
        tuple: (agent_key, agent_config) hoặc (None, None)
    """
    text_lower = text.lower()
    
    best_match = None
    best_score = 0
    
    for agent_key, agent_config in AGENTS.items():
        score = 0
        for keyword in agent_config['keywords']:
            if keyword.lower() in text_lower:
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = (agent_key, agent_config)
    
    if best_match:
        _logger.info(f"🎯 Matched agent: {best_match[0]} (score: {best_score})")
        return best_match
    
    # Default to business agent
    _logger.info("🎯 No match, using default: business")
    return ('business', AGENTS['business'])


def register_agent(key, config):
    """
    Đăng ký agent mới vào registry
    
    Args:
        key: Unique key cho agent
        config: dict với name, keywords, module_path, class_name
    """
    AGENTS[key] = config
    _logger.info(f"✅ Registered agent: {key}")
