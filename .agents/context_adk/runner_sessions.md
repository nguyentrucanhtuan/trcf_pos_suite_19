# ADK Runners & Sessions (Bộ thực thi và Phiên làm việc)

## 1. Quản lý Phiên (Session Management)
Session giúp duy trì lịch sử hội thoại và trạng thái.
- **InMemorySessionService**: Dùng cho ứng dụng đơn lẻ (phù hợp khi dev Odoo).
- **FirestoreSessionService**: Dùng cho ứng dụng thực tế đa người dùng, cần lưu trữ bền vững.

```python
from google.adk.sessions import InMemorySessionService
session_service = InMemorySessionService()
await session_service.create_session(app_name="app", user_id="u1", session_id="s1")
```

## 2. Thực thi với Runner
Runner là điểm bắt đầu để tương tác với Agent.
```python
from google.adk.runners import Runner, types

runner = Runner(
    agent=my_agent,
    app_name="my_app",
    session_service=session_service
)

# Chạy không đồng bộ (Async)
async for event in runner.run_async(
    user_id="u1",
    session_id="s1",
    new_message=types.Content(parts=[types.Part(text="Xin chào")])
):
    if event.is_final_response():
        print(event.content.parts[0].text)
```

## 3. Ngữ cảnh & Trạng thái (`session.state`)
- **State**: Dữ liệu tạm thời lưu trong một session (VD: bộ lọc hiện tại).
- **Shared Memory**: Ngữ cảnh dài hạn hội thoại có thể tìm kiếm lại.

## 4. Mô hình triển khai Odoo (Sync-to-Async bridge)
```python
import asyncio
def query(self, message):
    try:
        # Cầu nối từ Odoo Đồng bộ sang ADK Bất đồng bộ
        return asyncio.run(self._run_async(message))
    except Exception as e:
        return f"Lỗi thực thi: {e}"
```
