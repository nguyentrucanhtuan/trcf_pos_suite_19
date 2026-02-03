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
| Test module đầy đủ? | [TESTING_CHECKLIST.md](references/TESTING_CHECKLIST.md) |
| Gặp lỗi? | [TROUBLESHOOTING.md](references/TROUBLESHOOTING.md) |
| Cần best practices? | [BEST_PRACTICES.md](references/BEST_PRACTICES.md) |

## ⚙️ Verification & Testing

### Quick Verification Commands

```bash
# Install module mới
./odoo-bin -c odoo19.conf -d <database> -i <tên_module> --stop-after-init

# Update module sau khi sửa code
./odoo-bin -c odoo19.conf -d <database> -u <tên_module> --stop-after-init

# Development mode - auto reload XML/CSS/JS
./odoo-bin -c odoo19.conf -d <database> --dev=xml,css,js

# Debug mode với Python debugger
./odoo-bin -c odoo19.conf -d <database> --dev=all

# Enable SQL query logging (check performance)
./odoo-bin -c odoo19.conf -d <database> --log-sql

# Shell mode để test code trực tiếp
./odoo-bin shell -c odoo19.conf -d <database>
```

### Log Checking

Sau khi chạy lệnh, kiểm tra:
- ✅ Không có `ERROR` hoặc `CRITICAL` trong log
- ✅ Thấy message: `Module <tên_module>: successfully installed/updated`
- ✅ Không có warning về missing dependencies
- ✅ Views load thành công (check browser console)

### Comprehensive Testing

Xem chi tiết: [TESTING_CHECKLIST.md](references/TESTING_CHECKLIST.md)

**Quick checklist:**
- [ ] Module install/upgrade thành công
- [ ] All views render correctly
- [ ] Business logic hoạt động
- [ ] JavaScript components function
- [ ] Security/access rights đúng
- [ ] Performance acceptable

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
