# Tasks: Trang /dang-ky-ca – Thêm Tab Bảng Giờ Công Tháng

**Branch**: `001-attendance-tab`  
**Input**: `specs/001-attendance-tab/` (spec.md, plan.md, research.md, data-model.md)  
**Module**: `trcf_fnb_staff`

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Có thể chạy song song (file khác nhau, không phụ thuộc nhau)
- **[Story]**: US1 = Xem bảng giờ công tháng, US2 = Lọc theo tháng, US3 = Tab Đăng ký ca không bị regression

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Chuẩn bị cấu trúc CSS, xem lại các file sẽ thay đổi

- [x] T001 Đọc hiểu toàn bộ template hiện tại `trcf_fnb_staff/views/trcf_shift_registration_templates.xml` (246 dòng) để nắm cấu trúc HTML
- [x] T002 [P] Đọc toàn bộ controller `trcf_fnb_staff/controllers/trcf_shift_registration_controller.py` để nắm pattern xử lý route hiện tại
- [x] T003 [P] Kiểm tra CSS hiện có `trcf_fnb_staff/static/src/css/shift_registration.css` để biết selector và variable đang dùng

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Thêm route JSON mới — không ảnh hưởng tab cũ, là nền tảng cho US1 và US2

**⚠️ CRITICAL**: US1 và US2 không thể test được nếu route này chưa có

- [x] T004 Thêm route `GET/POST /dang-ky-ca/gio-cong` vào controller `trcf_fnb_staff/controllers/trcf_shift_registration_controller.py`:
  - Import `fields` từ `odoo`
  - Query `hr.attendance` với domain `employee_id`, `check_in >= first_day`, `check_in < next_month`
  - Format từng record: `date`, `check_in`, `check_out`, `worked_hours_display` (Xh Ym), `check_in_status` (fallback "–"), `check_out_status` (fallback "–"), `salary_display`
  - Trả JSON `{'success': True, 'records': [...], 'total_salary_display': '...', 'month': m, 'year': y, 'is_provisional': True}`
  - Default: tháng/năm hiện tại nếu không truyền params
  - Auth: `auth='user'` (không dùng `.sudo()` không cần thiết)

**Checkpoint**: `curl -X POST http://localhost:8069/dang-ky-ca/gio-cong -H 'Content-Type: application/json' -d '{...}'` trả đúng JSON với records của nhân viên đang login ✅

---

## Phase 3: User Story 1 – Nhân viên xem bảng giờ công tháng hiện tại (Priority: P1) 🎯 MVP

**Goal**: Nhân viên mở `/dang-ky-ca`, thấy 2 tab, chọn "Bảng giờ công" và thấy đúng dữ liệu tháng hiện tại với 6 cột đầy đủ.

**Independent Test**: Đăng nhập Odoo → truy cập `/dang-ky-ca` → tab "Bảng giờ công" hiển thị bảng với đúng records của tháng hiện tại khớp với dữ liệu HR backend.

### Implementation cho User Story 1

- [x] T005 [US1] Thêm tab navigation HTML vào template `trcf_fnb_staff/views/trcf_shift_registration_templates.xml`
- [x] T006 [US1] Bọc toàn bộ nội dung bảng đăng ký ca hiện tại vào `<div id="panel-dang-ky-ca" class="tab-panel active">`
- [x] T007 [US1] Thêm panel "Bảng giờ công" với bộ lọc tháng/năm, bảng 7 cột, tbody để JS render động, footer tổng lương + nhãn "Tạm tính", empty state
- [x] T008 [US1] Thêm CSS cho tab UI vào `trcf_fnb_staff/static/src/css/shift_registration.css`
- [x] T009 [US1] Thêm JavaScript tab switching vào `<script>` trong template
- [x] T010 [US1] Thêm hàm `loadAttendanceData(month, year)` với fetch + loading spinner
- [x] T011 [US1] Thêm hàm `renderAttendanceTable(data)` với XSS-safe textContent rendering

**Checkpoint**: Mở `/dang-ky-ca`, click "Bảng giờ công" → bảng load đúng records tháng hiện tại ✅

---

## Phase 4: User Story 2 – Lọc bảng giờ công theo tháng khác (Priority: P2)

**Goal**: Nhân viên chọn tháng/năm khác từ bộ lọc và bảng cập nhật đúng dữ liệu.

**Independent Test**: Trong tab "Bảng giờ công", chọn tháng trước → bảng cập nhật đúng records của tháng đó.

### Implementation cho User Story 2

- [x] T012 [US2] Thêm event listener cho bộ lọc tháng/năm — onChange → gọi `loadAttendanceData(month, year)`. Default tháng/năm hiện tại khi init.

**Checkpoint**: Thay đổi tháng trên dropdown → bảng re-fetch và render đúng ✅

---

## Phase 5: User Story 3 – Tab Đăng ký ca không bị regression (Priority: P1)

**Goal**: Sau khi refactor template thêm tabs, chức năng đăng ký ca vẫn hoạt động hoàn toàn bình thường.

**Independent Test**: Trong tab "Đăng ký ca", chọn một ca, lưu → thành công; hủy draft → thành công.

### Implementation cho User Story 3

- [x] T013 [US3] Scoped tất cả querySelector của tab đăng ký ca sang `#panel-dang-ky-ca .shift-cell` để tránh xung đột với elements trong panel giờ công

**Checkpoint**: Đăng ký ca mới + hủy ca draft thành công, không JS error ✅

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T014 [P] Security: route `/dang-ky-ca/gio-cong` dùng `auth='user'`, filter theo `employee_id` từ session
- [x] T015 [P] JS dùng `const`/`let`, `textContent` thay `innerHTML` cho user data (XSS-safe)
- [x] T016 Responsive: CSS thêm `@media (max-width: 768px)` cho tab buttons, attendance toolbar, bảng giờ công
- [x] T017 [P] Docstring đầy đủ cho `get_attendance_data` (Args, Returns)
- [ ] T018 flake8 — skipped (flake8 chưa được cài trong môi trường; kiểm tra thủ công)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Không phụ thuộc — bắt đầu ngay
- **Foundational (Phase 2)**: Sau Phase 1 — BLOCKS US1 và US2
- **US1 (Phase 3)**: Sau Phase 2 — MVP
- **US2 (Phase 4)**: Sau Phase 2 — có thể chạy song song US1 (T012 độc lập)
- **US3 (Phase 5)**: Sau Phase 3 (cần T006 hoàn thành trước) — regression test
- **Polish (Phase 6)**: Sau tất cả US phases

---

## Implementation Strategy

### MVP First (US1 + US3)

1. ✅ Complete Phase 1: Setup
2. ✅ Complete Phase 2: Route JSON
3. ✅ Complete Phase 3: US1
4. ✅ Complete Phase 5: US3 regression
5. ✅ Deploy/demo

### Status: COMPLETE ✅
