# Google ADK Best Practices (TRCF Wisdom)

Tài liệu này lưu trữ các nguyên tắc thiết kế và triển khai AI Agent sử dụng Google ADK để đạt hiệu quả cao nhất.

## 1. Thiết kế Tools (Function Calling)
- **Type Hinting**: Luôn khai báo Type Hint đầy đủ cho tham số (VD: `start_date: str = ""`). ADK dựa vào đây để sinh JSON Schema chính xác.
- **Docstring chuẩn**: Mô tả chi tiết chức năng và các tham số. AI sẽ đọc docstring này để quyết định "khi nào" và "như thế nào" để gọi tool.
- **Dữ liệu tối giản**: Chỉ trả về những thông tin thực sự cần thiết. Tránh trả về hàng ngàn dòng dữ liệu thô làm tràn context window của LLM.
- **Format Output**: Nên có hàm helper để format dữ liệu trả về thành Markdown đẹp (bảng, danh sách) giúp AI dễ trình bày lại cho người dùng.

## 2. Thiết kế Prompt (SYSTEM_INSTRUCTION)
- **Vai trò rõ ràng**: Định nghĩa rõ Agent là ai (VD: "Bạn là chuyên gia phân tích kinh doanh của chuỗi CoffeeTree").
- **Giới hạn phạm vi**: Chỉ dẫn rõ Agent không được trả lời các vấn đề ngoài chuyên môn.
- **Ví dụ (Few-shot)**: Đưa vào 2-3 ví dụ về cặp câu hỏi/trả lời mẫu để Agent bắt chước tông giọng và phong cách.

## 3. Quản lý Session & Performance
- **Model**: Ưu tiên sử dụng `gemini-2.0-flash-lite` cho các tác vụ thông thường để tối ưu tốc độ và chi phí.
- **Async Safety**: Khi tích hợp vào Odoo, đảm bảo các hàm tool không gây block thread chính. Sử dụng wrapper đồng bộ - bất đồng bộ chuẩn.

## 4. Bảo mật Code (Cython Protection)
- **Tách biệt dữ liệu nhạy cảm**: Tuyệt đối không để `SYSTEM_INSTRUCTION` (Prompt) trực tiếp trong file `agent.py` hay `mail_message.py`. Hãy luôn đưa vào `prompts.py`.
- **Hàm bọc Prompt**: Thay vì biến string toàn cục, hãy dùng hàm trả về string (VD: `get_instruction()`) trong `prompts.py`. Điều này giúp Cython mã hoá chuỗi tốt hơn.
- **Cấu trúc Import**: `agent.py` sẽ import từ `business_logic` và `prompts`. Khi 2 file này đã được compile thành nhị phân, logic vẫn chạy bình thường nhưng code gốc đã được giấu.
- **Workflow biên dịch**:
  1. Viết code `.py`.
  2. Dùng Cython biên dịch sang `.c`.
  3. Dùng GCC/Clang biên dịch sang `.so` / `.pyd`.
  4. Xoá file `.py` gốc trước khi bàn giao cho khách hàng.

*(Cập nhật thêm trong quá trình phát triển...)*
