---
description: /trcf_module_create - Tạo module Odoo 19 chuẩn TRCF
---

Sử dụng skill `odoo19-module-development` để tạo module.

### Quy trình:

1. **Thu thập yêu cầu**: Hỏi tên module và mô tả chức năng
2. **Đọc skill**: Load `skills/odoo19-module-development/SKILL.md`
3. **Tạo từ template**: Copy `assets/module_template/` thành `trcf_[tên_module]/`
4. **Customize**: Sửa model, views, security theo yêu cầu
// turbo
5. **Verify**: `./odoo-bin -c odoo19.conf -u <module> --stop-after-init`
6. **Báo cáo**: Liệt kê files đã tạo
