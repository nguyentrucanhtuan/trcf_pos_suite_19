---
description: /trcf_create_owl_component - Tạo OWL Component chuẩn Odoo 19
---

Workflow này giúp tạo nhanh một thành phần giao diện OWL (Javascript + XML) và đăng ký vào hệ thống Odoo 19.

### Các thực hiện:

1.  **Xác định vị trí**: Thường đặt trong `static/src/components/[component_name]/`.
2.  **Tạo file Logic (`.js`)**:
    - Sử dụng ESM (import/export).
    - Định nghĩa class kế thừa từ `@odoo/owl`.
    - Sử dụng `setup()` và các hooks (`useState`, `useService`).
3.  **Tạo file Template (`.xml`)**:
    - Sử dụng `<t t-name="...">` và cú pháp OWL chuẩn (`t-if`, `t-foreach`, `t-on-click`).
    - Đảm bảo template ID khớp với `static template` khai báo trong JS.
4.  **Đăng ký Assets**:
    - Tự động thêm đường dẫn file vào `__manifest__.py` dưới mục `assets/web.assets_backend`.
    - Kiểm tra thứ tự load file nếu có phụ thuộc.
5.  **Đăng ký Registry & Hooks**:
    - Sử dụng `useService` để gọi các dịch vụ chuẩn (orm, action, notification).
    - Đăng ký vào đúng category (fields, views, actions, services).
6.  **Hoàn tất**: Giải thích ngắn gọn cách sử dụng component vừa tạo trong các view XML (VD: dùng `widget` hay `component` tag).
