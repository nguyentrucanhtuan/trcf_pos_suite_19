---
name: odoo19-module-development
description: >
  Phát triển module Odoo ERP phiên bản 19+ theo tiêu chuẩn TRCF (Tuấn Rang Cà Phê).
  Use when: (1) Creating new Odoo modules, (2) Modifying/upgrading existing modules,
  (3) Debugging Odoo errors, (4) Writing OWL components for frontend,
  (5) Optimizing code, (6) Working with Models/Views/Security,
  (7) POS/Inventory/Sale/Purchase/HR/Accounting modules.
  Keywords: odoo, erp, module, python, owl, xml, pos, inventory, sale, purchase, hr, accounting, trcf.
---

# Phát triển Module Odoo 19

## 🚀 Quick Start: Tạo Module Mới

```
Task Progress:
- [ ] 1. Tạo cấu trúc thư mục từ template
- [ ] 2. Cấu hình __manifest__.py
- [ ] 3. Định nghĩa Model
- [ ] 4. Tạo Views (List, Form, Search)
- [ ] 5. Thiết lập Security
- [ ] 6. Kiểm tra module
```

### Cấu trúc thư mục chuẩn

Sử dụng template: [assets/module_template/](assets/module_template/)

```
trcf_[module_name]/
├── __init__.py
├── __manifest__.py
├── models/
│   ├── __init__.py
│   └── trcf_[model].py
├── views/
│   └── trcf_[model]_views.xml
├── security/
│   └── ir.model.access.csv
└── static/src/           # (nếu có OWL)
    ├── js/
    └── xml/
```

### Manifest chuẩn TRCF

```python
{
    'name': 'TRCF [Tên Module]',
    'version': '19.0.1.0.0',
    'author': 'Tuấn Rang Cà Phê',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/trcf_[model]_views.xml',
    ],
    'installable': True,
}
```

## 📋 Coding Standards (Quick Reference)

### Python Backend

| Quy tắc | Ví dụ |
|---------|-------|
| Model prefix | `_name = 'trcf.order'` |
| Bắt buộc `_description` | `_description = 'Đơn hàng TRCF'` |
| Create override | `@api.model_create_multi` |
| Environment | `self.env.user`, `self.env.context` |
| Error messages | `raise UserError("Lỗi bằng tiếng Việt")` |

### XML/Views

| Quy tắc | Ví dụ |
|---------|-------|
| List View | `<list>` (KHÔNG dùng `<tree>`) |
| Modifiers | `invisible="state == 'done'"` |
| Form | Header → Sheet → Chatter |
| Status | `widget="statusbar"` |

### OWL Components

| Quy tắc | Ví dụ |
|---------|-------|
| Imports | `import { Component } from "@odoo/owl"` |
| Services | `this.orm = useService("orm")` |
| State | `this.state = useState({...})` |
| RPC | `import { rpc } from "@web/core/network/rpc"` |

## 📚 References (Load khi cần)

| Cần làm gì? | Đọc file |
|-------------|----------|
| Viết Model, Fields, API? | [ORM_REFERENCE.md](references/ORM_REFERENCE.md) |
| Viết OWL Component? | [OWL_GUIDE.md](references/OWL_GUIDE.md) |
| Tạo Views XML? | [VIEWS_REFERENCE.md](references/VIEWS_REFERENCE.md) |
| Viết Controllers/Routes? | [CONTROLLERS_REFERENCE.md](references/CONTROLLERS_REFERENCE.md) |
| Gặp lỗi? | [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) |
| Cần best practices? | [BEST_PRACTICES.md](references/BEST_PRACTICES.md) |

## ⚙️ Verification

```bash
./odoo-bin -c odoo19.conf -u <tên_module> --stop-after-init
```

Kiểm tra log không có `ERROR` hoặc `CRITICAL`.

## ✅ Checklist Sạch Code

- [ ] Xóa code thừa, comment trống
- [ ] Docstring tiếng Việt
- [ ] Field tiền tệ: `Monetary` + `currency_field`
- [ ] `__init__.py` ở tất cả folder con
- [ ] File `ir.model.access.csv` đầy đủ

## 🔄 Cập nhật Tri thức

Khi phát hiện lỗi mới hoặc pattern hay → Cập nhật vào:
- `references/TROUBLESHOOTING.md` (lỗi)
- `references/BEST_PRACTICES.md` (kinh nghiệm)
