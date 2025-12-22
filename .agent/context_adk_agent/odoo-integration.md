# ADK Integration with Odoo (Tích hợp ADK với Odoo)

> **Source**: https://google.github.io/adk-docs/
> 
> **Last Updated**: 2025-12-22
>
> **IMPORTANT**: Cập nhật theo cú pháp chính thức Google ADK

---

## ⚠️ CÚ PHÁP ĐÚNG vs SAI

| Điểm | SAI (cũ) | ĐÚNG (Google docs) |
|------|----------|-------------------|
| Import Agent | `from adk import Agent` | `from google.adk.agents import Agent` |
| Import types | `from adk import types` | `from google.genai import types` |
| Runner | `InMemoryRunner` | `Runner` + `InMemorySessionService` |
| Tool return | `-> str` | `-> dict` với status/report |
| Agent param | `system_instruction` | `instruction` |

---

## 1. Chạy ADK trong Odoo (Synchronous Environment)

### Thách thức
Odoo chạy synchronous, ADK sử dụng async. Google ADK docs nói:
> "Async is Primary. A synchronous Runner.run method exists mainly for convenience."

### Giải pháp: Dùng `asyncio.run()` 

```python
import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

def query_agent(env, message):
    """Entry point từ Odoo - gọi async agent."""
    return asyncio.run(_run_agent_async(env, message))

async def _run_agent_async(env, message):
    """Async function chạy agent."""
    # 1. Setup
    session_service = InMemorySessionService()
    agent = Agent(
        name="odoo_agent",
        model="gemini-2.0-flash",
        instruction="You are a helpful assistant.",
        tools=[...]
    )
    
    # 2. Create session
    user_id = str(env.uid)
    session_id = f"session_{user_id}"
    await session_service.create_session(
        app_name="odoo_app",
        user_id=user_id,
        session_id=session_id
    )
    
    # 3. Create runner
    runner = Runner(
        agent=agent,
        app_name="odoo_app",
        session_service=session_service
    )
    
    # 4. Run agent
    content = types.Content(
        role='user',
        parts=[types.Part(text=message)]
    )
    
    response = ""
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=content
    ):
        if event.is_final_response():
            if event.content and event.content.parts:
                response = event.content.parts[0].text
            break
    
    return response or "Không có phản hồi"
```

---

## 2. Pattern chuẩn cho Odoo Model

```python
# -*- coding: utf-8 -*-
import os
import asyncio
import logging

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

APP_NAME = "my_odoo_agent"

class MyAgentModel(models.Model):
    _name = 'my.agent.model'
    _description = 'My ADK Agent'
    
    name = fields.Char()
    
    def _get_api_key(self):
        """Get API key from Odoo config."""
        api_key = self.env['ir.config_parameter'].sudo().get_param('trcf.gemini_api_key', '')
        if not api_key:
            raise ValueError("Chưa cấu hình Google API Key")
        os.environ['GOOGLE_API_KEY'] = api_key
        return api_key
    
    def _create_tools(self):
        """Create tools - TRẢ VỀ DICT!"""
        env = self.env
        
        def search_products(query: str) -> dict:
            """
            Tìm kiếm sản phẩm.
            
            Args:
                query (str): Từ khóa tìm kiếm.
                
            Returns:
                dict: status và kết quả.
            """
            try:
                products = env['product.product'].search([
                    ('name', 'ilike', query)
                ], limit=10)
                
                items = [{'id': p.id, 'name': p.name, 'price': p.list_price} for p in products]
                return {
                    "status": "success",
                    "report": f"Tìm thấy {len(items)} sản phẩm: {items}"
                }
            except Exception as e:
                return {"status": "error", "error_message": str(e)}
        
        return [search_products]
    
    def _create_agent(self):
        """Create Agent theo cú pháp ĐÚNG."""
        self._get_api_key()
        
        return Agent(
            name="my_agent",
            model="gemini-2.0-flash",
            description="Agent hỗ trợ nghiệp vụ Odoo",
            instruction="Bạn là trợ lý AI cho hệ thống Odoo. Dùng tools để trả lời.",
            tools=self._create_tools()
        )
    
    async def _run_async(self, agent, message):
        """Run agent async - ĐÚNG PATTERN từ Google docs."""
        session_service = InMemorySessionService()
        user_id = str(self.env.uid)
        session_id = f"session_{self.id}"
        
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
        
        response = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    response = event.content.parts[0].text
                break
        
        return response or "Không có phản hồi"
    
    def query(self, message):
        """Public method - gọi từ Odoo."""
        try:
            agent = self._create_agent()
            return asyncio.run(self._run_async(agent, message))
        except Exception as e:
            _logger.error(f"Agent error: {e}", exc_info=True)
            return f"Lỗi: {str(e)[:200]}"
```

---

## 3. Tạo Tools cho Odoo - TRẢ VỀ `dict`!

### Pattern chuẩn
```python
def my_tool(param: str) -> dict:
    """
    Tool description - LLM đọc này để quyết định gọi tool.
    
    Args:
        param (str): Mô tả parameter.
        
    Returns:
        dict: status và result hoặc error.
    """
    try:
        # Your logic here
        result = do_something(param)
        return {
            "status": "success",
            "report": f"Kết quả: {result}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }
```

### Tool truy cập Odoo Records
```python
def search_records(model_name: str, name_filter: str) -> dict:
    """
    Tìm kiếm records trong Odoo.
    
    Args:
        model_name (str): Tên model (vd: 'product.product')
        name_filter (str): Filter theo tên
        
    Returns:
        dict: Danh sách records tìm được
    """
    try:
        # Validate model
        ALLOWED = ['product.product', 'sale.order']
        if model_name not in ALLOWED:
            return {"status": "error", "error_message": f"Model {model_name} not allowed"}
        
        records = env[model_name].search([('name', 'ilike', name_filter)], limit=10)
        items = [{'id': r.id, 'name': r.display_name} for r in records]
        
        return {
            "status": "success",
            "report": f"Found {len(items)} records: {items}"
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
```

---

## 4. Error Handling

```python
def query(self, message):
    """Entry point với error handling."""
    try:
        agent = self._create_agent()
        return asyncio.run(self._run_async(agent, message))
    
    except ValueError as e:
        # Config errors
        return f"⚠️ Cấu hình lỗi: {e}"
    
    except Exception as e:
        error_msg = str(e)
        
        # Quota exceeded
        if "429" in error_msg or "quota" in error_msg.lower():
            return "⚠️ Quota API hết. Đợi 1-2 phút."
        
        # API key issues
        if "api key" in error_msg.lower():
            return "⚠️ API Key không hợp lệ."
        
        _logger.error(f"Agent error: {e}", exc_info=True)
        return f"⚠️ Lỗi: {error_msg[:200]}"
```

---

## 📌 Checklist Tích hợp ADK vào Odoo

- [ ] Import từ `google.adk.agents`, `google.adk.runners`, `google.adk.sessions`
- [ ] Import types từ `google.genai`
- [ ] Dùng `Runner` + `InMemorySessionService` (KHÔNG dùng `InMemoryRunner`)
- [ ] Agent dùng `instruction` (KHÔNG dùng `system_instruction`)
- [ ] Tools trả về `dict` với `status`/`report`/`error_message`
- [ ] Dùng `asyncio.run()` để gọi async từ Odoo
- [ ] Error handling đầy đủ
- [ ] API key từ Odoo config

---

## 🔗 Tham khảo

- **Official Docs**: https://google.github.io/adk-docs/
- **Quickstart**: https://google.github.io/adk-docs/get-started/quickstart/
- **Function Tools**: https://google.github.io/adk-docs/tools-custom/function-tools/
- Xem thêm: `core-concepts.md`, `best-practices.md`
