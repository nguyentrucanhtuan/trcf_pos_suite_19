# Agent Development Documentation

Tài liệu phát triển modules Odoo 19 với Google ADK Agent.

## 📁 Cấu trúc

```
custom_addons/.agent/
├── context_odoo19/             # Odoo 19 Documentation
│   ├── orm-reference.md        # ORM API, Fields
│   ├── views-reference.md      # Views (<list> không <tree>)
│   └── owl-components.md       # OWL Components
├── context_adk_agent/          # Google ADK Documentation
│   ├── core-concepts.md        # Khái niệm ADK
│   ├── odoo-integration.md     # Tích hợp Odoo
│   ├── best-practices.md       # Best practices
│   └── troubleshooting.md      # Xử lý lỗi
├── context_general/            # Coding Style, Git, Naming Conventions
├── docs/                       # Bảo mật Code (Cython) & Deployment
│   ├── protect_agent_prompts.md
│   ├── compile_tool_logic.md
│   └── cython_compilation.md
├── templates/                  # Module Templates
│   ├── odoo19_standard/        # 🆕 Standard Odoo 19 (CRUD, Business)
│   └── odoo19_adk_agent/       # ⏳ ADK Agent (AI Integration)
├── skills/                     # 🧠 AI Skills (Kỹ năng & Tư duy)
│   ├── odoo19_standard.md      # Skill viết code Odoo 19 chuẩn
│   └── adk_agent.md            # 🆕 Skill phát triển AI Agent (ADK)
└── workflows/                  # Quy trình làm việc & /slash commands
    ├── trcf_module_create.md   # /trcf_module_create - Tạo module
    ├── trcf_module_optimize.md # /trcf_module_optimize - Tối ưu/Nâng cấp
    └── trcf_adk_agent_create.md# /trcf_adk_agent_create - Tạo AI Agent
```

## 🚀 Workflows

| Command | Mô tả |
|---------|-------|
| `/trcf_module_create` | Tạo module Odoo 19 mới |
| `/trcf_module_optimize` | Tối ưu + Nâng cấp module |
| `/trcf_adk_agent_create` | Tạo module với Google ADK Agent |

## 📚 Tham khảo

- **Odoo 19**: `context_odoo19/` (ORM, Views, OWL)
- **Google ADK**: `context_adk_agent/` (Agent, Tools, Runner)
- **Bảo mật**: `docs/` (Cython compilation)
- **Chuẩn chung**: `context_general/`

## 🏗️ Conventions

- **Prefix**: `trcf_`
- **Author**: Tuấn Rang Cà Phê
- **License**: LGPL-3
- **Odoo 19**: Dùng `<list>` thay `<tree>`
