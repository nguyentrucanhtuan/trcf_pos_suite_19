# Tasks: Tab Chấm Công Geolocation + Public IP WiFi Verification

**Branch**: `002-geo-attendance` | **Date**: 2026-03-08  
**Input**: [spec.md](spec.md) · [plan.md](plan.md) · [data-model.md](data-model.md) · [contracts/api-routes.md](contracts/api-routes.md) · [research.md](research.md)

**Organization**: Mỗi User Story là một phase độc lập, có thể implement và test riêng biệt.

## Format: `[ID] [P?] [Story?] Description + file path`

- **[P]**: Có thể chạy song song (file khác nhau, không dependency)
- **[Story]**: User story tương ứng từ spec.md
- Tests: Có trong spec (FR có acceptance criteria rõ ràng) — bao gồm test tasks

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Khởi tạo cấu trúc module và scaffold.

- [ ] T001 Tạo thư mục `tests/` trong `trcf_zkteco_attendance_sync/` và file `tests/__init__.py`
- [ ] T002 [P] Tạo file `models/trcf_geo_location.py` với skeleton class (chưa có fields) và import vào `models/__init__.py`
- [ ] T003 [P] Tạo file `static/src/js/geo_attendance.js` với skeleton module (empty functions stubs)
- [ ] T004 [P] Tạo file `static/src/css/geo_attendance.css` với skeleton styles
- [ ] T005 [P] Tạo file `tests/test_geo_attendance.py` với class skeleton và imports chuẩn Odoo test framework

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Các thành phần cốt lõi PHẢI hoàn thành trước tất cả User Stories.

**⚠️ CRITICAL**: Không bắt đầu Phase 3+ cho đến khi phase này hoàn tất.

- [ ] T006 Thêm 12 fields mới vào `hr.attendance` trong `models/trcf_hr_attendance.py`: `attendance_source`, `geo_check_in_lat/lon/accuracy`, `geo_check_out_lat/lon/accuracy`, `geo_location_id` (Many2one→trcf.geo.location), `geo_suspicious`, `geo_suspicious_reason`, `request_ip`, `ip_suspicious` — thêm `models.Index` trên `geo_suspicious`, `ip_suspicious`, `attendance_source`
- [ ] T007 Implement model `trcf.geo.location` với đầy đủ fields trong `models/trcf_geo_location.py`: `name`, `latitude`, `longitude`, `radius`, `active`, `company_id`, `description`, `allowed_ips` (Text), `ip_check_mode` (Selection: none/warning/strict) — thêm SQL constraints và docstring
- [ ] T008 Thêm access rules cho `trcf.geo.location` vào `security/ir.model.access.csv`: read-only `base.group_user`, full CRUD `hr.group_hr_manager`
- [ ] T009 [P] Implement helper methods (private) trong `controllers/trcf_shift_registration_controller.py`: `_get_client_ip()` (rightmost trusted hop), `_check_ip(location, client_ip)` (warning/strict mode), `_haversine(lat1, lon1, lat2, lon2)`, `_check_geo_suspicious(accuracy, last_checkout_record, lat, lon)`
- [ ] T010 [P] Cập nhật `__manifest__.py`: thêm `views/trcf_geo_location_views.xml` vào `data`, thêm `static/src/js/geo_attendance.js` và `static/src/css/geo_attendance.css` vào `assets` (`web.assets_frontend`)
- [ ] T011 Nâng cấp `GET /dang-ky-ca` trong `controllers/trcf_shift_registration_controller.py`: query `trcf.geo.location` active, serialize thành JSON, truyền `geo_locations` và `current_attendance` vào template context

**Checkpoint**: `python odoo-bin -d <db> -u trcf_zkteco_attendance_sync --stop-after-init` không có ERROR/CRITICAL — model `trcf.geo.location` accessible trong Odoo backend.

---

## Phase 3: User Story 1 — Nhân viên Check-in Geolocation (Priority: P1) 🎯 MVP

**Goal**: Nhân viên mở tab "Chấm Công", GPS xác định vị trí trong geofence, nhấn Check-in → bản ghi `hr.attendance` được tạo với timestamp server.

**Independent Test**: Đăng nhập nhân viên → `/dang-ky-ca` → tab "Chấm Công" → cho phép GPS → xác nhận vị trí hợp lệ → nhấn Check-in → kiểm tra `hr.attendance` có `check_in` (UTC), `attendance_source='geo'`, `geo_location_id` đúng.

### Tests cho User Story 1

- [ ] T012 [P] [US1] Viết test `test_checkin_within_geofence` trong `tests/test_geo_attendance.py`: mock GPS trong radius → POST `/dang-ky-ca/geo-checkin` → assert `hr.attendance` được tạo với `attendance_source='geo'`
- [ ] T013 [P] [US1] Viết test `test_checkin_outside_geofence` trong `tests/test_geo_attendance.py`: mock GPS ngoài radius → assert response `error='out_of_range'`, không tạo attendance record
- [ ] T014 [P] [US1] Viết unit test `test_haversine_known_distance` trong `tests/test_geo_attendance.py`: tính khoảng cách 2 điểm đã biết (ví dụ: HN→HCM ≈ 1726 km)
- [ ] T015 [P] [US1] Viết test `test_timestamp_is_server_time` trong `tests/test_geo_attendance.py`: gọi check-in xác nhận `check_in` ≠ giá trị client gửi lên

### Implementation cho User Story 1

- [ ] T016 [US1] Implement route `POST /dang-ky-ca/geo-checkin` trong `controllers/trcf_shift_registration_controller.py`: validate GPS → chọn closest geo_location (tiebreaker: gần nhất) → gọi `_check_geo_suspicious()` → tạo `hr.attendance` với đầy đủ geo fields + `request_ip` + `geo_location_id` — validate `out_of_range`, `no_location_configured`, `already_checked_in`, `no_employee`
- [ ] T017 [US1] Implement route `GET /dang-ky-ca/geo-status` trong `controllers/trcf_shift_registration_controller.py`: query attendance hôm nay → trả JSON `{status: idle|checked_in|done, ...}` với `check_in_display`, `location_name`, `elapsed_display`
- [ ] T018 [US1] Thêm tab thứ 3 "Chấm Công" vào `views/trcf_shift_registration_templates.xml`: tab nav `data-tab="cham-cong"` icon `fa-map-marker`, panel `#panel-cham-cong` với GPS status display, tên cơ sở, nút Check-in (disabled mặc định), thông tin phiên
- [ ] T019 [US1] Implement `geo_attendance.js`: `startGeoWatch()` / `stopGeoWatch()` với `setInterval(5000)` + `visibilitychange` listener; `updatePosition(pos)` tính Haversine client-side → cập nhật UI khoảng cách/status/enable nút; `doCheckIn()` AJAX POST → xử lý responses
- [ ] T020 [US1] Implement CSS cho tab Chấm Công trong `static/src/css/geo_attendance.css`: GPS status badge (valid=green/invalid=red), nút Check-in lớn, loading spinner, layout responsive mobile
- [ ] T021 [US1] Thêm edge case UI vào `views/trcf_shift_registration_templates.xml`: thông báo khi browser không hỗ trợ GPS, thông báo khi từ chối permission, cảnh báo GPS accuracy < 5m

**Checkpoint**: Đăng nhập nhân viên test → tab Chấm Công hiển thị → GPS cập nhật mỗi 5s → Check-in thành công → bản ghi `hr.attendance` được tạo correct.

---

## Phase 4: User Story 2 — Nhân viên Check-out Geolocation (Priority: P1)

**Goal**: Nhân viên kết thúc ca nhấn Check-out — hệ thống xác minh GPS **và** IP (cùng quy tắc check-in) trước khi ghi `check_out`. `worked_hours` được tính tự động.

**Independent Test**: Sau khi Phase 3 hoàn tất và có bản ghi check-in → vào tab Chấm Công → nhấn Check-out ở GPS hợp lệ + IP hợp lệ → `check_out` được cập nhật, `worked_hours` hiển thị đúng.

### Tests cho User Story 2

- [ ] T022 [P] [US2] Viết test `test_checkout_within_geofence` trong `tests/test_geo_attendance.py`: tạo attendance đang mở → mock GPS trong radius → POST `/dang-ky-ca/geo-checkout` → assert `check_out` được cập nhật
- [ ] T023 [P] [US2] Viết test `test_checkout_outside_geofence` trong `tests/test_geo_attendance.py`: mock GPS ngoài radius → assert response `error='out_of_range'`, `check_out` không thay đổi
- [ ] T024 [P] [US2] Viết test `test_checkout_no_open_session` trong `tests/test_geo_attendance.py`: không có attendance đang mở → assert `error='no_open_session'`

### Implementation cho User Story 2

- [ ] T025 [US2] Implement route `POST /dang-ky-ca/geo-checkout` trong `controllers/trcf_shift_registration_controller.py`: tìm attendance đang mở → lấy `geo_location_id` từ bản ghi check-in → validate GPS + IP → cập nhật `check_out=datetime.now()` + `geo_check_out_*` + `request_ip` → return `worked_hours_display`, `salary_display`
- [ ] T026 [US2] Cập nhật `geo_attendance.js`: implement `doCheckOut()` AJAX POST → xử lý responses (`out_of_range`, `ip_blocked`, `no_open_session`) → cập nhật UI sau checkout thành công (hiển thị tổng giờ làm)
- [ ] T027 [US2] Cập nhật `views/trcf_shift_registration_templates.xml` panel Chấm Công: nút Check-out (hidden khi idle, show khi checked_in), thông báo hoàn thành ca với summary giờ công

**Checkpoint**: Flow hoàn chỉnh — Check-in → đợi → Check-out → `worked_hours` hiển thị đúng; Check-out ngoài geofence bị chặn.

---

## Phase 5: User Story 3 — Cấu hình Geofence + IP cho cơ sở (Priority: P2)

**Goal**: Admin/HR Manager cấu hình geofence (bản đồ tương tác Leaflet.js) và whitelist IP WiFi văn phòng cho từng cơ sở, với 2 chế độ: Cảnh báo và Bắt buộc.

**Independent Test**: Vào Odoo backend → TRCF → Cấu hình → Vị trí Geofence → tạo cơ sở → click bản đồ → lat/lon tự điền → kéo circle → radius cập nhật → nhập `allowed_ips` → chọn `ip_check_mode=strict` → lưu → kiểm tra record DB.

### Tests cho User Story 3

- [ ] T028 [P] [US3] Viết test `test_checkin_ip_warning_mode` trong `tests/test_geo_attendance.py`: cấu hình `ip_check_mode='warning'`, IP request không khớp → check-in thành công, `ip_suspicious=True`
- [ ] T029 [P] [US3] Viết test `test_checkin_ip_strict_mode` trong `tests/test_geo_attendance.py`: cấu hình `ip_check_mode='strict'`, IP request không khớp → assert `error='ip_blocked'`
- [ ] T030 [P] [US3] Viết test `test_checkin_no_ip_config` trong `tests/test_geo_attendance.py`: `allowed_ips=''` → check-in thành công bất kể IP, `ip_suspicious=False`
- [ ] T031 [P] [US3] Viết test `test_geo_location_id_saved` trong `tests/test_geo_attendance.py`: 2 cơ sở active → check-in gần cơ sở 1 → assert `geo_location_id == location1.id`

### Implementation cho User Story 3

- [ ] T032 [US3] Tạo `views/trcf_geo_location_views.xml`: list view (name, lat, lon, radius, ip_check_mode, active) + form view với Leaflet.js map widget (CDN load qua `<script>` trong template) + fields `allowed_ips` (widget textarea) + `ip_check_mode` + menu TRCF → Cấu hình → Vị trí Geofence
- [ ] T033 [US3] Implement Leaflet.js UX trong `views/trcf_geo_location_views.xml` form view: click đặt marker → tự điền `latitude`/`longitude`; kéo rìa `L.Circle` → cập nhật `radius`; nút "Dùng vị trí hiện tại" → browser GPS → pan + set marker
- [ ] T034 [US3] Integrate IP check vào route `geo-checkin` và `geo-checkout` tại `controllers/trcf_shift_registration_controller.py`: sau khi xác định `geo_location`, gọi `_check_ip(geo_location, client_ip)` → set `ip_suspicious` hoặc raise UserError nếu strict — thêm error code `ip_blocked` vào response contracts
- [ ] T035 [US3] Cập nhật `views/trcf_shift_registration_templates.xml` panel Chấm Công: hiển thị thông báo `ip_blocked` friendly ("Thiết bị không kết nối đúng mạng WiFi văn phòng"), không hiển thị chi tiết kỹ thuật cho nhân viên

**Checkpoint**: Tạo cơ sở qua bản đồ + cấu hình IP → check-in từ IP đúng → thành công; check-in từ IP sai + strict → bị chặn; check-in từ IP sai + warning → flag `ip_suspicious`.

---

## Phase 6: User Story 3b — Xác minh Public IP WiFi (cross-cutting với US3)

**Goal**: Mọi bản ghi chấm công Geo đều có `request_ip` được ghi nhận. HR có thể xem flag `ip_suspicious` trong danh sách.

**Independent Test**: Sau khi Phase 5 hoàn tất → kiểm tra DB `hr.attendance.request_ip` không null sau check-in; HR Manager filter `ip_suspicious=True` trong list view → thấy bản ghi bị flag.

### Tests cho User Story 3b

- [ ] T036 [P] [US3B] Viết test `test_request_ip_always_saved` trong `tests/test_geo_attendance.py`: mọi check-in (dù IP có khớp hay không) đều có `request_ip != ''`

### Implementation cho User Story 3b

- [ ] T037 [US3B] Cập nhật HR Manager review view — thêm filter `geo_suspicious` và `ip_suspicious` vào list view attendance của Odoo backend trong `views/trcf_geo_location_views.xml` hoặc extend `hr.attendance` views: badge icon ⚠️ khi `geo_suspicious=True` hoặc `ip_suspicious=True`, tooltip hiển thị lý do
- [ ] T038 [US3B] Implement `FR-015` — đảm bảo HR Manager có thể truy cập danh sách bản ghi `geo_suspicious=True` hoặc `ip_suspicious=True`: thêm action/menu shortcut "Bản ghi đáng ngờ" trong TRCF menu hoặc filter sẵn trong `hr.attendance` list view

**Checkpoint**: HR Manager vào list view attendance → filter "Đáng ngờ" → thấy bản ghi bị flag với icon và tooltip lý do.

---

## Phase 7: User Story 4 — Tab 1 & 2 không bị regression (Priority: P1)

**Goal**: Sau khi thêm tab "Chấm Công", tab "Đăng ký ca" và tab "Bảng giờ công" vẫn hoạt động chính xác như trước.

**Independent Test**: Vào `/dang-ky-ca` → 3 tab hiển thị → đăng ký ca thành công → bảng giờ công hiển thị đầy đủ kể cả bản ghi Geo.

### Tests cho User Story 4

- [ ] T039 [P] [US4] Viết test `test_tab_regression_shift_registration` trong `tests/test_geo_attendance.py`: GET `/dang-ky-ca` → assert 3 tab trong HTML response
- [ ] T040 [P] [US4] Viết test `test_attendance_source_default_zkteco` trong `tests/test_geo_attendance.py`: bản ghi `hr.attendance` cũ (không có `attendance_source`) → `attendance_source = 'zkteco'` (default backward compat)

### Implementation cho User Story 4

- [ ] T041 [US4] Kiểm tra và fix nếu cần: `views/trcf_shift_registration_templates.xml` — đảm bảo tab 1 và tab 2 vẫn render đúng sau khi thêm tab 3 (test bằng cách load trang và kiểm tra không có JS error)
- [ ] T042 [US4] Cập nhật bảng giờ công (tab 2) để hiển thị cột `attendance_source` hoặc icon phân biệt ZKTeco vs Geo trong `views/trcf_shift_registration_templates.xml` (FR-011)

**Checkpoint**: `/dang-ky-ca` có đủ 3 tab; tab 1 đăng ký ca bình thường; tab 2 bảng giờ công hiển thị cả bản ghi ZKTeco và Geo; không có console errors.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T043 [P] Viết `README.md` cho module `trcf_zkteco_attendance_sync`: mô tả tính năng Geo Attendance mới, hướng dẫn cài, cấu hình IP WiFi
- [ ] T044 [P] Thêm translations (i18n) cho tất cả string mới: labels UI (tab "Chấm Công", thông báo error), field labels trong views — dùng chuẩn `_("...")` Odoo
- [ ] T045 Chạy `flake8` trên toàn bộ Python files mới/sửa: `models/trcf_geo_location.py`, `models/trcf_hr_attendance.py`, `controllers/trcf_shift_registration_controller.py`, `tests/test_geo_attendance.py` → fix mọi warning
- [ ] T046 [P] Chạy `xmllint` trên `views/trcf_geo_location_views.xml` và `views/trcf_shift_registration_templates.xml` → fix mọi XML error
- [ ] T047 Run full test suite: `python odoo-bin -d <test_db> --test-enable --stop-after-init -u trcf_zkteco_attendance_sync` → xác nhận tất cả 14 tests pass, không có ERROR/CRITICAL
- [ ] T048 Kiểm tra log install/upgrade lần cuối: `python odoo-bin -d <db> -u trcf_zkteco_attendance_sync --stop-after-init --log-level=info` → xác nhận không có CRITICAL/ERROR

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational) ← BLOCKS tất cả stories
    ↓
Phase 3 (US1 Check-in P1)     ┐
Phase 4 (US2 Check-out P1)    ├── Có thể chạy song song sau Phase 2
Phase 5 (US3 Geofence+IP P2)  ┘
    ↓
Phase 6 (US3b IP cross-cutting) ← Phụ thuộc Phase 5
Phase 7 (US4 Regression P1)    ← Phụ thuộc Phase 3 + 4
    ↓
Phase 8 (Polish)
```

### User Story Dependencies

- **US1 (Check-in)**: Cần Phase 2 xong → độc lập
- **US2 (Check-out)**: Cần US1 xong (để có bản ghi check-in để test check-out)
- **US3 (Geofence config)**: Cần Phase 2 xong → song song với US1/US2
- **US3b (IP cross-cutting)**: Cần US3 xong
- **US4 (Regression)**: Cần US1 + US2 xong (để không regression)

### Parallel Opportunities

```bash
# Phase 1 — tất cả song song:
T002 trcf_geo_location.py skeleton  ||  T003 geo_attendance.js stubs
T004 geo_attendance.css skeleton    ||  T005 test file skeleton

# Phase 2 — song song:
T006 hr.attendance fields  ||  T007 trcf.geo.location model
T009 helper methods        ||  T010 __manifest__.py update

# Phase 3 tests — song song:
T012 test_checkin_within   ||  T013 test_checkin_outside
T014 test_haversine        ||  T015 test_timestamp

# Phase 5 tests — song song:
T028 test IP warning  ||  T029 test IP strict
T030 test no IP       ||  T031 test geo_location_id
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 + 4 — P1 Only)

1. Phase 1: Setup (T001–T005)
2. Phase 2: Foundational (T006–T011) — **CRITICAL, blocks everything**
3. Phase 3: US1 Check-in (T012–T021)
4. Phase 4: US2 Check-out (T022–T027)
5. Phase 7: US4 Regression (T039–T042)
6. **STOP và VALIDATE**: Test đầy đủ flow check-in → check-out → bảng giờ công

### Full Feature (thêm P2)

7. Phase 5: US3 Geofence + IP config (T028–T035)
8. Phase 6: US3b IP cross-cutting (T036–T038)
9. Phase 8: Polish (T043–T048)

### Parallel Team Strategy

Sau khi Phase 2 hoàn tất:
- **Dev A**: Phase 3 (US1 Check-in) + Phase 4 (US2 Check-out)
- **Dev B**: Phase 5 (US3 Admin Geofence + IP config)
- **Dev C**: Phase 7 (US4 Regression tests)

---

## Notes

- `[P]` = tasks khác file, không dependency → có thể chạy song song
- Tests viết TRƯỚC implementation — chạy lần đầu phải FAIL (TDD)
- Mỗi checkpoint: chạy Odoo với `--stop-after-init` kiểm tra không có ERROR
- GPS polling 5 giây: dừng khi tab ẩn (`visibilitychange`) để tiết kiệm pin mobile
- IP extraction: luôn dùng rightmost hop từ `X-Forwarded-For` hoặc `REMOTE_ADDR` — không tin client
- `geo_location_id` tiebreaker: nếu nhiều cơ sở overlap GPS → chọn cơ sở closest (min distance)
