# -*- coding: utf-8 -*-
"""
DRINK CREATIVE AGENT - Single Agent với Odoo Tools
❌ KHÔNG COMPILE
"""
import logging
import os
import asyncio

from google.adk.agents import Agent
from google.adk.runners import Runner, types
from google.adk.sessions import InMemorySessionService

from odoo import fields
from . import business_logic, prompts

_logger = logging.getLogger(__name__)

APP_NAME = "trcf_creative_agent"

class DrinkCreativeAgent:
    """
    Agent Sáng tạo Đồ uống - Tối ưu quota.
    Không dùng sub-agents, chỉ dùng tools trực tiếp.
    """
    
    def __init__(self, env):
        self.env = env
        self.model_name = "gemini-2.0-flash-lite"
    
    def _setup_api_key(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param('trcf.gemini_api_key', '')
        if not api_key:
            raise ValueError("Chưa cấu hình Google API Key (trcf.gemini_api_key)")
        os.environ['GOOGLE_API_KEY'] = api_key

    def _create_tools(self):
        """Tạo tools truy vấn Odoo"""
        env = self.env
        
        def get_trending_pos_drinks() -> dict:
            """Lấy top món bán chạy nhất từ dữ liệu POS của quán."""
            data = business_logic.get_trending_drinks(env)
            return {"status": "success", "data": business_logic.format_trending_output(data)}

        def get_shop_fundamentals() -> dict:
            """Lấy giá vốn nguyên liệu và các BoM mẫu từ Odoo."""
            data = business_logic.get_shop_fundamentals(env)
            formatted = business_logic.format_fundamentals(data)
            return {"status": "success", "data": formatted}
            
        def get_barista_conventions() -> dict:
            """Lấy các quy tắc pha chế từ Settings."""
            data = business_logic.get_barista_conventions(env)
            formatted = business_logic.format_rules(data)
            return {"status": "success", "data": formatted}

        return [get_trending_pos_drinks, get_shop_fundamentals, get_barista_conventions]

    def create_agent(self):
        """Tạo Single Agent với Odoo tools"""
        self._setup_api_key()
        today = fields.Date.today().strftime('%d-%m-%Y')
        
        instruction = f"""Bạn là Chuyên gia Sáng tạo Đồ uống Coffee Tree ☕ (Hôm nay: {today})

TOOLS:
• get_trending_pos_drinks → Món bán chạy tại quán
• get_shop_fundamentals → Giá nguyên liệu & BoM
• get_barista_conventions → Quy tắc pha chế

KHI NÀO DÙNG TOOLS:
- Hỏi "xu hướng/trend/bán chạy" → get_trending_pos_drinks
- Sáng tạo món mới → get_trending_pos_drinks + get_shop_fundamentals + get_barista_conventions
- Hỏi giá vốn → get_shop_fundamentals

OUTPUT:
- Nhiệt tình, dùng emoji ☕🍵
- Món mới: Công thức + Giá vốn chi tiết
- Ưu tiên: Khả thi, giá hợp lý, đúng quy tắc"""

        tools = self._create_tools()
        
        return Agent(
            name="drink_creative_assistant",
            model=self.model_name,
            description="Chuyên gia sáng tạo đồ uống",
            instruction=instruction,
            tools=tools
        )
    
    async def _run_async(self, agent, message):
        session_service = InMemorySessionService()
        user_id = "odoo_user"
        session_id = f"session_creative_{id(message)}"
        
        await session_service.create_session(
            app_name=APP_NAME, 
            user_id=user_id, 
            session_id=session_id
        )
        
        runner = Runner(
            agent=agent, 
            app_name=APP_NAME, 
            session_service=session_service
        )
        
        content = types.Content(
            role='user', 
            parts=[types.Part(text=message)]
        )
        
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id, 
            session_id=session_id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response_text = event.content.parts[0].text
                break
        
        return response_text or "⚠️ Không có phản hồi."

    def query(self, message):
        """Entry point từ Odoo Discuss"""
        try:
            agent = self.create_agent()
            return asyncio.run(self._run_async(agent, message))
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                return "⚠️ Quota Gemini API đã hết. Hãy đợi 1 phút."
            _logger.error(f"❌ Creative Agent Error: {e}", exc_info=True)
            return f"⚠️ Lỗi: {error_msg[:200]}"
