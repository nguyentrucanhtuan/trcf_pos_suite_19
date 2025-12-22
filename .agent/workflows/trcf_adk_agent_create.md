---
description: Tạo Odoo module với Google ADK Agent
---

# Workflow: Google ADK Agent Module

Tạo module Odoo tích hợp Google ADK Agent.

> ⚠️ **QUAN TRỌNG**: Tài liệu này dựa trên https://google.github.io/adk-docs/ 
> Luôn tham chiếu `context_adk_agent/core-concepts.md` để đảm bảo đúng cú pháp.

## 📋 Prerequisites

- `pip install google-adk google-genai`
- **Đọc tài liệu ADK:** `custom_addons/.agent/context_adk_agent/`
  - `core-concepts.md` - Khái niệm cơ bản về Agents, Tools, Runners
  - `odoo-integration.md` - Patterns tích hợp ADK với Odoo
  - `best-practices.md` - Best practices cho tool design, security
  - `troubleshooting.md` - Xử lý lỗi thường gặp

## 📁 Cấu trúc Module

```
trcf_my_agent/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   ├── trcf_agent_model.py        # Odoo model wrapper
│   └── agents/
│       └── my_agent/
│           ├── __init__.py
│           ├── agent.py           # ❌ KHÔNG compile
│           ├── business_logic.py  # ✅ Compile được
│           └── prompts.py         # ✅ Compile được
├── security/
│   └── ir.model.access.csv
└── views/
    └── agent_views.xml
```

## 📝 Steps

### 1. Tạo cấu trúc

```bash
cd custom_addons
MODULE="trcf_my_agent"
mkdir -p $MODULE/{models/agents/my_agent,security,views}
touch $MODULE/__init__.py $MODULE/__manifest__.py
touch $MODULE/models/__init__.py $MODULE/models/trcf_agent_model.py
touch $MODULE/models/agents/__init__.py
touch $MODULE/models/agents/my_agent/{__init__.py,agent.py,business_logic.py,prompts.py}
```

### 2. `__manifest__.py`

```python
{
    'name': 'TRCF My Agent',
    'version': '1.0',
    'summary': 'AI Agent với Google ADK',
    'author': 'Tuấn Rang Cà Phê',
    'depends': ['base'],
    'external_dependencies': {'python': ['google-adk', 'google-genai']},
    'data': ['security/ir.model.access.csv'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
```

### 3. `prompts.py` (✅ Compile)

```python
# -*- coding: utf-8 -*-
"""System prompts - CÓ THỂ COMPILE"""

def get_system_instruction(today_str):
    return f"""Bạn là trợ lý AI.
HÔM NAY: {today_str}

NHIỆM VỤ:
- [Mô tả nhiệm vụ]

CÁCH TRẢ LỜI:
- Ngắn gọn, tiếng Việt
- Có emoji
- Đưa số liệu cụ thể"""
```

### 4. `business_logic.py` (✅ Compile)

```python
# -*- coding: utf-8 -*-
"""Business logic - CÓ THỂ COMPILE"""
import logging
_logger = logging.getLogger(__name__)

def get_data(env, param1=None):
    """Lấy dữ liệu từ Odoo"""
    try:
        records = env['model.name'].sudo().search([])
        return {'data': records.mapped('name'), 'count': len(records)}
    except Exception as e:
        _logger.error(f"❌ Error: {e}")
        return {'error': str(e)}

def format_output(data):
    """Format output thành dict (KHÔNG PHẢI string!)"""
    if 'error' in data:
        return {"status": "error", "error_message": data['error']}
    return {"status": "success", "report": f"📊 Kết quả: {data['count']} records"}
```

### 5. `agent.py` (❌ KHÔNG compile) - THEO TÀI LIỆU CHÍNH THỨC

```python
# -*- coding: utf-8 -*-
"""ADK Agent - KHÔNG COMPILE
Dựa trên: https://google.github.io/adk-docs/tools-custom/function-tools/
"""
import os
import asyncio
import logging

# ⚠️ IMPORT ĐÚNG - từ google.adk và google.genai
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from . import business_logic, prompts

_logger = logging.getLogger(__name__)

APP_NAME = "my_agent_app"

class MyAgent:
    def __init__(self, env):
        self.env = env
        self.model_name = "gemini-2.0-flash"  # Model chính thức từ Google docs
    
    def _create_tools(self):
        """Tạo tools - trả về dict, KHÔNG PHẢI string!"""
        env = self.env
        
        def get_info(query: str = "") -> dict:
            """
            Lấy thông tin từ hệ thống.
            
            Args:
                query (str): Từ khóa tìm kiếm.
                
            Returns:
                dict: status và result hoặc error message.
            """
            try:
                data = business_logic.get_data(env, query)
                return business_logic.format_output(data)
            except Exception as e:
                return {"status": "error", "error_message": str(e)}
        
        return [get_info]
    
    def create_agent(self):
        """Tạo Agent theo cú pháp CHÍNH XÁC từ Google ADK docs."""
        api_key = self.env['ir.config_parameter'].sudo().get_param('trcf.gemini_api_key', '')
        if not api_key:
            raise ValueError("Chưa cấu hình Google API Key")
        os.environ['GOOGLE_API_KEY'] = api_key
        
        from odoo import fields
        today = fields.Date.today().strftime('%d-%m-%Y')
        
        # ⚠️ CÚ PHÁP ĐÚNG: name, model, description, instruction, tools
        return Agent(
            name="my_agent",
            model=self.model_name,
            description="Agent trả lời câu hỏi về dữ liệu hệ thống",
            instruction=prompts.get_system_instruction(today),  # KHÔNG PHẢI system_instruction!
            tools=self._create_tools(),
        )
    
    async def _run_async(self, agent, message):
        """Chạy agent theo pattern CHÍNH XÁC từ Google ADK docs."""
        # ⚠️ ĐÚNG: Dùng Runner + InMemorySessionService, KHÔNG PHẢI InMemoryRunner
        session_service = InMemorySessionService()
        user_id = "odoo_user"
        session_id = f"session_{id(message)}"
        
        # Tạo session
        await session_service.create_session(
            app_name=APP_NAME, 
            user_id=user_id, 
            session_id=session_id
        )
        
        # Tạo runner với session_service
        runner = Runner(
            agent=agent, 
            app_name=APP_NAME, 
            session_service=session_service
        )
        
        # ⚠️ ĐÚNG: types từ google.genai, role='user'
        content = types.Content(
            role='user', 
            parts=[types.Part(text=message)]
        )
        
        # Chạy async và lấy response
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
        
        return response or "⚠️ Không có phản hồi"
    
    def query(self, message):
        """Entry point - gọi từ Odoo model."""
        try:
            return asyncio.run(self._run_async(self.create_agent(), message))
        except Exception as e:
            if "429" in str(e) or "quota" in str(e).lower():
                return "⚠️ Quota API đã hết. Đợi 1-2 phút."
            _logger.error(f"❌ Error: {e}", exc_info=True)
            return f"⚠️ Lỗi: {str(e)[:200]}"
```

### 6. `trcf_agent_model.py` (Odoo Model)

```python
# -*- coding: utf-8 -*-
from odoo import models, fields, api
from .agents.my_agent.agent import MyAgent

class TrcfAgentModel(models.Model):
    _name = 'trcf.my.agent'
    _description = 'My ADK Agent'
    
    name = fields.Char('Name', default='My Agent')
    
    def query(self, message):
        agent = MyAgent(self.env)
        return agent.query(message)
```

### 7. Init files

**`__init__.py`:** `from . import models`

**`models/__init__.py`:** `from . import trcf_agent_model, agents`

**`models/agents/__init__.py`:** `from . import my_agent`

**`models/agents/my_agent/__init__.py`:**
```python
from . import prompts, business_logic, agent
```

### 8. Security

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_trcf_my_agent,trcf.my.agent,model_trcf_my_agent,base.group_user,1,1,1,1
```

### 9. Install & Test

// turbo
```bash
./odoo-bin -c odoo19.conf -u trcf_my_agent --stop-after-init 2>&1 | tail -100
```

**Error Handling:** Nếu có lỗi, phân tích nguyên nhân và đề xuất cách fix. Chờ user xác nhận trước khi sửa.

**Test:**
```python
agent = env['trcf.my.agent'].create({'name': 'test'})
print(agent.query("Xin chào"))
```

## ➕ Thêm Tool Mới

### 1. Thêm logic vào `business_logic.py`

```python
def get_new_feature(env, param1=None, param2=None):
    """Logic xử lý cho feature mới"""
    try:
        records = env['model.name'].sudo().search([('field', '=', param1)])
        result = {'items': [], 'total': 0}
        for rec in records:
            result['items'].append({'name': rec.name, 'value': rec.amount})
        result['total'] = len(records)
        return result
    except Exception as e:
        return {'error': str(e)}

def format_new_feature(data):
    """Format output - TRẢ VỀ DICT"""
    if 'error' in data:
        return {"status": "error", "error_message": data['error']}
    
    lines = [f"📋 Tìm thấy {data['total']} kết quả:"]
    for item in data['items']:
        lines.append(f"  • {item['name']}: {item['value']}")
    
    return {"status": "success", "report": "\n".join(lines)}
```

### 2. Thêm tool vào `_create_tools()` trong `agent.py`

```python
def _create_tools(self):
    env = self.env
    
    # Tool cũ
    def get_info(query: str = "") -> dict:
        """..."""
        ...
    
    # ⚠️ Tool mới - TRẢ VỀ DICT, không phải string!
    def get_new_feature(param1: str, param2: str = "") -> dict:
        """
        Mô tả chi tiết tool làm gì.
        Gọi tool này khi user hỏi về [tình huống cụ thể].
        
        Args:
            param1 (str): Mô tả param1 (bắt buộc)
            param2 (str): Mô tả param2 (optional)
            
        Returns:
            dict: status và result hoặc error message.
        """
        try:
            data = business_logic.get_new_feature(env, param1, param2)
            return business_logic.format_new_feature(data)
        except Exception as e:
            return {"status": "error", "error_message": str(e)}
    
    return [get_info, get_new_feature]  # Thêm tool vào list
```

### 3. Cập nhật `prompts.py`

```python
def get_system_instruction(today_str):
    return f"""...
TOOLS:
- get_info: Mô tả ngắn
- get_new_feature: Mô tả tool mới  # <-- Thêm dòng này
..."""
```

### 4. Test tool mới

// turbo
```bash
./odoo-bin -c odoo19.conf -u trcf_my_agent --stop-after-init 2>&1 | tail -100
```

```python
agent = env['trcf.my.agent'].create({'name': 'test'})
print(agent.query("[Câu hỏi trigger tool mới]"))
```

## ⚠️ ĐIỂM QUAN TRỌNG - SAI vs ĐÚNG

| Điểm | SAI (trước đây) | ĐÚNG (theo Google docs) |
|------|-----------------|------------------------|
| Import Agent | `from adk import Agent` | `from google.adk.agents import Agent` |
| Import types | `from adk import types` | `from google.genai import types` |
| Tool return | `-> str` (JSON string) | `-> dict` với status/report |
| Agent param | `system_instruction` | `instruction` |
| Runner | `InMemoryRunner` | `Runner` + `InMemorySessionService` |
| Run method | `runner.run(...)` | `runner.run_async(...)` + asyncio.run() |

## ✅ Checklist

- [ ] Cấu trúc agents subfolder
- [ ] Prompts + Logic tách riêng  
- [ ] **Tools trả về dict, KHÔNG PHẢI string**
- [ ] **Import từ google.adk và google.genai**
- [ ] **Dùng Runner + InMemorySessionService**
- [ ] Error handling (quota, 429)
- [ ] Security + Install OK
