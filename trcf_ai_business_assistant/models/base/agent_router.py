# -*- coding: utf-8 -*-
"""
AGENT ROUTER - Điều hướng tin nhắn đến agent phù hợp
"""
import logging
import importlib

from . import agent_registry

_logger = logging.getLogger(__name__)


def route(env, message):
    """
    Điều hướng message đến agent phù hợp và trả về response
    
    Args:
        env: Odoo environment
        message: Nội dung tin nhắn từ user
        
    Returns:
        str: Response từ agent
    """
    try:
        # Tìm agent phù hợp
        agent_key, agent_config = agent_registry.get_agent_by_keyword(message)
        
        if not agent_config:
            return "⚠️ Không tìm thấy agent phù hợp"
        
        _logger.info(f"🚀 Routing to: {agent_config['name']}")
        
        # Dynamic import agent module
        module = importlib.import_module(agent_config['module_path'])
        agent_class = getattr(module, agent_config['class_name'])
        
        # Khởi tạo và query agent
        agent_instance = agent_class(env)
        response = agent_instance.query(message)
        
        return response
        
    except ImportError as e:
        _logger.error(f"❌ Import error: {e}")
        return f"⚠️ Agent chưa được implement: {agent_key}"
        
    except Exception as e:
        _logger.error(f"❌ Router error: {e}", exc_info=True)
        return f"⚠️ Lỗi xử lý: {str(e)}"
