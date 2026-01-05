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

### Lỗi `Service rpc is not available` hoặc `this.env.services.rpc is not a function`
- **Hiện tượng**: Không thể gọi được RPC trong component OWL.
- **Nguyên nhân**: Trong Odoo 19, `rpc` không còn là một service được đăng ký nữa.
- **Khắc phục**: Import trực tiếp `rpc` từ module:
  ```javascript
  import { rpc } from "@web/core/network/rpc";
  // Sử dụng: await rpc("/url", params);
  ```

### Lỗi JS không cập nhật code mới (Cache)
- **Hiện tượng**: Sửa code JS/XML nhưng trình duyệt vẫn báo lỗi cũ hoặc không đổi giao diện.
- **Khắc phục**: 
  - Dùng **Cmd + Shift + R** (Mac) hoặc **Ctrl + F5** (Win) để Hard Refresh.
  - Xóa "Clear site data" trong tab Application của DevTools nếu cần.

## 4. Bảo mật & Iframe

### Lỗi `X-Frame-Options: deny` khi nhúng website vào Iframe
- **Hiện tượng**: Iframe bị trắng hoặc báo lỗi bảo mật từ chối hiển thị.
- **Nguyên nhân**: Odoo mặc định chặn việc nhúng giao diện vào iframe.
- **Khắc phục**:
  1. Thêm `allow_frames=True` vào decorator của route:
     ```python
     @http.route('/my/route', ..., allow_frames=True)
     ```
  2. Kích hoạt System Parameter: `web.browser_security_disable_x_frame_options` = `True`.
  3. **Tối ưu**: Nếu nhúng giữa các component OWL của chính mình, hãy nhúng trực tiếp bằng Component con (sub-component) thay vì Iframe để tránh lỗi nạp module JS.
