# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)

AGENTS = {
    'pnl_analyst': {
        'name': 'Trợ lý P&L & Tài chính',
        'keywords': [
            'pnl', 'lợi nhuận', 'lỗ', 'chi phí', 'tài chính', 
            'giá vốn', 'cogs', 'opex', 'kinh doanh'
        ],
        'module_path': 'odoo.addons.trcf_ai_business_assistant.models.agents.pnl_analyst.agent',
        'class_name': 'PnlAnalystAgent',
    }
}

def get_all_agents():
    return AGENTS

def get_agent_by_keyword(text):
    text_lower = text.lower()
    for key, config in AGENTS.items():
        for keyword in config['keywords']:
            if keyword.lower() in text_lower:
                return (key, config)
    return ('pnl_analyst', AGENTS['pnl_analyst'])
