---
description: /trcf_create_adk_agent - Tạo AI Agent chuẩn Google ADK tích hợp Odoo 19
---

Sử dụng workflow này khi bạn muốn tạo một AI Agent mới sử dụng Google ADK trong Odoo.

# Quy trình thực hiện

1.  **Xác định Agent**: Hỏi người dùng tên Agent và các tools cần thiết (truy vấn danh mục, báo cáo, hay xử lý logic).
2.  **Tạo cấu trúc thư mục**: Tạo package mới trong `custom_addons/your_module/models/agents/[agent_name]/`.
3.  **Generate Files**: Tạo 4 file chuẩn:
    *   `__init__.py`: Import class Agent.
    *   `prompts.py`: Chứa `SYSTEM_INSTRUCTION`.
    *   `business_logic.py`: Chứa các hàm tools (được gán Type Hint đầy đủ).
    *   `agent.py`: Chứa class chính, Runner logic và bridge Async-Sync.
4.  **Thiết lập Discuss (Mail Hook)**:
    *   Đảm bảo `res.users` cho Agent đã được tạo (thường qua file `data/`).
    *   Kiểm tra logic trong `mail_message.py` để bot có thể tự động trả lời khi được mention hoặc trong channel riêng.
5.  **Đăng ký Agent**: Cập nhật `agent_registry.py` để Odoo có thể nhận diện Agent mới.

# Template Code chuẩn cho `agent.py`

```python
import logging
import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner, types
from google.adk.sessions import InMemorySessionService
from . import business_logic, prompts

_logger = logging.getLogger(__name__)

class YourAgentName:
    def __init__(self, env):
        self.env = env
        self.model_name = "gemini-2.0-flash-lite"

    def create_agent(self):
        tools = business_logic.get_tools(self.env)
        return Agent(
            name="unique_agent_name",
            model=self.model_name,
            instruction=prompts.SYSTEM_INSTRUCTION,
            tools=tools
        )

    async def _run_async(self, agent, message):
        # ... logic Runner chuẩn bridge với Odoo ...
        pass

    def query(self, message):
        """Entry point từ Odoo Discuss"""
        return asyncio.run(self._run_async(self.create_agent(), message))
```

# Cách kết nối với Odoo Discuss

Để Agent có thể chat trực tiếp, bạn cần cấu hình trong `mail_message.py` (Inherit từ `mail.message`):

1. **Lấy Bot User**: Tìm partner của bot agent.
2. **Hook `create`**: Chặn tin nhắn mới trong `discuss.channel`.
3. **Gọi Router**: Gửi text đến `agent_router.route()`.
4. **Post Reply**: Dùng `channel.message_post()` để trả lời người dùng.

// turbo
5. **Kiểm tra Syntax**: Chạy lệnh `python3 -m py_compile` cho các file mới tạo để đảm bảo không có lỗi cú pháp.

// turbo
6. **Nâng cấp Module**: Chạy lệnh nâng cấp module để áp dụng thay đổi ngay lập tức:
   `python3 odoo-bin -c odoo19.conf -u [module_name] -d coffeetree_odoo19_restore --stop-after-init`
