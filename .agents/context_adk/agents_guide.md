# Hướng dẫn về ADK Agents

## 1. Các loại Agent

### LLM Agents (`Agent`, `LlmAgent`)
- **Engine**: Sử dụng Gemini (khuyên dùng bản 2.0-flash-lite).
- **Điều khiển**: Thông qua Chỉ dẫn (Instructions) và gọi công cụ (Tool calling) linh hoạt.
- **Sử dụng**: Cho các tác vụ linh hoạt, dựa trên ngôn ngữ tự nhiên.

### Workflow Agents
Dùng cho các luồng xử lý cố định, có thể dự đoán được mà không cần LLM điều hướng:
- **SequentialAgent**: Thực thi các agent nối tiếp nhau.
- **ParallelAgent**: Thực thi đồng thời nhiều agent.
- **LoopAgent**: Lặp lại một agent dựa trên một điều kiện nhất định.

### 🔹 business_logic.py & prompts.py (IP Protection)
Đây là hai file quan trọng nhất chứa "chất xám" (Prompt và Logic xử lý dữ liệu).
- **Phân tách**: Luôn tách rời logic lấy dữ liệu Odoo ra khỏi file bridge `agent.py`.
- **Cython Ready**: Viết code sạch, hạn chế dùng các shortcut Python quá mức để Cython biên dịch sang C đạt hiệu năng và bảo mật cao nhất.
- **Biên dịch**: Sau khi hoàn thiện, bạn sẽ dùng Cython biên dịch 2 file này thành file nhị phân (`.so` trên Linux/Mac, `.pyd` trên Windows). Khi đó, người dùng mở file sẽ chỉ thấy mã máy, không thể thấy Prompt hay logic gốc.

### Custom Agents
- Kế thừa từ `BaseAgent` để tự định nghĩa logic điều khiển riêng hoặc tích hợp chuyên biệt.

## 2. Cấu hình LLM Agent
```python
from google.adk.agents import Agent

agent = Agent(
    name="tro_ly_cua_toi",
    model="gemini-2.0-flash-lite",
    instruction="Bạn là một trợ lý hữu ích.",
    tools=[ham_cong_cu_cua_toi],
    # Nâng cao
    input_schema=InputModel,
    output_schema=OutputModel,
    code_execution=True  # Bật công cụ thực thi code có sẵn
)
```

## 3. Quy trình thực hiện (5 Bước)

1. **Cấu trúc thư mục**: 
   - **Cấu trúc thư mục**: 
```text
your_module/
├── models/
│   ├── agents/
│   │   └── [agent_name]/
│   │       ├── __init__.py
│   │       ├── agent.py            # Bridge (Không mã hoá - Giữ để Odoo gọi)
│   │       ├── business_logic.py   # Core Logic (Biên dịch sang .so/.pyd)
│   │       ├── prompts.py          # Prompt (Biên dịch sang .so/.pyd)
│   │       └── ...
```
2. **Đăng ký Registry**: Thêm Agent vào `models/base/agent_registry.py`.
3. **Mail Hook**: Kế thừa `mail.message` để bắt tin nhắn từ Discuss.
4. **Tools Mapping**: Khai báo Type Hint và Docstring rõ ràng trong `business_logic.py`.
5. **Kiểm tra**: Dùng `python3 -m py_compile` kiểm tra cú pháp trước khi nạp vào Odoo.

## 4. Tài liệu bổ trợ
Để đảm bảo Agent hoạt động ổn định và thông minh hơn, hãy tham khảo các tài liệu chuyên biệt sau:

- 💡 **[Best Practices](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/.agent/context_adk/best_practices.md)**: Các nguyên tắc thiết kế Tool và Prompt.
- 🛠 **[Troubleshooting](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/.agent/context_adk/troubleshooting.md)**: Nhật ký lỗi và cách khắc phục nhanh.
- 🎓 **Cơ chế Tự học**: Xem phần "Self-Learning" trong Best Practices để triển khai Feedback Loop.
