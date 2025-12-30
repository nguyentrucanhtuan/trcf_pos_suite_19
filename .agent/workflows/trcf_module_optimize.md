---
description: /trcf_module_optimize - Tối ưu hóa & Nâng cấp module Odoo 19
---

Workflow này dùng để rà soát, làm sạch và nâng cấp các module cũ hoặc code chưa chuẩn lên tiêu chuẩn Odoo 19 của TRCF.

### Các thực hiện:

1.  **Phân tích**: Đọc toàn bộ code của module được yêu cầu. Đối chiếu với `skills/odoo19_standard.md`.
2.  **Nâng cấp Syntax & Logic**:
    - Thay thế toàn bộ thẻ `<tree>` bằng `<list>`.
    - Chuyển đổi `attrs` sang thuộc tính trực tiếp (`invisible`, `readonly`, `required`).
    - Cập nhật hàm `create` dùng `@api.model_create_multi`.
    - Thay thế `self._uid`, `self._context`, `self._cr` bằng `self.env` tương ứng.
    - Cân nhắc chuyển `read_group` sang `_read_group` để tối ưu hiệu suất.
    - Đảm bảo các model đều có `_description`.
3.  **Làm sạch Code & Chuẩn hóa TRCF**:
    - Xóa các comment thừa, code rác.
    - Đảm bảo toàn bộ labels, help text và docstrings là tiếng Việt.
    - Thêm `tracking=True` cho các trường quan trọng nếu thiếu.
    - Kiểm tra và thêm `index=True` cho các trường hay dùng để tìm kiếm.
4.  **Kiểm tra Security & Manifest**:
    - Đảm bảo mọi model đều có access rights.
    - Kiểm tra `license: LGPL-3` và `depends` trong manifest.
5.  **Kiểm tra & Xác minh**:
    - Chạy lệnh nâng cấp module: `./odoo-bin -c odoo19.conf -u <tên_module> --stop-after-init`.
    - Kiểm tra terminal để đảm bảo không có lỗi (Error/Critical).
6.  **Báo cáo**: Liệt kê danh sách các thay đổi đã thực hiện và lý do tối ưu.
