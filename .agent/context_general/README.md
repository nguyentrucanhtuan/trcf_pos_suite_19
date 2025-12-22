# General Coding Conventions

Tài liệu quy chuẩn lập trình chung cho dự án.

## 🐍 Python Style
- Tuân thủ **PEP 8**.
- Sử dụng **4 spaces** cho thụt lề (indentation).
- Đặt tên biến/hàm theo kiểu `snake_case`.
- Đặt tên class theo kiểu `PascalCase`.
- Luôn có Docstring cho các hàm và class phức tạp.

## 📄 Odoo Standards
- **Prefix**: Mọi module và model mới phải bắt đầu bằng `trcf_`.
- **Fields**: Các trường quan trọng nên có `tracking=True` (chatter).
- **Translations**: Sử dụng `_('Text')` để hỗ trợ đa ngôn ngữ.

## 📜 XML / OWL
- **Views XML**: Đặt tên file theo định dạng `model_name_views.xml`.
- **CSS**: Sử dụng tiền tố để tránh xung đột styles.
- **Odoo 19**: Ưu tiên sử dụng component OWL hiện đại.

## 🛠️ Git Workflow
- **Commit Message**: `[Feature/Fix/Refactor] Mô tả ngắn gọn bằng tiếng Việt/Anh`.
- **Branching**: `feature/name-of-task` hoặc `fix/issue-id`.
