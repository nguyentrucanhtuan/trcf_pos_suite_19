<!-- SYNC IMPACT REPORT
Version change: none → 1.0.0 (initial ratification)
Added sections:
  - Core Principles (6 principles)
  - Additional Constraints (Security Requirements)
  - Development Workflow (CI/CD)
  - Governance
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ (reviewed, aligned)
  - .specify/templates/spec-template.md ✅ (reviewed, aligned)
  - .specify/templates/tasks-template.md ✅ (reviewed, aligned)
Deferred TODOs:
  - TODO(RATIFICATION_DATE): Lấy ngày chính xác từ lần commit đầu tiên
-->

# Odoo 19 Community Modules Constitution

## Core Principles

### I. Odoo 19-First (BẮT BUỘC)

Mọi phát triển PHẢI bám sát theo các phương pháp hay nhất và kiến trúc của Odoo 19
Community Edition.

- Ưu tiên sử dụng các module, API và công cụ gốc của Odoo trước khi xem xét giải pháp tùy chỉnh.
- Tùy chỉnh CHỈ ĐƯỢC triển khai khi không thể đáp ứng yêu cầu bằng chức năng tiêu chuẩn của Odoo.
- Mọi thay đổi phải tương thích ngược với Odoo 19 Community và không gây xung đột với
  các module core.
- Khi Odoo cung cấp một cơ chế (wizard, onchange, compute field, v.v.), ta PHẢI dùng cơ chế đó.

### II. Backend UX/UI — Odoo 19 Design System (BẮT BUỘC)

Giao diện quản trị (backend) của tất cả module PHẢI tuân thủ nghiêm ngặt các nguyên tắc
thiết kế UX/UI của Odoo 19 Community.

- Bố cục, thành phần (widget, button, form view, list view, kanban) và luồng người dùng PHẢI
  nhất quán với giao diện Odoo chuẩn.
- Không tự ý thêm CSS/JS tùy chỉnh vào backend nếu Odoo đã cung cấp widget hoặc view tương đương.
- Mọi trường hiển thị, nhãn, tooltip PHẢI được dịch (i18n) theo chuẩn `_("...")` của Odoo.

### III. Frontend UX/UI — QWeb + OWL + Tailwind CSS (BẮT BUỘC)

Giao diện web (frontend) công khai hoặc nhúng của module PHẢI tuân thủ QWeb và OWL.

- Component OWL PHẢI được viết theo kiến trúc Reactivity đúng chuẩn Odoo 19 (hooks, state, props).
- Tailwind CSS ĐƯỢC sử dụng để tạo giao diện hiện đại, responsive và tối ưu đa thiết bị.
- Không sử dụng JavaScript framework bên ngoài (React, Vue, Angular) trừ khi có quyết định
  kiến trúc được phê duyệt.
- Mọi template QWeb PHẢI có fallback graceful khi dữ liệu trống.

### IV. Chất lượng Mã & Dễ Bảo trì (BẮT BUỘC)

Mã nguồn PHẢI rõ ràng, dễ đọc và dễ bảo trì.

- Tuân thủ PEP8 cho Python và quy ước XML chuẩn của Odoo 19 (thụt lề 4 space, attribute ordering).
- Mọi method có logic nghiệp vụ phức tạp PHẢI có docstring mô tả mục đích, tham số, kết quả trả về.
- Tên biến, method, field PHẢI có nghĩa rõ ràng — không dùng tên viết tắt không rõ ràng (e.g., `fn`, `tmp`).
- Không commit code bị comment-out hoặc debug statement (`print`, `pdb`).
- Mỗi module PHẢI có `README.md` mô tả mục đích, phụ thuộc và hướng dẫn cài đặt.

### V. Hiệu suất & Tối ưu hóa (BẮT BUỘC)

Tất cả hoạt động quan trọng PHẢI được tối ưu để đảm bảo thời gian phản hồi nhanh.

- Truy vấn ORM PHẢI dùng `domain`, `fields`, `limit` tối thiểu cần thiết — tránh `search()` không có
  điều kiện trên bảng lớn.
- Dùng `precompute=True` cho compute fields không phụ thuộc record khác khi có thể.
- Dùng `models.Index` cho các trường dùng làm filter/search thường xuyên.
- Xử lý batch (>100 records) PHẢI dùng `env.cr.execute()` hoặc `write()` theo batch, không loop
  từng record.
- Cache kết quả tính toán nặng bằng `@tools.ormcache` khi phù hợp.

### VI. Khả năng Mở rộng & Bảo trì Dài hạn (BẮT BUỘC)

Thiết kế và triển khai module PHẢI tính đến khả năng mở rộng trong tương lai.

- Mọi module PHẢI thiết kế theo hướng loosely coupled — không hard-code dependency vào module
  khác nếu có thể dùng `ir.config_parameter` hoặc selection field.
- Business logic phức tạp PHẢI được tách thành service layer hoặc mixin để tái sử dụng.
- Schema thay đổi (thêm field, table) PHẢI đi kèm migration script trong `migrations/`.
- Hằng số cấu hình PHẢI được đặt ở cấp module (không hard-code trong method).

## Ràng buộc Bảo mật

Mọi module xử lý dữ liệu nhạy cảm PHẢI thực thi các biện pháp bảo mật sau:

- **SQL Injection**: TUYỆT ĐỐI không dùng string format/concatenation trong `env.cr.execute()`.
  Luôn dùng parameterized queries: `env.cr.execute("SELECT ... WHERE id = %s", (record_id,))`.
- **XSS**: Mọi dữ liệu user-generated hiển thị trên frontend PHẢI được escape đúng cách qua
  QWeb `t-esc` (không dùng `t-raw` trừ trường hợp đặc biệt được phê duyệt).
- **Phân quyền**: Mọi model PHẢI có file `security/ir.model.access.csv` và record rules phù hợp.
  `sudo()` chỉ được dùng khi thực sự cần thiết và PHẢI có comment giải thích lý do.
- **Dữ liệu nhạy cảm**: Mật khẩu, token, API key PHẢI lưu qua `ir.config_parameter` hoặc
  field `password` — không lưu plain text trong code hay config file.
- **CSRF**: Controller HTTP PHẢI sử dụng `csrf=True` (mặc định) hoặc có justification rõ ràng.

## Quy trình Phát triển

### CI/CD Pipeline

Dự án PHẢI triển khai quy trình CI/CD để tự động hóa kiểm thử, build và triển khai.

- **Kiểm thử tự động**: Mọi module PHẢI có test suite trong `tests/` với coverage tối thiểu cho
  các business logic quan trọng. Chạy bằng `python -m pytest` hoặc Odoo test runner.
- **Lint & Format**: Code PHẢI pass `flake8` (Python) và `xmllint` (XML) trước khi merge.
- **Build gate**: CI pipeline PHẢI chặn merge nếu có lỗi `ERROR` hoặc `CRITICAL` trong Odoo
  server log khi cài đặt/nâng cấp module.
- **Triển khai**: Deployment PHẢI thực hiện qua script tự động (không manual copy) với bước
  `--update` module và kiểm tra log sau deploy.
- **Môi trường**: Phân tách rõ ràng: `dev` → `staging` → `production`. Không deploy thẳng lên
  production mà không qua staging.

### Quy trình Review

- Mọi thay đổi code PHẢI được review bởi ít nhất 1 developer khác trước khi merge.
- PR description PHẢI mô tả: mục đích thay đổi, cách test, ảnh hưởng schema (nếu có).
- Migration script (nếu có) PHẢI được review kỹ trước khi chạy trên production.

## Governance

Constitution này là tài liệu tối cao và ràng buộc mọi quyết định phát triển trong dự án.

- **Tuân thủ bắt buộc**: Mọi PR/code review PHẢI xác minh tuân thủ các nguyên tắc trên.
  Complexity không được phép tồn tại nếu không có justification rõ ràng.
- **Quy trình sửa đổi**: Sửa đổi constitution PHẢI được đề xuất qua `/speckit.constitution`,
  mô tả rõ lý do và impact, được team lead phê duyệt trước khi áp dụng.
- **Versioning**: Dùng Semantic Versioning — MAJOR: bỏ/đổi nguyên tắc, MINOR: thêm nguyên tắc,
  PATCH: làm rõ/sửa câu từ.
- **Review định kỳ**: Constitution được review mỗi quý hoặc khi có thay đổi kiến trúc lớn.
- **Hướng dẫn phát triển**: Tham khảo `.agents/skills/trcf-odoo19-module/SKILL.md` cho
  runtime development guidance chi tiết.

**Version**: 1.0.0 | **Ratified**: 2026-03-01 | **Last Amended**: 2026-03-01
