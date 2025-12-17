# -*- coding: utf-8 -*-
"""
BUSINESS AGENT - Google ADK Agent
❌ KHÔNG COMPILE

Sử dụng Google ADK với asyncio wrapper
"""
import logging
import os
import asyncio
from datetime import timedelta

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner, types

from . import business_logic
from . import prompts

_logger = logging.getLogger(__name__)


class BusinessAgent:
    """
    Trợ lý Kinh doanh - Google ADK
    
    Chức năng:
    - Tra cứu doanh thu
    - Phân tích kinh doanh
    """
    
    def __init__(self, env):
        self.env = env
        self.model_name = "gemini-2.5-flash-lite"
    
    def _get_date_context(self):
        """Lấy context ngày tháng"""
        from odoo import fields
        
        today = fields.Date.today()
        yesterday = today - timedelta(days=1)
        week_start = today - timedelta(days=today.weekday())
        month_start = today.replace(day=1)
        
        return today, yesterday, week_start, month_start
    
    def _create_tools(self):
        """
        Tạo tools cho ADK Agent
        
        Returns:
            list: Danh sách Python functions
        """
        env = self.env
        
        def get_revenue(start_date: str = "", end_date: str = "") -> str:
            """
            Lấy doanh thu bán hàng trong khoảng thời gian.
            
            Gọi tool này khi user hỏi về doanh thu, bán hàng, revenue.
            
            Args:
                start_date: Ngày bắt đầu (DD-MM-YYYY), để trống = hôm nay
                end_date: Ngày kết thúc (DD-MM-YYYY), để trống = hôm nay
                
            Returns:
                Báo cáo doanh thu chi tiết
            """
            try:
                data = business_logic.get_revenue(
                    env,
                    start_date=start_date if start_date else None,
                    end_date=end_date if end_date else None
                )
                return business_logic.format_revenue_output(data)
            except Exception as e:
                _logger.error(f"❌ get_revenue error: {e}", exc_info=True)
                return f"⚠️ Lỗi: {str(e)}"
        
        return [get_revenue]
    
    def create_agent(self):
        """
        Tạo Google ADK Agent instance
        
        Returns:
            Agent: ADK Agent đã được cấu hình
        """
        # Lấy API key
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'trcf.gemini_api_key', ''
        )
        if not api_key:
            raise ValueError("Chưa cấu hình Google API Key")
        
        os.environ['GOOGLE_API_KEY'] = api_key
        
        # Lấy date context
        today, _, _, _ = self._get_date_context()
        
        # Tạo system instruction
        system_instruction = prompts.get_system_instruction(
            today.strftime('%d-%m-%Y')
        )
        
        # Tạo tools
        tools = self._create_tools()
        
        # Tạo ADK Agent
        agent = Agent(
            name="business_assistant",
            model=self.model_name,
            tools=tools,
            instruction=system_instruction
        )
        
        return agent
    
    async def _run_agent_async(self, agent, message):
        """Run agent async với InMemoryRunner"""
        runner = InMemoryRunner(
            app_name="trcf_business_assistant",
            agent=agent
        )
        
        # Tạo session mới
        user_id = "odoo_user"
        session_id = f"session_{id(self)}_{id(message)}"
        
        await runner.session_service.create_session(
            app_name="trcf_business_assistant",
            user_id=user_id,
            session_id=session_id
        )
        
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
        ):
            # Chỉ lấy text từ model responses
            if hasattr(event, 'content') and event.content:
                content = event.content
                if hasattr(content, 'role') and content.role == 'model':
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            if hasattr(part, 'text') and part.text:
                                response_text = part.text
        
        return response_text if response_text else "⚠️ Không có phản hồi"
    
    def query(self, message):
        """Xử lý query từ user (sync wrapper)"""
        try:
            agent = self.create_agent()
            response = asyncio.run(self._run_agent_async(agent, message))
            return response
                
        except ValueError as e:
            return f"⚠️ {str(e)}"
        except Exception as e:
            error_msg = str(e)
            
            # Quota exceeded
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                return (
                    "⚠️ **Google API Quota vượt giới hạn**\n\n"
                    "Bạn đã dùng hết quota miễn phí.\n\n"
                    "🔗 Kiểm tra: https://ai.dev/usage?tab=rate-limit\n"
                    "📊 Quota info: https://ai.google.dev/gemini-api/docs/rate-limits\n\n"
                    "**Giải pháp:** Đợi 1-2 phút hoặc nâng cấp paid plan"
                )
            
            # Model not found
            if "404" in error_msg or "not found" in error_msg.lower():
                return f"⚠️ Model `{self.model_name}` không khả dụng. Kiểm tra lại cấu hình."
            
            _logger.error(f"❌ Agent error: {e}", exc_info=True)
            return f"⚠️ Lỗi: {error_msg[:200]}..." if len(error_msg) > 200 else f"⚠️ Lỗi: {error_msg}"
