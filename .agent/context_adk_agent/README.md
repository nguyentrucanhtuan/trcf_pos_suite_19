# Google ADK Documentation - Tài liệu tham khảo

> **Source**: https://google.github.io/adk-docs/
> 
> **Last Updated**: 2025-12-22

---

## 📚 Mục đích

Thư mục này chứa tài liệu Google ADK đã được **xác minh từ nguồn chính thức** để AI Agent tham khảo khi viết code, giúp:

- ✅ Tuân thủ đúng cú pháp Google ADK
- ✅ Tránh lỗi phổ biến
- ✅ Áp dụng best practices

---

## ⚠️ ĐIỂM QUAN TRỌNG - CÚ PHÁP ĐÚNG

| Điểm | SAI | ĐÚNG |
|------|-----|------|
| Import Agent | `from adk import Agent` | `from google.adk.agents import Agent` |
| Import types | `from adk import types` | `from google.genai import types` |
| Runner | `InMemoryRunner` | `Runner` + `InMemorySessionService` |
| Tool return | `-> str` (JSON) | `-> dict` với status/report |
| Agent param | `system_instruction` | `instruction` |

---

## 📁 Files trong thư mục

| File | Mô tả |
|------|-------|
| [core-concepts.md](./core-concepts.md) | Khái niệm cơ bản: Agent, Tools, Sessions, Runner |
| [odoo-integration.md](./odoo-integration.md) | Patterns tích hợp ADK vào Odoo |
| [best-practices.md](./best-practices.md) | Best practices cho Agent và Tool design |
| [troubleshooting.md](./troubleshooting.md) | Xử lý lỗi thường gặp |

---

## 🚀 Quick Start

### Tạo Agent cơ bản
```python
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# 1. Tạo tool - TRẢ VỀ DICT!
def my_tool(query: str) -> dict:
    """Tool description for LLM."""
    return {"status": "success", "report": f"Result: {query}"}

# 2. Tạo agent
agent = Agent(
    name="my_agent",
    model="gemini-2.0-flash",
    description="My agent description",
    instruction="You are a helpful assistant.",  # KHÔNG dùng system_instruction!
    tools=[my_tool]
)

# 3. Setup và run
session_service = InMemorySessionService()
runner = Runner(agent=agent, app_name="my_app", session_service=session_service)
```

---

## 💡 Khi nào tham khảo file nào?

| Cần gì? | Đọc file |
|---------|----------|
| Hiểu Agent, Tool, Runner | `core-concepts.md` |
| Tích hợp vào Odoo | `odoo-integration.md` |
| Design tool đúng cách | `best-practices.md` |
| Gặp lỗi | `troubleshooting.md` |

---

## 🔗 Tài liệu gốc

- **Official Docs**: https://google.github.io/adk-docs/
- **Quickstart**: https://google.github.io/adk-docs/get-started/quickstart/
- **Function Tools**: https://google.github.io/adk-docs/tools-custom/function-tools/
