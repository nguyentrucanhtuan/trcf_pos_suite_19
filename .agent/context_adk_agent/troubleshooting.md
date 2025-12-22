# ADK Troubleshooting (Xử lý lỗi thường gặp)

> **Source**: https://google.github.io/adk-docs/
> 
> **Last Updated**: 2025-12-22
>
> **IMPORTANT**: Cú pháp đã cập nhật theo tài liệu chính thức Google ADK

---

## ⚠️ LƯU Ý QUAN TRỌNG - CÚ PHÁP ĐÃ THAY ĐỔI

Các lỗi dưới đây sử dụng **cú pháp ĐÚNG** từ Google ADK docs:

| Điểm | SAI | ĐÚNG |
|------|-----|------|
| Import | `from adk import Agent` | `from google.adk.agents import Agent` |
| types | `from adk import types` | `from google.genai import types` |
| Runner | `InMemoryRunner` | `Runner` + `InMemorySessionService` |
| Tool return | `-> str` | `-> dict` với status/report |

---

## 1. Runner và Session Errors

### Lỗi: "Missing required parameter"
```
TypeError: Runner() missing required argument: 'session_service'
```

**Nguyên nhân:** Chưa truyền `session_service` cho `Runner`

**Giải pháp:**
```python
# ❌ SAI - Thiếu session_service
runner = Runner(agent=agent, app_name="my_app")

# ✅ ĐÚNG
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

session_service = InMemorySessionService()
runner = Runner(
    agent=agent,
    app_name="my_app",
    session_service=session_service
)
```

---

### Lỗi: "Session not created"
```
ValueError: Session 'session_123' not found for user 'user_456'
```

**Nguyên nhân:** Chưa tạo session trước khi run

**Giải pháp:**
```python
# ✅ ĐÚNG - Tạo session TRƯỚC khi run
await session_service.create_session(
    app_name="my_app",
    user_id="user_456",
    session_id="session_123"
)

# Sau đó mới run
async for event in runner.run_async(
    user_id="user_456",
    session_id="session_123",
    new_message=content
):
    ...
```

---

### Lỗi: "new_message must be types.Content"
```
TypeError: new_message must be of type Content
```

**Nguyên nhân:** Truyền string thay vì `types.Content`

**Giải pháp:**
```python
# ❌ SAI
new_message = "Hello, agent!"

# ✅ ĐÚNG
from google.genai import types  # KHÔNG phải from adk import types!

new_message = types.Content(
    role='user',
    parts=[types.Part(text="Hello, agent!")]
)
```

---

## 2. Tool Errors

### Lỗi: Tool không được gọi hoặc gọi sai

**Nguyên nhân:** Docstring không rõ ràng

**Giải pháp:** LLM đọc docstring để quyết định gọi tool
```python
# ❌ SAI - Docstring mơ hồ
def my_tool(x):
    """Process data."""
    pass

# ✅ ĐÚNG - Docstring chi tiết
def search_products(query: str) -> dict:
    """
    Tìm kiếm sản phẩm trong database.
    Gọi tool này khi user hỏi về sản phẩm hoặc menu.
    
    Args:
        query (str): Từ khóa tìm kiếm (tên sản phẩm)
        
    Returns:
        dict: status và danh sách sản phẩm
    """
    ...
```

---

### Lỗi: "Tool function returned wrong type"
```
TypeError: Tool function 'search_products' returned str, expected dict
```

**Nguyên nhân:** Tool return string thay vì dict

**Giải pháp (QUAN TRỌNG!):**
```python
# ❌ SAI - Return string (cách CŨ)
def search_products(query: str) -> str:
    return json.dumps(results)

# ✅ ĐÚNG - Return dict với status pattern
def search_products(query: str) -> dict:
    """Search products."""
    if success:
        return {
            "status": "success",
            "report": f"Found {count} products"
        }
    else:
        return {
            "status": "error",
            "error_message": "No products found"
        }
```

---

## 3. Agent Configuration Errors

### Lỗi: "Unknown parameter 'system_instruction'"
```
TypeError: Agent() got unexpected keyword argument 'system_instruction'
```

**Nguyên nhân:** ADK dùng `instruction`, không phải `system_instruction`

**Giải pháp:**
```python
# ❌ SAI
agent = Agent(
    name="my_agent",
    model="gemini-2.0-flash",
    system_instruction="You are helpful."  # WRONG!
)

# ✅ ĐÚNG
agent = Agent(
    name="my_agent",
    model="gemini-2.0-flash",
    instruction="You are helpful."  # ĐÚNG!
)
```

---

### Lỗi: Import không tìm thấy
```
ImportError: cannot import name 'Agent' from 'adk'
```

**Giải pháp:**
```python
# ❌ SAI - Import cũ
from adk import Agent
from adk import types
from adk.runners import InMemoryRunner

# ✅ ĐÚNG - Import theo Google docs
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
```

---

## 4. Async/Await Errors trong Odoo

### Lỗi: "'await' outside async function"
```
SyntaxError: 'await' outside async function
```

**Giải pháp:** Dùng `asyncio.run()` trong Odoo
```python
import asyncio

# Odoo method (sync)
def query(self, message):
    return asyncio.run(self._run_async(message))

# Async method
async def _run_async(self, message):
    session_service = InMemorySessionService()
    # ... setup ...
    async for event in runner.run_async(...):
        ...
```

---

### Lỗi: Event loop already running
```
RuntimeError: This event loop is already running
```

**Giải pháp:** Dùng `nest_asyncio` nếu cần
```python
import nest_asyncio
nest_asyncio.apply()

# Hoặc tạo new event loop
import asyncio
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
result = loop.run_until_complete(self._run_async(message))
```

---

## 5. API Key Errors

### Lỗi: "API key not found"
```
ValueError: GOOGLE_API_KEY environment variable not set
```

**Giải pháp:**
```python
import os

# Lấy từ Odoo config
api_key = self.env['ir.config_parameter'].sudo().get_param('trcf.gemini_api_key', '')
if not api_key:
    raise ValueError("Chưa cấu hình Google API Key")
os.environ['GOOGLE_API_KEY'] = api_key
```

---

### Lỗi: "Quota exceeded" (429)
```
google.api_core.exceptions.ResourceExhausted: 429 Quota exceeded
```

**Giải pháp:**
```python
def query(self, message):
    try:
        return asyncio.run(self._run_async(message))
    except Exception as e:
        if "429" in str(e) or "quota" in str(e).lower():
            return "⚠️ Quota API hết. Đợi 1-2 phút."
        raise
```

---

## 6. Response Parsing

### Lỗi: Không lấy được response text

**Giải pháp:** Dùng `event.is_final_response()`
```python
async for event in runner.run_async(...):
    if event.is_final_response():
        if event.content and event.content.parts:
            response = event.content.parts[0].text
        break
```

---

## 7. Odoo Serialization

### Lỗi: "RecordSet is not JSON serializable"
```
TypeError: Object of type 'product.product' is not JSON serializable
```

**Giải pháp:** Convert recordset sang dict
```python
def search_products(query: str) -> dict:
    products = env['product.product'].search([...])
    
    # Convert thành list of dicts
    items = [
        {'id': p.id, 'name': p.name, 'price': p.list_price}
        for p in products
    ]
    
    return {
        "status": "success",
        "report": f"Found {len(items)} products: {items}"
    }
```

---

## 📌 Debugging Checklist

### 1. Imports
- [ ] `from google.adk.agents import Agent`
- [ ] `from google.adk.runners import Runner`
- [ ] `from google.adk.sessions import InMemorySessionService`
- [ ] `from google.genai import types`

### 2. Agent Setup
- [ ] Dùng `instruction` (KHÔNG phải `system_instruction`)
- [ ] Có `name`, `model`, `instruction`, `tools`

### 3. Runner Setup
- [ ] Tạo `InMemorySessionService()` first
- [ ] `Runner(agent=..., app_name=..., session_service=...)`
- [ ] `await session_service.create_session(...)` TRƯỚC khi run

### 4. Tools
- [ ] Return `dict` với `status`/`report`/`error_message`
- [ ] Docstring chi tiết với Args, Returns
- [ ] Type hints đầy đủ

### 5. Message
- [ ] `types.Content(role='user', parts=[types.Part(text=...)])`
- [ ] Import từ `google.genai` KHÔNG phải `adk`

---

## 🔗 Tham khảo

- **Official Docs**: https://google.github.io/adk-docs/
- **Quickstart**: https://google.github.io/adk-docs/get-started/quickstart/
- **Function Tools**: https://google.github.io/adk-docs/tools-custom/function-tools/
