# Các Khái niệm Cốt lõi & Thiết lập ADK

## 1. Cài đặt
```bash
pip install google-adk
```

## 2. Cấu trúc Dự án (Tiêu chuẩn ADK)
Khi chạy lệnh `adk create my_agent`, hệ thống sẽ tạo ra:
- `app.yaml`: Cấu hình ứng dụng (tên app, danh sách agents).
- `agents/`: Thư mục chứa định nghĩa các agent (file Python).
- `tools/`: Thư mục tùy chọn cho các hàm công cụ (custom tools).

## 3. Tích hợp với Odoo (Mô hình tùy chỉnh)
Trong Odoo, chúng ta không dùng cấu trúc dự án CLI tiêu chuẩn mà tích hợp trực tiếp:
- **Agent Package**: Tạo một thư mục riêng trong `models/agents/`.
- **Bridge Model**: Sử dụng một class Python để bọc ADK agent, truyền Odoo `env` vào để truy vấn dữ liệu.
- **Xử lý Async**: Backend Odoo chạy đồng bộ (sync), trong khi ADK chạy bất đồng bộ (async). Sử dụng `asyncio.run()` để làm cầu nối.

## 4. Kiến trúc Thành phần
- **Agent**: "Bộ não" xử lý (bao gồm chỉ dẫn/instruction + bộ công cụ/tools).
- **Runner**: "Động cơ" thực thi agent.
- **Session**: "Phiên làm việc" hoặc luồng hội thoại của người dùng.
- **Memory**: Bộ nhớ lưu trữ ngữ cảnh dài hạn (tùy chọn).
