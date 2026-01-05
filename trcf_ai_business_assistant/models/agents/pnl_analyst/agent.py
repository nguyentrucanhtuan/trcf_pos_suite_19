# -*- coding: utf-8 -*-
import logging
import os
import asyncio
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner, types
from . import business_logic, prompts

_logger = logging.getLogger(__name__)

class PnlAnalystAgent:
    def __init__(self, env):
        self.env = env
        self.model_name = "gemini-flash-latest"

    def create_agent(self):
        # Lấy API key từ Odoo Config
        api_key = self.env['ir.config_parameter'].sudo().get_param('trcf.gemini_api_key', '')
        if not api_key:
            raise ValueError("Chưa cấu hình Google API Key trong Cài đặt.")
        
        os.environ['GOOGLE_API_KEY'] = api_key
        
        from odoo import fields
        today_str = fields.Date.today().strftime('%d/%m/%Y')
        
        # Tools definitions
        def get_pnl_report(period: str = 'month') -> str:
            """
            Lấy báo cáo P&L (Lợi nhuận & Lỗ) chi tiết.
            Args:
                period: Khoảng thời gian ('day', 'week', 'month')
            """
            return business_logic.get_pnl_report(self.env, period)

        return Agent(
            name="pnl_analyst",
            model=self.model_name,
            instruction=prompts.get_system_instruction(today_str),
            tools=[get_pnl_report],
            generate_content_config=types.GenerateContentConfig(
                http_options=types.HttpOptions(
                    retry_options=types.HttpRetryOptions(initial_delay=1, attempts=3)
                )
            )
        )

    async def _run_async(self, agent, message):
        runner = InMemoryRunner(app_name="trcf_pnl_analyst", agent=agent)
        user_id = "odoo_user"
        session_id = f"pnl_session_{id(message)}"
        
        await runner.session_service.create_session(
            app_name="trcf_pnl_analyst", user_id=user_id, session_id=session_id
        )
        
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(role="user", parts=[types.Part(text=message)])
        ):
            if hasattr(event, 'content') and event.content:
                if event.content.role == 'model':
                    for part in event.content.parts:
                        if part.text:
                            response_text = part.text
        
        return response_text if response_text else "⚠️ Agent không phản hồi."

    def query(self, message):
        """Entry point từ Odoo Discuss"""
        try:
            agent = self.create_agent()
            return asyncio.run(self._run_async(agent, message))
        except Exception as e:
            _logger.error(f"P&L Agent Error: {e}", exc_info=True)
            return f"❌ Lỗi Agent: {str(e)}"
