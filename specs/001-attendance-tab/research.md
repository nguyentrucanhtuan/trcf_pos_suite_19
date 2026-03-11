# Phase 0 Research: Attendance Tab Feature

**Feature**: 001-attendance-tab  
**Date**: 2026-03-05

---

## 1. Existing Route & Template Architecture

### Decision
Trang `/dang-ky-ca` đã được triển khai dưới dạng **Odoo HTTP Controller** (không dùng portal Odoo chuẩn) trong module `trcf_fnb_staff`. Template QWeb standalone (không extend `web.frontend_layout` ngoại trừ trang lỗi).

### Findings
- **Controller**: `trcf_fnb_staff/controllers/trcf_shift_registration_controller.py`  
  - Route chính: `GET /dang-ky-ca` → render template `shift_registration_form`
  - API endpoints: `POST /dang-ky-ca/save`, `POST /dang-ky-ca/remove` (JSON-RPC)
- **Template**: `trcf_fnb_staff/views/trcf_shift_registration_templates.xml`  
  - ID: `shift_registration_form`
  - Trang đứng độc lập với custom CSS: `static/src/css/shift_registration.css`

### Rationale
Giữ nguyên kiến trúc controller + QWeb template. Thêm tab bằng HTML/JS thuần trong template hiện tại — không cần route mới, chỉ thêm `?tab=attendance` query param để controller truyền dữ liệu giờ công.

---

## 2. Attendance Data Fields (đã có trên hr.attendance extended)

### Decision
Tất cả dữ liệu cần thiết cho bảng giờ công đã được tính toán sẵn trong model `hr.attendance` mở rộng của module hiện tại.

### Findings

| Cột bảng | Field nguồn | Model |
|----------|-------------|-------|
| Ngày | `check_in.date()` | `hr.attendance` |
| Giờ vào | `check_in` | `hr.attendance` |
| Giờ ra | `check_out` | `hr.attendance` |
| Thời gian làm việc | `worked_hours` | `hr.attendance` |
| Đi (trễ/sớm) | `check_in_status` | `hr.attendance` (computed) |
| Về (trễ/sớm) | `check_out_status` | `hr.attendance` (computed) |
| Lương phiên | `trcf_hourly_salary_sum` | `hr.attendance` (computed) |
| Đơn giá | `trcf_hourly_salary_display` → `employee_id.trcf_hourly_salary` | `hr.employee` |

### Formula
`trcf_hourly_salary_sum` = `worked_hours × employee_id.trcf_hourly_salary`  
Đã compute + store sẵn → chỉ cần query và hiển thị.

---

## 3. Tab Navigation Strategy

### Decision
Dùng **HTML tab thuần** (không dùng framework) với state quản lý bằng CSS class + JavaScript inline. Phù hợp với kiến trúc hiện tại (không có OWL component trên trang này).

### Alternatives Considered
- **URL query param `?tab=attendance`**: Đơn giản nhưng gây reload page khi chuyển tab → UX kém.
- **JavaScript tab switching (chosen)**: Chuyển tab không reload, dữ liệu tháng load via fetch AJAX khi cần.
- **OWL Component**: Quá phức tạp cho trang standalone này, không phù hợp.

---

## 4. Attendance Data Loading Strategy

### Decision
Thêm route mới `GET /dang-ky-ca/gió-cong-thang` (JSON) để trả về dữ liệu giờ công theo tháng. Tab Bảng giờ công fetch dữ liệu này via AJAX khi được kích hoạt lần đầu, cache trong biến JS. Tháng/năm được gửi qua query params.

### Rationale
- Không reload trang khi chuyển tab
- Dữ liệu chỉ được fetch khi nhân viên mở tab đó (lazy loading)
- Dễ test endpoint riêng lẻ

---

## 5. Security

### Findings
- Route `/dang-ky-ca` đã có `auth='user'` → chỉ user đã đăng nhập mới truy cập.
- Data filter `employee_id = request.env.user.employee_id` đã được áp dụng trong controller hiện tại.
- Route mới cần thêm filter tương tự — không dùng `.sudo()` không cần thiết.

### Decision
Route JSON mới sẽ dùng `auth='user'` và filter `employee_id` từ session — **không** expose dữ liệu nhân viên khác.

---

## 6. NEEDS CLARIFICATION resolved

Tất cả clarifications đã được giải quyết qua `/speckit.clarify`:
- ✅ Tổng lương: tạm tính từ `trcf_hourly_salary_sum`
- ✅ Không có ca → Đi/Về hiển thị "–"
- ✅ Đơn giá từ `trcf_hourly_salary_display`
- ✅ Mỗi hàng = 1 phiên `hr.attendance`
- ✅ Lương phiên + footer tổng tháng
