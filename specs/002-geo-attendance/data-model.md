# Data Model: Tab Chấm Công Geolocation

**Branch**: `002-geo-attendance` | **Phase**: 1 | **Updated**: 2026-03-08 (bổ sung IP WiFi fields, checkout validation, geo_location_id)

---

## Model 1: `hr.attendance` (extend hiện có)

**File**: `models/trcf_hr_attendance.py` (đã tồn tại, BỔ SUNG fields)

| Field | Type | Default | Mô tả |
|-------|------|---------|-------|
| `attendance_source` | Selection | `'zkteco'` | Nguồn: `zkteco`, `geo`, `manual` |
| `geo_check_in_lat` | Float | `0.0` | Latitude lúc check-in |
| `geo_check_in_lon` | Float | `0.0` | Longitude lúc check-in |
| `geo_check_in_accuracy` | Float | `0.0` | GPS accuracy check-in (mét) |
| `geo_check_out_lat` | Float | `0.0` | Latitude lúc check-out |
| `geo_check_out_lon` | Float | `0.0` | Longitude lúc check-out |
| `geo_check_out_accuracy` | Float | `0.0` | GPS accuracy check-out (mét) |
| `geo_location_id` | Many2one(`trcf.geo.location`) | False | Cơ sở check-in (closest matching) |
| `geo_suspicious` | Boolean | `False` | Cờ bất thường GPS (accuracy < 5m OR velocity > 500km/h) |
| `geo_suspicious_reason` | Char | `''` | Lý do flag GPS |
| `request_ip` | Char | `''` | Public IP của request check-in/check-out |
| `ip_suspicious` | Boolean | `False` | Cờ IP không khớp danh sách allowed_ips |

**Index mới**: `geo_suspicious`, `ip_suspicious` (filter HR review), `attendance_source` (filter/stats), `geo_location_id` (lookup).

### Validation rules
- Nếu `attendance_source == 'geo'`: `geo_check_in_lat`, `geo_check_in_lon` PHẢI khác 0
- `geo_suspicious_reason` chỉ set khi `geo_suspicious == True`
- `ip_suspicious = True` chỉ khi cơ sở có `allowed_ips` và `ip_check_mode = 'warning'`

### Backward compatibility
- `attendance_source` default `'zkteco'` → các bản ghi cũ tự gán nguồn ZKTeco
- `request_ip`, `ip_suspicious`: default rỗng/False → bản ghi ZKTeco không bị ảnh hưởng
- Tất cả computed fields cũ không thay đổi

---

## Model 2: `trcf.geo.location` (MỚI)

**File**: `models/trcf_geo_location.py` (tạo mới)

| Field | Type | Required | Default | Mô tả |
|-------|------|----------|---------|-------|
| `name` | Char | ✅ | – | Tên cơ sở/chi nhánh |
| `latitude` | Float | ✅ | `0.0` | Vĩ độ tâm geofence |
| `longitude` | Float | ✅ | `0.0` | Kinh độ tâm geofence |
| `radius` | Float | ✅ | `100.0` | Bán kính (mét) |
| `active` | Boolean | – | `True` | Bật/tắt cơ sở |
| `company_id` | Many2one(`res.company`) | – | current company | Multi-company |
| `description` | Text | – | – | Ghi chú |
| `allowed_ips` | Text | – | `''` | Danh sách public IP cách nhau bởi dấu phẩy (trống = bỏ qua kiểm tra) |
| `ip_check_mode` | Selection | – | `'none'` | `none` – bỏ qua \| `warning` – flag \| `strict` – từ chối |

**Constraints**: `latitude` ∈ [-90, 90], `longitude` ∈ [-180, 180], `radius` > 0

**Indexes**: `company_id + active` (filter khi check-in), `ip_check_mode` (lookup logic)

### State Transitions
- `active=True` → đang dùng để validate check-in/check-out
- `active=False` → lịch sử, không kiểm tra vị trí mới

---

## Controller Routes

**File**: `controllers/trcf_shift_registration_controller.py`

| Route | Method | Thay đổi |
|-------|--------|----------|
| `GET /dang-ky-ca` | `shift_registration_page` | Truyền thêm `geo_locations` vào template |
| `POST /dang-ky-ca/geo-checkin` | `geo_check_in` | **MỚI**: lat/lon/accuracy → validate GPS + IP → tạo `hr.attendance` |
| `POST /dang-ky-ca/geo-checkout` | `geo_check_out` | **MỚI**: lat/lon/accuracy → validate GPS + IP → cập nhật `check_out` |
| `GET /dang-ky-ca/geo-status` | `geo_status` | **MỚI**: trả trạng thái check-in hiện tại |

### Server-side validation sequence (check-in VÀ check-out)
1. Tìm employee từ `request.env.user.employee_id`
2. Extract `client_ip` từ `X-Forwarded-For` (rightmost) hoặc `REMOTE_ADDR`
3. Query `trcf.geo.location` active → Haversine distance → chọn closest match
4. Nếu không có match → `out_of_range` (check-in) hoặc `out_of_range` (check-out)
5. Kiểm tra IP: `_check_ip(location, client_ip)` → có thể raise UserError (strict) hoặc set `ip_suspicious`
6. GPS suspicious check: accuracy < 5m OR velocity > 500km/h
7. Tạo / cập nhật `hr.attendance` với đầy đủ fields

---

## Backend Admin View: `trcf.geo.location`

**File mới**: `views/trcf_geo_location_views.xml`

- **List view**: name, latitude, longitude, radius, ip_check_mode, active
- **Form view**: name, company_id, active, description + **Leaflet.js map widget** + `allowed_ips` + `ip_check_mode`
- **Menu**: TRCF → Cấu hình → Vị trí Geofence

---

## Security: `security/ir.model.access.csv`

| Model | Group | Read | Write | Create | Delete |
|-------|-------|------|-------|--------|--------|
| `trcf.geo.location` | `base.group_user` | ✅ | ❌ | ❌ | ❌ |
| `trcf.geo.location` | `hr.group_hr_manager` | ✅ | ✅ | ✅ | ✅ |

---

## Template Changes: `trcf_shift_registration_templates.xml`

### Thay đổi
1. **Tab nav**: Thêm tab thứ 3 `data-tab="cham-cong"` với icon `fa-map-marker`
2. **Panel mới**: `<div id="panel-cham-cong" class="tab-panel">` với UI check-in
3. **JavaScript**: GPS polling mỗi 5 giây, logic IP transparent (server-side)

### Panel "Chấm Công" UI Structure
```
[Trạng thái GPS] — Đang xác định vị trí... / Hợp lệ ✓ X mét / Ngoài vùng ✗ Y mét
[Tên cơ sở gần nhất] — hiển thị khi có vị trí
[Nút CHECK-IN / CHECK-OUT] — disabled khi GPS chưa hợp lệ
[Thông tin phiên hiện tại] — giờ vào, thời gian đã làm
[Cảnh báo accuracy thấp] — nếu accuracy < 5m
```

---

## File mới cần tạo

| File | Loại | Ghi chú |
|------|------|---------|
| `models/trcf_geo_location.py` | Model | Model mới `trcf.geo.location` (có `allowed_ips`, `ip_check_mode`) |
| `views/trcf_geo_location_views.xml` | View | List + Form view backend |
| `static/src/js/geo_attendance.js` | JS | Geolocation logic (5s polling, check-in/out calls) |
| `static/src/css/geo_attendance.css` | CSS | Styles cho tab Chấm Công |
| `tests/test_geo_attendance.py` | Test | Unit + integration tests |

## File cần sửa đổi

| File | Thay đổi |
|------|---------|
| `models/__init__.py` | Import `trcf_geo_location` |
| `models/trcf_hr_attendance.py` | Thêm 12 fields (geo + IP + location FK) |
| `controllers/trcf_shift_registration_controller.py` | 3 routes mới + IP validation helpers |
| `views/trcf_shift_registration_templates.xml` | Tab 3 + panel + JS block (5s polling) |
| `security/ir.model.access.csv` | Access rules cho `trcf.geo.location` |
| `__manifest__.py` | Files mới vào `data` và `assets` |
