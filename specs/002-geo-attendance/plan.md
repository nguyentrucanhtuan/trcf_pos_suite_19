# Implementation Plan: Tab Chấm Công Geolocation + Public IP WiFi Verification

**Branch**: `002-geo-attendance` | **Date**: 2026-03-08 | **Spec**: [spec.md](spec.md)

## Summary

Mở rộng module `trcf_fnb_staff` với tính năng chấm công Geolocation qua browser GPS. Nhân viên mở tab "Chấm Công" tại `/dang-ky-ca` — hệ thống xác minh vị trí GPS (geofence) **và** public IP WiFi (tuỳ cấu hình cơ sở) trước khi cho check-in/check-out. Timestamp luôn là giờ server. Bổ sung model `trcf.geo.location` với giao diện bản đồ tương tác (Leaflet.js) cho admin cấu hình.

---

## Technical Context

**Language/Version**: Python 3.11 + Odoo 19 Community  
**Primary Dependencies**: Odoo 19 ORM, QWeb, Vanilla JS, Leaflet.js 1.9.x (CDN, no API key)  
**Storage**: PostgreSQL (qua Odoo ORM)  
**Testing**: Odoo test runner (`python -m pytest` hoặc `odoo -d <db> --test-enable -u trcf_fnb_staff`)  
**Target Platform**: Browser (Chrome, Safari, Firefox) + Odoo backend  
**Project Type**: Odoo module extension  
**Performance Goals**: Check-in response < 2 giây; GPS poll mỗi 5 giây  
**Constraints**: Không dùng JS framework ngoài (React/Vue); dùng CDN cho Leaflet; không native app  
**Scale/Scope**: ~50–200 nhân viên/cơ sở, 2–10 cơ sở

---

## Constitution Check

| # | Principle | Gate Question | Status |
|---|-----------|---------------|--------|
| I | Odoo 19-First | Odoo core không có geofence attendance; `hr.attendance` extend theo chuẩn | ✅ |
| II | Backend UX/UI | Form view `trcf.geo.location` dùng Odoo standard form + Leaflet widget tùy chỉnh (justified: không có Odoo map widget) | ✅ |
| III | Frontend UX/UI | Tab Chấm Công dùng QWeb template + Vanilla JS (nhất quán với pattern hiện tại); Tailwind cho styling | ✅ |
| IV | Code Quality | PEP8, docstring trên mọi method nghiệp vụ, không print/pdb | ✅ |
| V | Performance | ORM queries có `domain`, `fields`, `limit`; không loop từng record | ✅ |
| VI | Maintainability | Odoo tự xử lý migration fields; helper methods tách biệt | ✅ |
| S | Security | `auth='user'`, `t-esc`, `ir.model.access.csv`, IP từ server không phải client | ✅ |

---

## Project Structure

### Documentation (feature)

```text
specs/002-geo-attendance/
├── plan.md              ← file này
├── research.md          ← updated 2026-03-08 (14 decisions)
├── data-model.md        ← updated 2026-03-08
├── contracts/
│   └── api-routes.md   ← updated 2026-03-08
└── tasks.md             ← tạo bởi /speckit.tasks
```

### Source Code

```text
trcf_fnb_staff/
├── __manifest__.py              [MODIFY] thêm assets + data files mới
├── models/
│   ├── __init__.py              [MODIFY] import trcf_geo_location
│   ├── trcf_hr_attendance.py    [MODIFY] thêm 12 fields mới
│   └── trcf_geo_location.py     [NEW] model trcf.geo.location
├── controllers/
│   └── trcf_shift_registration_controller.py  [MODIFY] 3 routes mới + IP helpers
├── views/
│   ├── trcf_shift_registration_templates.xml  [MODIFY] tab 3 + panel + JS
│   └── trcf_geo_location_views.xml            [NEW] list + form view backend
├── static/
│   ├── src/js/
│   │   └── geo_attendance.js    [NEW] GPS polling, check-in/out calls
│   └── src/css/
│       └── geo_attendance.css   [NEW] styles tab Chấm Công
├── security/
│   └── ir.model.access.csv     [MODIFY] access rules trcf.geo.location
└── tests/
    └── test_geo_attendance.py  [NEW] unit + integration tests
```

---

## Proposed Changes

### Component 1: Data Layer

---

#### [MODIFY] [trcf_hr_attendance.py](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/trcf_fnb_staff/models/trcf_hr_attendance.py)

Thêm 12 fields vào class `TrcfHrAttendance(models.Model)`:

| Field | Type | Ghi chú |
|-------|------|---------|
| `attendance_source` | Selection | `'zkteco'`(default), `'geo'`, `'manual'` |
| `geo_check_in_lat/lon/accuracy` | Float | GPS check-in |
| `geo_check_out_lat/lon/accuracy` | Float | GPS check-out |
| `geo_location_id` | Many2one(`trcf.geo.location`) | Cơ sở check-in (closest match) |
| `geo_suspicious` | Boolean | Flag GPS bất thường |
| `geo_suspicious_reason` | Char | Lý do flag |
| `request_ip` | Char | Public IP của request |
| `ip_suspicious` | Boolean | Flag IP không khớp |

Thêm `models.Index` trên: `geo_suspicious`, `ip_suspicious`, `attendance_source`.

---

#### [NEW] [trcf_geo_location.py](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/trcf_fnb_staff/models/trcf_geo_location.py)

Model mới `trcf.geo.location` với fields: `name`, `latitude`, `longitude`, `radius`, `active`, `company_id`, `description`, `allowed_ips` (Text), `ip_check_mode` (Selection: none/warning/strict).

SQL constraint: `radius > 0`, `latitude BETWEEN -90 AND 90`, `longitude BETWEEN -180 AND 180`.

---

### Component 2: Controller Layer

---

#### [MODIFY] [trcf_shift_registration_controller.py](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/trcf_fnb_staff/controllers/trcf_shift_registration_controller.py)

**Helper methods** (private):
- `_get_client_ip()` — rightmost `X-Forwarded-For` hop hoặc `REMOTE_ADDR`
- `_check_ip(location, client_ip)` — warning/strict mode, raise `UserError` nếu strict
- `_haversine(lat1, lon1, lat2, lon2)` — khoảng cách GPS (mét)
- `_check_geo_suspicious(accuracy, last_checkout, lat, lon)` — accuracy + velocity flag

**New routes**:
- `POST /dang-ky-ca/geo-checkin` (jsonrpc, auth=user): GPS + IP check → tạo `hr.attendance`
- `POST /dang-ky-ca/geo-checkout` (jsonrpc, auth=user): GPS + IP check → cập nhật `check_out`
- `GET /dang-ky-ca/geo-status` (http, auth=user): trả JSON trạng thái check-in

**Modified**:
- `GET /dang-ky-ca`: truyền `geo_locations` (JSON serialized) vào template context

---

### Component 3: Frontend Layer

---

#### [MODIFY] [trcf_shift_registration_templates.xml](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/trcf_fnb_staff/views/trcf_shift_registration_templates.xml)

- Thêm tab thứ 3: `data-tab="cham-cong"`, icon `fa-map-marker`
- Thêm panel `#panel-cham-cong` với: GPS status display, khoảng cách, nút Check-in/Check-out, thông tin phiên
- Inline script block gọi `geo_attendance.js` (hoặc inline pattern hiện tại)

#### [NEW] [geo_attendance.js](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/trcf_fnb_staff/static/src/js/geo_attendance.js)

- `startGeoWatch()`: gọi `getCurrentPosition` ngay lập tức, sau đó `setInterval(5000)`
- `stopGeoWatch()`: `clearInterval` khi chuyển tab hoặc tab ẩn (`visibilitychange`)
- `updatePosition(pos)`: tính Haversine client-side → cập nhật UI (khoảng cách, trạng thái, enable/disable nút)
- `doCheckIn() / doCheckOut()`: gọi AJAX → `/dang-ky-ca/geo-checkin` | `/geo-checkout`
- Xử lý error codes: `out_of_range`, `ip_blocked`, `already_checked_in`, `no_open_session`

#### [NEW] [geo_attendance.css](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/trcf_fnb_staff/static/src/css/geo_attendance.css)

Styles cho panel Chấm Công: status badge (valid/invalid), nút check-in lớn, loading spinner GPS.

---

### Component 4: Admin UI

---

#### [NEW] [trcf_geo_location_views.xml](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/trcf_fnb_staff/views/trcf_geo_location_views.xml)

- **List view**: name, latitude, longitude, radius, ip_check_mode, active
- **Form view**: standard Odoo form + Leaflet.js map widget (CDN, `<script>` trong template) + `allowed_ips` textarea + `ip_check_mode` selection
- **Leaflet UX**: click đặt tâm → tự điền lat/lon; kéo rìa circle → cập nhật radius; nút "Dùng vị trí hiện tại"
- **Menu**: TRCF → Cấu hình → Vị trí Geofence

---

### Component 5: Security & Manifest

---

#### [MODIFY] [ir.model.access.csv](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/trcf_fnb_staff/security/ir.model.access.csv)

Thêm access lines cho `trcf.geo.location`: read-only cho `group_user`, full CRUD cho `group_hr_manager`.

#### [MODIFY] [__manifest__.py](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/trcf_fnb_staff/__manifest__.py)

Thêm vào `data`: `views/trcf_geo_location_views.xml`  
Thêm vào `assets` (`web.assets_frontend`): `static/src/js/geo_attendance.js`, `static/src/css/geo_attendance.css`

---

### Component 6: Tests

---

#### [NEW] [test_geo_attendance.py](file:///Users/tuan/coffeetree_odoo19_dev/custom_addons/trcf_fnb_staff/tests/test_geo_attendance.py)

Test cases:

| Test | Type | Mô tả |
|------|------|-------|
| `test_haversine_known_distance` | Unit | Tính khoảng cách 2 điểm đã biết |
| `test_checkin_within_geofence` | Integration | Check-in IP đúng + GPS đúng → thành công |
| `test_checkin_outside_geofence` | Integration | GPS ngoài radius → `out_of_range` |
| `test_checkin_ip_warning_mode` | Integration | IP sai + warning mode → `ip_suspicious=True` |
| `test_checkin_ip_strict_mode` | Integration | IP sai + strict mode → `ip_blocked` |
| `test_checkin_no_ip_config` | Integration | `allowed_ips` trống → bỏ qua kiểm tra IP |
| `test_checkout_requires_gps` | Integration | Check-out ngoài geofence → `out_of_range` |
| `test_timestamp_is_server_time` | Unit | `check_in` không thể được set từ client |
| `test_geo_suspicious_low_accuracy` | Unit | accuracy < 5 → `geo_suspicious=True` |
| `test_geo_location_id_saved` | Integration | `geo_location_id` được lưu đúng cơ sở gần nhất |
| `test_velocity_suspicious` | Unit | velocity > 500km/h → `geo_suspicious=True` |

---

## Verification Plan

### Automated Tests

```bash
# Chạy test suite (từ thư mục gốc Odoo)
python odoo-bin -d <test_db> --test-enable --stop-after-init -u trcf_fnb_staff --log-level=test

# Hoặc dùng pytest nếu có pytest-odoo
python -m pytest custom_addons/trcf_fnb_staff/tests/test_geo_attendance.py -v
```

### Manual Verification

#### Step 1: Cài đặt module
```bash
# Restart Odoo với update module
python odoo-bin -d <db> -u trcf_fnb_staff --stop-after-init
# Kiểm tra log không có ERROR/CRITICAL
```

#### Step 2: Kiểm tra admin form Leaflet

1. Đăng nhập Odoo backend với quyền HR Manager
2. Vào **TRCF → Cấu hình → Vị trí Geofence**
3. Tạo mới cơ sở → bản đồ Leaflet phải hiển thị (mặc định center Việt Nam)
4. Click trên bản đồ → marker xuất hiện, lat/lon tự điền
5. Kéo rìa circle → radius field cập nhật (mét)
6. Nhập `allowed_ips` = IP máy bạn, chọn `ip_check_mode = Cảnh báo`
7. Lưu → kiểm tra record trong Odoo

#### Step 3: Kiểm tra tab Chấm Công (nhân viên)

1. Đăng nhập bằng tài khoản nhân viên có hồ sơ `hr.employee`
2. Truy cập `/dang-ky-ca` → kiểm tra 3 tab hiển thị
3. Chọn tab **Chấm Công** → kiểm tra GPS permission prompt
4. Cho phép GPS → khoảng cách tới cơ sở cập nhật mỗi 5 giây
5. Nếu trong geofence → nút Check-in bật → nhấn → kiểm tra `hr.attendance` được tạo
6. Quay lại tab → nút chuyển thành Check-out → nhấn (trong geofence + IP đúng) → worked_hours hiển thị

#### Step 4: Kiểm tra IP strict mode

1. Cấu hình cơ sở với `ip_check_mode = Bắt buộc`, `allowed_ips = 1.2.3.4` (IP không thực)
2. Check-in từ geofence hợp lệ → kỳ vọng: thông báo "Thiết bị không kết nối đúng mạng WiFi văn phòng"
3. Kiểm tra không có `hr.attendance` mới được tạo

#### Step 5: Kiểm tra regression tab 1 và tab 2

1. Vào tab "Đăng ký ca" → đăng ký ca bình thường
2. Vào tab "Bảng giờ công" → bảng hiển thị đầy đủ
3. Kiểm tra không có lỗi console trình duyệt
