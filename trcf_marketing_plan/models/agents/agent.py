# -*- coding: utf-8 -*-
"""
Marketing Content Agent - Tạo Content Pillars và Angles
"""
import logging
import os
import asyncio
import json
import re

from google.adk.agents import Agent
from google.adk.runners import Runner, types
from google.adk.sessions import InMemorySessionService

from odoo import fields
from . import business_logic

_logger = logging.getLogger(__name__)

APP_NAME = "trcf_marketing_plan"


def get_agent_instruction(today_str):
    """System instruction cho Marketing Agent"""
    return f"""Bạn là Marketing Strategist chuyên nghiệp ☕
Hôm nay: {today_str}

═══ LEARNING FROM FEEDBACK ═══
QUAN TRỌNG: Bạn có khả năng học từ feedback!

1. Dùng get_approved_content_history() → Xem content ĐÃ ĐƯỢC DUYỆT → HỌC phong cách này
2. Dùng get_rejected_content_history() → Xem content BỊ TỪ CHỐI → TRÁNH lặp lại

═══ DATA COLLECTION ═══
1. get_customer_persona() → Hiểu khách hàng
2. get_brand_key() → Hiểu thương hiệu
3. get_customer_journey() → Hiểu hành trình mua hàng
4. get_business_goals() → Hiểu mục tiêu kinh doanh
5. get_trending_products() → Xem sản phẩm đang hot

═══ OUTPUT REQUIREMENTS ═══
Khi được yêu cầu tạo content, hãy trả về JSON với cấu trúc:

```json
{{
  "contents": [
    {{
      "platform": "tiktok|instagram|facebook|threads",
      "pillar": "Tên content pillar",
      "angle": "Góc tiếp cận",
      "name": "Tiêu đề ngắn gọn",
      "hook": "Câu hook đầu video/bài",
      "content": "Nội dung chi tiết...",
      "hashtags": "#hashtag1 #hashtag2 #hashtag3"
    }}
  ]
}}
```

═══ RULES ═══
✅ Tạo 1 content cho MỖI platform được yêu cầu
✅ Mỗi content phải có đủ: name, pillar, angle, hook, content, hashtags
✅ Hook phải gây tò mò, thu hút
✅ Nội dung phù hợp với đặc thù từng platform
✅ Hashtags phù hợp và trending
✅ TRÁNH lặp lại rejected content
✅ HỌC từ approved content
✅ Trả về ĐÚNG format JSON"""


class MarketingContentAgent:
    """Agent tạo Content Marketing"""
    
    def __init__(self, env):
        self.env = env
        self.model_name = "gemini-2.0-flash-lite"
    
    def _setup_api_key(self):
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'trcf.marketing.content.gemini_api_key', ''
        )
        if not api_key:
            # Fallback to main API key
            api_key = self.env['ir.config_parameter'].sudo().get_param(
                'trcf.gemini_api_key', ''
            )
        if not api_key:
            raise ValueError("⚠️ Chưa cấu hình Gemini API Key trong Settings")
        os.environ['GOOGLE_API_KEY'] = api_key
    
    def _create_tools(self):
        env = self.env
        
        def get_customer_persona() -> dict:
            """Lấy chân dung khách hàng từ Settings."""
            return business_logic.get_customer_persona(env)
        
        def get_brand_key() -> dict:
            """Lấy thế mạnh thương hiệu từ Settings."""
            return business_logic.get_brand_key(env)
        
        def get_customer_journey() -> dict:
            """Lấy hành trình khách hàng từ Settings."""
            return business_logic.get_customer_journey(env)
        
        def get_business_goals() -> dict:
            """Lấy mục tiêu kinh doanh từ Settings."""
            return business_logic.get_business_goals(env)
        
        def get_trending_products() -> dict:
            """Lấy top 5 sản phẩm bán chạy nhất."""
            return business_logic.get_trending_products(env)
        
        def get_approved_content_history() -> dict:
            """Lấy content đã duyệt để học phong cách."""
            return business_logic.get_approved_content_history(env)
        
        def get_rejected_content_history() -> dict:
            """Lấy content bị từ chối để tránh lặp."""
            return business_logic.get_rejected_content_history(env)
        
        return [
            get_customer_persona,
            get_brand_key,
            get_customer_journey,
            get_business_goals,
            get_trending_products,
            get_approved_content_history,
            get_rejected_content_history
        ]
    
    def create_agent(self):
        """Tạo agent instance"""
        self._setup_api_key()
        today = fields.Date.today().strftime('%d-%m-%Y')
        instruction = get_agent_instruction(today)
        tools = self._create_tools()
        
        return Agent(
            name="marketing_content_agent",
            model=self.model_name,
            description="Chuyên gia Marketing Content",
            instruction=instruction,
            tools=tools
        )
    
    async def _run_agent_async(self, agent, message):
        session_service = InMemorySessionService()
        user_id = "odoo_user"
        session_id = f"session_marketing_{id(message)}"
        
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
        
        return response_text or "⚠️ Không có phản hồi từ AI."
    
    def _parse_and_save_content(self, response_text):
        """Parse JSON response và lưu vào database"""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response_text)
            if not json_match:
                _logger.warning("No JSON found in response")
                return None
            
            data = json.loads(json_match.group())
            contents = data.get('contents', [])
            
            created_ids = []
            for c in contents:
                record = self.env['trcf.marketing.content'].create({
                    'name': c.get('name', 'Untitled'),
                    'platform': c.get('platform', 'instagram'),
                    'pillar': c.get('pillar', ''),
                    'angle': c.get('angle', ''),
                    'hook': c.get('hook', ''),
                    'content': c.get('content', ''),
                    'hashtags': c.get('hashtags', ''),
                    'state': 'draft'
                })
                created_ids.append(record.id)
            
            return created_ids
        except Exception as e:
            _logger.error(f"Error parsing content: {e}")
            return None
    
    def generate_content(self, platforms=None, request=None):
        """
        Tạo content cho các platforms
        
        Args:
            platforms: List of platforms ['tiktok', 'instagram', 'facebook', 'threads']
            request: Custom request from user
        
        Returns:
            dict with created content IDs and raw response
        """
        try:
            if platforms is None:
                platforms = ['instagram']
            
            platform_str = ', '.join(platforms)
            
            if request:
                message = f"{request}\n\nTạo content cho các platform: {platform_str}"
            else:
                message = f"Hãy tạo content marketing cho các platform: {platform_str}"
            
            agent = self.create_agent()
            response = asyncio.run(self._run_agent_async(agent, message))
            
            # Parse and save to database
            created_ids = self._parse_and_save_content(response)
            
            return {
                'success': True,
                'created_ids': created_ids,
                'raw_response': response
            }
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                return {'success': False, 'error': "⚠️ Quota Gemini API đã hết. Hãy đợi 1 phút."}
            _logger.error(f"Marketing Agent Error: {e}", exc_info=True)
            return {'success': False, 'error': error_msg}
