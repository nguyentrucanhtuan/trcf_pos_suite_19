# Google Search Tool - ADK Reference

Tài liệu hướng dẫn sử dụng công cụ tìm kiếm của Google tích hợp sẵn trong ADK.

## 📍 Tổng quan
Công cụ `google_search` cho phép Agent thực hiện tìm kiếm web trực tiếp. Công cụ này hỗ trợ **Grounding** (Xác thực dữ liệu) giúp Agent trả lời dựa trên thông tin thực tế từ internet.

## 🛠 Cú pháp Import
```python
from google.adk.tools import google_search
```

## ⚠️ Giới hạn quan trọng (Critical Limitation)
- **Single Tool Limitation**: Tại thời điểm này, công cụ `google_search` **chỉ có thể được sử dụng duy nhất một mình** trong một thực thể Agent.
- **Tương thích**: Chỉ tương thích với các model **Gemini 2** (ví dụ: `gemini-2.0-flash`).

## 💡 Giải pháp Multi-Agent (Workaround)
Để kết hợp tìm kiếm với các công cụ khác (như truy vấn Odoo), cần sử dụng mô hình **Multi-Agent** hoặc **Team**:
1. Một Agent chuyên trách `google_search`.
2. Các Agent khác chuyên trách logic nghiệp vụ.
3. Một Agent chính (Manager/Director) điều phối các Agent trên.

## 📝 Yêu cầu hiển thị (Grounding Suggestions)
Khi sử dụng công cụ này, nếu có "Search suggestions" trả về trong `renderedContent`, ứng dụng cần hiển thị các gợi ý đó cho người dùng theo chính sách của Google.

## 🚀 Ví dụ khởi tạo
```python
from google.adk.agents import Agent
from google.adk.tools import google_search

search_agent = Agent(
    name="search_specialist",
    model="gemini-2.0-flash",
    description="Chuyên gia tra cứu thông tin internet.",
    instruction="Sử dụng google_search để tìm câu trả lời mới nhất.",
    tools=[google_search] # Chỉ được dùng duy nhất 1 tool này
)
```
