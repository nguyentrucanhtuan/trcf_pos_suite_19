# Research: Tab Chấm Công Geolocation

**Branch**: `002-geo-attendance` | **Phase**: 0 | **Updated**: 2026-03-08 (bổ sung IP WiFi, checkout validation, GPS polling, geo_location_id)

---

## 1. Kiến trúc frontend hiện tại

### Decision: Giữ nguyên mô hình QWeb + Vanilla JS inline

**Rationale**: Template `trcf_shift_registration_templates.xml` hiện dùng QWeb template + JavaScript inline trong `<script>` tag — không có OWL component, không có webpack build. Tab thứ 3 "Chấm Công" sẽ theo đúng mô hình này để nhất quán.

**Alternatives considered**:
- OWL component: Phức tạp hơn cần thiết, không tương thích với pattern hiện tại của file template này
- Tách file JS riêng: Có thể làm nhưng không cần thiết cho tính năng này

---

## 2. Browser Geolocation API

### Decision: Dùng `navigator.geolocation.getCurrentPosition()` + watchPosition cho real-time

**Rationale**: Web standard, hoạt động trên mọi trình duyệt hiện đại (Chrome, Safari, Firefox). Không cần thư viện bên ngoài.

**Key API**:
```javascript
navigator.geolocation.getCurrentPosition(
  (pos) => { lat = pos.coords.latitude; lon = pos.coords.longitude; accuracy = pos.coords.accuracy; },
  (err) => { /* handle: PERMISSION_DENIED, POSITION_UNAVAILABLE, TIMEOUT */ },
  { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
);
```

**Accuracy signal**: `pos.coords.accuracy` trả về radius (mét) của vòng tròn tin cậy. App giả GPS (mock location) thường trả `0.0` - bất thường với GPS thực tế (thường 5-20m ngoài trời, 20-50m trong nhà).

**Supported**: Chrome 5+, Firefox 3.5+, Safari 5+, Edge 12+

---

## 3. Haversine Formula — Tính khoảng cách GPS

### Decision: Tính phía client (JS) để phản hồi real-time, xác nhận lại phía server

**Rationale**: Client tính khoảng cách → UX responsive (hiển thị khoảng cách ngay lập tức). Server xác nhận lại trước khi lưu → bảo mật (không tin hoàn toàn vào client).

**Formula (JS)**:
```javascript
function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // metres
    const φ1 = lat1 * Math.PI/180;
    const φ2 = lat2 * Math.PI/180;
    const Δφ = (lat2-lat1) * Math.PI/180;
    const Δλ = (lon2-lon1) * Math.PI/180;
    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)); // mét
}
```

**Server-side (Python)**: Dùng công thức tương đương trong method `_check_geofence()` của controller.

---

## 4. Bản đồ Admin — Leaflet.js

### Decision: Leaflet.js (open-source, CDN) cho admin form geofence config

**Rationale**:
- Leaflet v1.9.x: 42KB minified, không cần API key (dùng OpenStreetMap tiles)
- Google Maps: Cần API key + billing, quá nặng cho use case này
- Tích hợp OpenStreetMap tiles: `https://tile.openstreetmap.org/{z}/{x}/{y}.png`

**Alternatives considered**:
- Google Maps: Cần API key, phí phát sinh → rejected
- Mapbox: Cần API key → rejected
- Nhập tay lat/lon: UX kém, admin phải biết tọa độ số → rejected as sole option
- Leaflet.js: ✅ Open source, dễ tích hợp, hỗ trợ circle drag

**Integration point**: Admin form view của model `trcf.geo.location` trong Odoo backend. Dùng widget HTML tùy chỉnh hoặc nhúng map trong field `<field widget="geo_map_picker">` (OWL widget mới).

**Map picker UX**:
1. Form load → render Leaflet map (center Việt Nam mặc định)
2. User click → `L.Marker` tại vị trí click → tự điền lat/lon field
3. `L.Circle` render bán kính → user kéo rìa → cập nhật radius field
4. Nút "Dùng vị trí hiện tại" → `navigator.geolocation` → pan map + set marker

---

## 5. Velocity Check — Phát hiện GPS Spoofing

### Decision: Tính velocity phía server tại thời điểm check-in

**Rationale**: Server có thể truy vấn check-out record gần nhất của nhân viên, tính khoảng cách/thời gian → velocity.

**Logic**:
```python
IMPOSSIBLE_SPEED_KMH = 500  # Không thể di chuyển > 500 km/h

last_checkout = env['hr.attendance'].search([
    ('employee_id', '=', employee_id),
    ('check_out', '!=', False),
], order='check_out desc', limit=1)

if last_checkout:
    dist = haversine(last_checkout.geo_check_out_lat, last_checkout.geo_check_out_lon, lat, lon)
    time_diff_h = (now - last_checkout.check_out).total_seconds() / 3600
    speed_kmh = (dist / 1000) / time_diff_h if time_diff_h > 0 else 0
    if speed_kmh > IMPOSSIBLE_SPEED_KMH:
        geo_suspicious = True
        geo_suspicious_reason = f"impossible_velocity:{speed_kmh:.0f}km/h"
```

---

## 6. Model: `trcf.geo.location` vs `res.config.settings`

### Decision: Model riêng `trcf.geo.location` (many2many hoặc one2many với company)

**Rationale**:
- `res.config.settings` chỉ lưu được 1 giá trị per key → không hỗ trợ nhiều chi nhánh
- Model riêng hỗ trợ `active`, `name`, nhiều records, dễ mở rộng

**Fields**:
```python
name: Char (required)        # "Cơ sở Nguyễn Thị Minh Khai"
latitude: Float (required)   # 10.7769
longitude: Float (required)  # 106.7009
radius: Float (default=100)  # mét
active: Boolean (default=True)
company_id: Many2one('res.company')  # multi-company support
```

---

## 7. Server Timestamp — Chống fake time

### Decision: Dùng `fields.Datetime.now()` phía server, KHÔNG dùng timestamp từ client

**Rationale**: Standard Odoo pattern. Controller chỉ nhận `lat`, `lon`, `accuracy` từ client — không bao giờ nhận `timestamp` từ client.

---

## 8. Security: CSRF & Auth

### Decision: Dùng `type='jsonrpc'` + `auth='user'` cho check-in/check-out routes

**Rationale**: Odoo jsonrpc type tự handle CSRF. `auth='user'` đảm bảo chỉ nhân viên đã đăng nhập mới gọi được. Không dùng `sudo()` trong query check-in/check-out — enforce ownership level qua `employee_id = request.env.user.employee_id`.

---

## 9. Migration

### Decision: Cần `migrations/1.6.0/upgrade.py` để thêm columns mới

**Fields mới trên `hr_attendance`**:
- `geo_check_in_lat`, `geo_check_in_lon`, `geo_check_in_accuracy`
- `geo_check_out_lat`, `geo_check_out_lon`, `geo_check_out_accuracy`
- `attendance_source` (Selection)
- `geo_suspicious` (Boolean)
- `geo_suspicious_reason` (Char)

Odoo tự xử lý qua `_columns` migration khi upgrade module. Không cần script thủ công.

---

## 10. Không có Test Suite hiện tại

**Finding**: Module `trcf_zkteco_attendance_sync` không có thư mục `tests/`. Cần tạo mới.

**Decision**: Tạo `tests/test_geo_attendance.py` với các test cases cho:
- Haversine calculation (unit test)
- Check-in trong/ngoài geofence (integration test)
- Velocity check logic
- Timestamp không lấy từ client

---

## 11. Public IP WiFi Verification (MỚI — 2026-03-08)

### Decision: Server đọc IP từ rightmost trusted hop, so sánh với `allowed_ips` của cơ sở

**Rationale**: Public IP của WiFi văn phòng thường cố định. Bổ sung bên cạnh GPS, phát hiện check-in từ xa.

**Logic server**:
```python
def _get_client_ip(self):
    xff = request.httprequest.environ.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[-1].strip()  # rightmost = trusted proxy-appended IP
    return request.httprequest.remote_addr

def _check_ip(self, location, client_ip):
    if not location.allowed_ips:
        return False
    allowed = [ip.strip() for ip in location.allowed_ips.split(',') if ip.strip()]
    if client_ip in allowed:
        return False
    if location.ip_check_mode == 'strict':
        raise UserError(_("Thiết bị không kết nối đúng mạng WiFi văn phòng."))
    return True  # 'warning' → ip_suspicious = True
```

**Alternatives considered**: Geo-IP lookup (cần thư viện ngoài → rejected MVP), client tự báo IP (dễ giả mạo → rejected).

---

## 12. Checkout GPS + IP Validation (MỚI — 2026-03-08)

### Decision: Check-out áp dụng cùng validation GPS + IP như check-in

**Rationale**: Đảm bảo nhân viên check-out tại văn phòng.

Route `POST /dang-ky-ca/geo-checkout` bổ sung: (1) Haversine GPS check, (2) `_check_ip()`, (3) lưu `geo_check_out_*` + `request_ip` (checkout IP). Error codes bổ sung: `out_of_range`, `ip_blocked`.

---

## 13. GPS 5-Second Polling (MỚI — 2026-03-08)

### Decision: `setInterval(updatePosition, 5000)` + dừng khi tab ẩn

**Rationale**: Nút Check-in/Check-out tự bật/tắt mà không cần nhân viên tương tác.

```javascript
let geoInterval = null;
function startGeoWatch() { updatePosition(); geoInterval = setInterval(updatePosition, 5000); }
function stopGeoWatch()  { if (geoInterval) clearInterval(geoInterval); }
document.addEventListener('visibilitychange', () => document.hidden ? stopGeoWatch() : startGeoWatch());
```

---

## 14. `geo_location_id` FK trên `hr.attendance` (MỚI — 2026-03-08)

### Decision: Lưu Many2one → `trcf.geo.location` tại thời điểm check-in

**Rationale**: Biết `allowed_ips`/`ip_check_mode` của cơ sở nào; hỗ trợ HR report; tiebreaker multi-location (chọn cơ sở gần nhất).

```python
matched = [(loc, dist) for loc in active_locs if haversine(...) <= loc.radius]
geo_location = min(matched, key=lambda x: x[1])[0]
```
