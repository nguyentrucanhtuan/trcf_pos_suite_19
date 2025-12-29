---
description: /trcf_module_create - Tạo module Odoo 19 chuẩn TRCF
---

Workflow này hướng dẫn Antigravity cách tạo một module Odoo 19 mới với đầy đủ cấu trúc và tiêu chuẩn của dự án Tuấn Rang Cà Phê.

### Các thực hiện:

1.  **Thu thập thông tin**: Hỏi người dùng về tên module (ví dụ: `inventory_check`) và mô tả ngắn gọn.
2.  **Khởi tạo cấu trúc folder**:
    - Tạo folder chính `trcf_[module_name]`.
    - Tạo các folder con: `models/`, `views/`, `security/`, `data/`, `static/`.
3.  **Tạo file cấu hình**:
    - Tạo `__manifest__.py` với:
        - `name`: "TRCF [Tên mô tả]"
        - `author`: "Tuấn Rang Cà Phê"
        - `license`: "LGPL-3"
        - `depends`: `['base', 'mail']` (mặc định)
    - Tạo `__init__.py` ở root và trong folder `models/`.
4.  **Tạo Model & View mẫu (Standard)**:
    - Tạo một model cơ bản kế thừa `mail.thread`.
    - Phải có `_description` và đặt tên model bắt đầu bằng `trcf.`.
    - Tạo một view danh sách dùng thẻ `<list>` và một form view có `<header>` + `<sheet>` + `<chatter>`.
    - Sử dụng các thuộc tính trực tiếp (`invisible`, `readonly`) thay vì `attrs`.
5.  **Thiết lập Bảo mật**:
    - Tạo file `security/ir.model.access.csv` cấp quyền full cho `base.group_user`.
    - Đảm bảo model được đăng ký đúng trong file access.
6.  **Review & Hoàn thiện**:
    - Kiểm tra lại toàn bộ file theo dúng chuẩn trong `skills/odoo19_standard.md`.
    - Đảm bảo file `__init__.py` có mặt ở tất cả các folder logic (`models`, `controllers`).

// turbo
7. **Thông báo**: Sau khi tạo xong, liệt kê các file đã tạo và hướng dẫn người dùng cách cài đặt.
