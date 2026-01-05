# Google ADK Troubleshooting & Bug Fixes

Nhật ký ghi lại các lỗi thường gặp và cách khắc phục khi làm việc với Google ADK Agents trong Odoo 19.

## 1. Lỗi Kết nối & API

### Lỗi `429 Resource Exhausted` hoặc Quota exceed
- **Hiện tượng**: Agent không trả lời, log ghi lỗi 429.
- **Nguyên nhân**: Vượt quá giới hạn gọi API của Gemini bản miễn phí.
- **Khắc phục**: 
  - Đợi 1-2 phút rồi thử lại.
  - Cấu hình API Key Paid (Pay-as-you-go).
  - Tối ưu lại số lượng tin nhắn trong session.

### Lỗi `404 Model not found`
- **Hiện tượng**: Lỗi khi khởi tạo Agent.
- **Nguyên nhân**: Sai tên model hoặc region không hỗ trợ.
- **Khắc phục**: Kiểm tra lại `self.model_name`, ưu tiên `gemini-2.0-flash-lite`.

## 2. Lỗi Logic Agent

### Agent không gọi Tool dù đã được cung cấp
- **Hiện tượng**: Người dùng hỏi đúng vấn đề nhưng AI chỉ trả lời chung chung, không thực thi code.
- **Nguyên nhân**: Docstring của hàm tool mập mờ hoặc Type Hint thiếu chính xác.
- **Khắc phục**: Viết lại Docstring mô tả rõ: "Gọi tool này khi người dùng hỏi về...".

### Lỗi `RuntimeError: There is no current event loop`
- **Hiện tượng**: Crash khi gọi `asyncio.run()`.
- **Nguyên nhân**: Xung đột loop trong môi trường Odoo (thường là khi gọi lồng nhau).
- **Khắc phục**: Kiểm tra loop hiện tại trước khi khởi tạo mới:
  ```python
  try:
      loop = asyncio.get_event_loop()
  except RuntimeError:
      loop = asyncio.new_event_loop()
  ```

## 3. Lỗi Định dạng & Hiển thị

### AI trả về ngày tháng sai định dạng Odoo
- **Hiện tượng**: AI truyền `2024/01/01` vào tool trong khi Odoo cần `2024-01-01`.
- **Khắc phục**: Ghi rõ format yêu cầu trong `SYSTEM_INSTRUCTION` (VD: "Luôn truyền ngày tháng theo định dạng YYYY-MM-DD").

*(Cập nhật ngay mỗi khi phát hiện lỗi mới...)*
