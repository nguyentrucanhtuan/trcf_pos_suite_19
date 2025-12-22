# 📄 Odoo ADK Agent Templates

Bộ templates chuẩn cho các module tích hợp Google ADK Agent và Odoo 19.

## 📁 Cấu trúc đặc thù
Bộ template này tuân thủ cấu trúc tách biệt để bảo mật code (Cython-ready):
- `prompts.py`: Chứa System Instructions (CÓ THỂ compile).
- `business_logic.py`: Chứa các Tool functions (CÓ THỂ compile).
- `agent.py`: Chứa runner và agent setup (KHÔNG compile).

## 🚀 Cách dùng
Dùng lệnh `/trcf_adk_agent_create` để AI tự động áp dụng bộ template này.

## ⚠️ Lưu ý kỹ thuật
- **Imports**: Luôn dùng `google.adk` và `google.genai` (tránh `adk` cũ).
- **Return Type**: Toàn bộ tool functions phải trả về `dict`.
- **Runner**: Sử dụng pattern `Runner` + `InMemorySessionService` chính thức.
