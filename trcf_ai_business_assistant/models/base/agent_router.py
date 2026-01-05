# -*- coding: utf-8 -*-
import importlib
import logging
from . import agent_registry

_logger = logging.getLogger(__name__)

def route(env, message):
    """Điều hướng tin nhắn đến Agent phù hợp"""
    agent_key, agent_config = agent_registry.get_agent_by_keyword(message)
    
    _logger.info(f"🤖 Routing message to agent: {agent_key}")
    
    try:
        # Dynamic import
        module = importlib.import_module(agent_config['module_path'])
        agent_class = getattr(module, agent_config['class_name'])
        
        # Khởi tạo và truy vấn
        agent_instance = agent_class(env)
        return agent_instance.query(message)
        
    except Exception as e:
        _logger.error(f"❌ Router error: {e}", exc_info=True)
        return f"⚠️ Lỗi router: {str(e)}"
