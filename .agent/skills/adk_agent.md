# Skill: Phát triển Google ADK Agent (TRCF AI Style)

Kỹ năng này hướng dẫn Antigravity cách thiết kế và triển khai AI Agents thông minh, bảo mật và hiệu quả bằng Google ADK trong môi trường Odoo.

## 🎯 Nguyên tắc cốt lõi
- **Tách biệt logic (Separation of Concerns)**: Luôn tách `prompts.py`, `business_logic.py` và `agent.py`.
- **Bảo mật (Security)**: Thiết kế sẵn để có thể biên dịch Cython các file chứa "chất xám" (prompts và business logic).
- **Tin cậy (Reliability)**: Tool phải trả về dữ liệu cấu trúc (dict), xử lý lỗi chặt chẽ.

## 📝 Kỹ năng viết Prompts (`prompts.py`)
- **System Instruction**: Luôn bao gồm:
    - **Vai trò**: "Bạn là chuyên gia về [lĩnh vực]..."
    - **Context thời gian**: Luôn truyền `today_str` vào prompt.
    - **Giới hạn**: "Chỉ trả lời dựa trên dữ liệu từ các công cụ được cung cấp."
    - **Định dạng**: "Trả lời ngắn gọn, sử dụng Markdown, ưu tiên tiếng Việt."
- **Bảo mật**: Tuyệt đối không để API Keys hay thông tin nhạy cảm trong prompt.

## ⚙️ Thiết kế Tools (`business_logic.py` & `agent.py`)
- **Return Type**: Luôn trả về `dict` có cấu trúc: `{"status": "success/error", "report": "...", "data": {...}}`.
- **Docstring cho Tool**: Cực kỳ quan trọng vì ADK dùng nó để hiểu Tool. Phải mô tả:
    - Tool làm gì?
    - Khi nào Agent nên gọi Tool này?
    - Ý nghĩa của từng tham số (`Args`).
- **Idempotency**: Tool tra cứu dữ liệu không được làm thay đổi trạng thái hệ thống. Tool ghi dữ liệu phải có xác nhận hoặc kiểm tra điều kiện.

## 🚀 Thực thi ADK (Pattern chuẩn)
- **Imports**: Luôn dùng đúng namespace:
    - `from google.adk.agents import Agent`
    - `from google.adk.runners import Runner`
    - `from google.adk.sessions import InMemorySessionService`
    - `from google.genai import types`
- **Async Handling**: Luôn dùng `asyncio.run()` trong Odoo để bọc hàm `_run_async` của ADK.
- **Quota & Error**: Luôn bọc logic gọi AI trong `try...except` để xử lý lỗi Quota (429) hoặc lỗi kết nối.

## 🧪 Testing & Debugging
- Kiểm tra Tool thủ công trước khi gắn vào Agent.
- Log lại các event quan trọng trong `runner.run_async` để debug khi Agent "đi chệch hướng".

## ⚠️ Lưu ý đặc thù TRCF
- Prefix cho Agent Model: `trcf.ai.`. ví dụ: `trcf.ai.business.assistant`.
- Luôn sử dụng Gemini model mới nhất (ví dụ: `gemini-2.0-flash`).
