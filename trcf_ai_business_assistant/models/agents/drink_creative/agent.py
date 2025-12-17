# -*- coding: utf-8 -*-
"""
DRINK CREATIVE AGENT - Google ADK Agent
❌ KHÔNG COMPILE (chứa agent definition)

Sử dụng Google ADK với asyncio wrapper cho Odoo sync environment
"""
import logging
import os
import asyncio

from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner, types

from . import business_logic
from . import prompts

_logger = logging.getLogger(__name__)


class DrinkCreativeAgent:
    """
    Trợ lý Sáng tạo Thức uống - Google ADK
    
    Chức năng:
    - Tìm món trending
    - Tra công thức từ BOM
    - Gợi ý biến thể sáng tạo
    """
    
    def __init__(self, env):
        """
        Khởi tạo agent
        
        Args:
            env: Odoo environment
        """
        self.env = env
        self.model_name = "gemini-2.5-flash-lite"
    
    def _create_tools(self):
        """
        Tạo tools cho ADK Agent (Python functions với docstrings)
        
        Returns:
            list: Danh sách Python functions
        """
        env = self.env
        
        def search_trending(limit: int = 5) -> str:
            """
            Tìm các món thức uống bán chạy nhất trong 30 ngày.
            
            Gọi tool này khi user hỏi về món hot, trend, bán chạy.
            
            Args:
                limit: Số lượng món trả về (mặc định 5)
                
            Returns:
                Danh sách món trending với số lượng bán và doanh thu
            """
            try:
                data = business_logic.get_trending_drinks(env, limit=limit)
                return business_logic.format_trending_output(data)
            except Exception as e:
                _logger.error(f"❌ search_trending error: {e}", exc_info=True)
                return f"⚠️ Lỗi: {str(e)}"
        
        def get_recipe(product_name: str) -> str:
            """
            Lấy công thức của món thức uống từ hệ thống BOM.
            
            Gọi tool này khi user hỏi về công thức, cách pha, nguyên liệu.
            
            Args:
                product_name: Tên món cần tra công thức
                
            Returns:
                Công thức chi tiết bao gồm nguyên liệu, số lượng, giá vốn
            """
            try:
                recipe = business_logic.get_drink_recipe(env, product_name)
                return business_logic.format_recipe_output(recipe)
            except Exception as e:
                _logger.error(f"❌ get_recipe error: {e}", exc_info=True)
                return f"⚠️ Lỗi: {str(e)}"
        
        def suggest_creative(base_drink: str, style: str = "") -> str:
            """
            Gợi ý biến thể sáng tạo từ món có sẵn.
            
            Gọi tool này khi user muốn sáng tạo, biến thể, món mới.
            
            Args:
                base_drink: Món gốc làm nền tảng sáng tạo
                style: Phong cách/Concept (VD: 'mùa hè', 'ít ngọt', 'healthy')
                
            Returns:
                Gợi ý món mới với công thức và lý do
            """
            try:
                recipe = business_logic.get_drink_recipe(env, base_drink)
                rules = business_logic.get_creativity_rules(env)
                if not rules:
                    rules = prompts.get_default_creativity_rules()
                
                context = f"""CÔNG THỨC GỐC:
{business_logic.format_recipe_output(recipe)}

QUY TẮC PHA CHẾ:
{rules}

STYLE MONG MUỐN: {style if style else 'Tự do sáng tạo'}

Hãy dựa trên thông tin trên để gợi ý biến thể sáng tạo!"""
                
                return context
            except Exception as e:
                _logger.error(f"❌ suggest_creative error: {e}", exc_info=True)
                return f"⚠️ Lỗi: {str(e)}"
        
        return [search_trending, get_recipe, suggest_creative]
    
    def create_agent(self):
        """
        Tạo Google ADK Agent instance
        
        Returns:
            Agent: ADK Agent đã được cấu hình
        """
        # Lấy API key và set vào environment variable
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'trcf.gemini_api_key', ''
        )
        if not api_key:
            raise ValueError("Chưa cấu hình Google API Key trong System Parameters (trcf.gemini_api_key)")
        
        os.environ['GOOGLE_API_KEY'] = api_key
        
        # Lấy quy tắc pha chế
        rules = business_logic.get_creativity_rules(self.env)
        if not rules:
            rules = prompts.get_default_creativity_rules()
        
        # Tạo system instruction
        system_instruction = prompts.get_system_instruction(rules)
        
        # Tạo tools
        tools = self._create_tools()
        
        # Tạo ADK Agent
        agent = Agent(
            name="drink_creative_assistant",
            model=self.model_name,
            tools=tools,
            instruction=system_instruction
        )
        
        return agent
    
    async def _run_agent_async(self, agent, message):
        """
        Run agent async với InMemoryRunner
        
        Args:
            agent: ADK Agent instance
            message: User message
            
        Returns:
            str: Agent response
        """
        # Tạo runner với agent
        runner = InMemoryRunner(
            app_name="trcf_ai_assistant",
            agent=agent
        )
        
        # Tạo session mới cho mỗi request
        user_id = "odoo_user"
        session_id = f"session_{id(self)}_{id(message)}"  # Unique session per request
        
        # Tạo session trong session service
        await runner.session_service.create_session(
            app_name="trcf_ai_assistant",
            user_id=user_id,
            session_id=session_id
        )
        
        # Run agent và collect response
        response_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=types.Content(
                role="user",
                parts=[types.Part(text=message)]
            )
        ):
            # Chỉ collect text từ model responses (bỏ qua function calls)
            if hasattr(event, 'content') and event.content:
                content = event.content
                # Chỉ lấy text từ model role
                if hasattr(content, 'role') and content.role == 'model':
                    if hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            # Chỉ lấy text, bỏ qua function_call
                            if hasattr(part, 'text') and part.text:
                                response_text = part.text  # Overwrite để lấy response cuối cùng
        
        return response_text if response_text else "⚠️ Không có phản hồi từ agent"
    
    def query(self, message):
        """
        Xử lý query từ user (sync wrapper cho async agent)
        
        Args:
            message: Tin nhắn từ user
            
        Returns:
            str: Response từ AI
        """
        try:
            agent = self.create_agent()
            
            # Run async agent trong sync context bằng asyncio.run()
            response = asyncio.run(self._run_agent_async(agent, message))
            return response
            
        except ValueError as e:
            return f"⚠️ {str(e)}"
        except Exception as e:
            error_msg = str(e)
            
            # Xử lý quota exceeded error
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                return (
                    "⚠️ **Google API Quota vượt giới hạn**\n\n"
                    "Bạn đã dùng hết quota miễn phí của Gemini API.\n\n"
                    "🔗 Kiểm tra usage: https://ai.dev/usage?tab=rate-limit\n"
                    "📊 Tìm hiểu về quota: https://ai.google.dev/gemini-api/docs/rate-limits\n\n"
                    "**Giải pháp:**\n"
                    "- Đợi 1-2 phút để quota reset\n"
                    "- Hoặc nâng cấp lên paid plan"
                )
            
            # Xử lý model not found error
            if "404" in error_msg or "not found" in error_msg.lower():
                return (
                    "⚠️ **Model không tồn tại**\n\n"
                    f"Model `{self.model_name}` không khả dụng.\n"
                    "Vui lòng kiểm tra lại model name trong cấu hình."
                )
            
            # Lỗi chung
            _logger.error(f"❌ Agent error: {e}", exc_info=True)
            return f"⚠️ Lỗi xử lý: {error_msg[:200]}..." if len(error_msg) > 200 else f"⚠️ Lỗi: {error_msg}"
