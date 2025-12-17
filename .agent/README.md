# Agent Development Documentation

Tài liệu hướng dẫn phát triển modules cho Odoo với Google ADK Agent.

## 📁 Cấu trúc thư mục

```
custom_addons/.agent/
├── README.md                    # File này - Tổng quan
├── docs/                        # Tài liệu tham khảo
│   ├── google_adk_llms.txt     # Google ADK documentation (gốc)
│   ├── google_adk_reference.md # ADK reference (đã xử lý)
│   ├── architecture.md         # Kiến trúc tổng thể
│   ├── naming_conventions.md   # Quy tắc đặt tên
│   ├── module_structure.md     # Cấu trúc module chuẩn
│   ├── coding_standards.md     # Chuẩn code Python/JS/XML
│   ├── cython_compilation.md   # Chiến lược compile
│   └── odoo_patterns.md        # Patterns thường dùng
├── workflows/                   # Quy trình làm việc
│   ├── create_new_module.md    # Tạo module mới
│   ├── create_adk_agent.md     # Tạo ADK agent
│   └── compile_module.md       # Compile với Cython
├── templates/                   # Templates code
│   └── module_template/        # Template module đầy đủ
└── scripts/                     # Scripts tự động hóa
    └── create_module.py        # Script tạo module
```

## 🎯 Mục đích

Repository này chứa:

1. **Documentation** - Tài liệu về patterns, conventions, best practices
2. **Workflows** - Quy trình từng bước để thực hiện các tác vụ phổ biến
3. **Templates** - Code templates để bắt đầu nhanh
4. **Scripts** - Automation scripts để tăng tốc development

## 🚀 Quick Start

### Tạo module mới
```bash
# Xem workflow
cat custom_addons/.agent/workflows/create_new_module.md

# Hoặc dùng script (coming soon)
python custom_addons/.agent/scripts/create_module.py --name trcf_my_module
```

### Tạo ADK Agent module
```bash
# Xem workflow
cat custom_addons/.agent/workflows/create_adk_agent.md
```

## 📚 Tài liệu quan trọng

- **Google ADK**: `custom_addons/.agent/docs/google_adk_reference.md`
- **Odoo Patterns**: `custom_addons/.agent/docs/odoo_patterns.md`
- **Cython Strategy**: `custom_addons/.agent/docs/cython_compilation.md`

## 🏗️ Module Conventions

Tất cả modules trong `custom_addons/` follow:

- **Prefix**: `trcf_` (Tuấn Rang Cà Phê)
- **Structure**: Standard Odoo module structure
- **License**: LGPL-3
- **Author**: Tuấn Rang Cà Phê
- **Website**: https://coffeetree.vn

## 📝 Notes

- File `google_adk_llms.txt` là bản gốc từ Google, không nên chỉnh sửa
- Các file `.md` khác có thể cập nhật theo dự án
- Workflows được thiết kế để AI agent (Antigravity) đọc và thực thi

## 🤖 Sử dụng với Antigravity

Khi làm việc với Antigravity AI agent, bạn có thể:

1. **Reference workflows**: "Hãy follow workflow trong `.agent/workflows/create_adk_agent.md`"
2. **Reference docs**: "Hãy đọc `.agent/docs/google_adk_reference.md` để hiểu ADK"
3. **Use templates**: "Dùng template trong `.agent/templates/module_template/`"
