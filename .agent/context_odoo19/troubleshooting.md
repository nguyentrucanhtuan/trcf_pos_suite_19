# Odoo 19 Troubleshooting & Bug Fixes

Tài liệu này là nhật ký ghi lại các lỗi kỹ thuật và cách khắc phục trong quá trình phát triển Odoo 19.

> [!TIP]
> **Quy tắc cho Antigravity**: Mỗi khi bạn giải quyết xong một lỗi phức tạp hoặc phát hiện một "bẫy" (pitfall) của Odoo 19, hãy cập nhật ngay vào file này.

## 1. Lỗi Giao diện (UI/XML)

### Thẻ `<tree>` không hoạt động hoặc báo lỗi
- **Hiện tượng**: Giao diện không load hoặc báo lỗi parser.
- **Nguyên nhân**: Odoo 19 đã chuyển sang dùng `<list>`.
- **Khắc phục**: Thay thế toàn bộ thẻ `<tree>` bằng `<list>`.

### Thuộc tính `attrs` bị lỗi
- **Hiện tượng**: Lỗi `Unknown attribute 'attrs'`.
- **Nguyên nhân**: Odoo 19 bỏ `attrs`.
- **Khắc phục**: Dùng `invisible="expression"`, `readonly="expression"`.

## 2. Lỗi Backend (Python/ORM)

### Lỗi truy cập `self._context`
- **Hiện tượng**: `AttributeError: 'model' object has no attribute '_context'`.
- **Nguyên nhân**: Không được dùng underscore attributes.
- **Khắc phục**: Chuyển sang dùng `self.env.context`.

## 3. Lỗi OWL/Javascript
*(Đang cập nhật...)*
