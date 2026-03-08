# API Routes Contract: Geo Attendance

**Branch**: `002-geo-attendance` | **Updated**: 2026-03-08 (bổ sung IP check, checkout GPS validation, geo_location_id)

---

## Tổng quan

Tất cả routes đều thuộc `TrcfShiftRegistrationController` trong `controllers/trcf_shift_registration_controller.py`. Auth: `user` (Odoo session). Format: JSON-RPC 2.0.

**IP extraction**: Server tự đọc `X-Forwarded-For` (rightmost trusted hop) hoặc `REMOTE_ADDR`. Client không cần gửi IP.

---

## Route 1: `POST /dang-ky-ca/geo-checkin`

**Auth**: `auth='user'` | **Type**: `jsonrpc`

### Request
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "lat": 10.7769,
    "lon": 106.7009,
    "accuracy": 12.5
  }
}
```

| Param | Type | Required | Mô tả |
|-------|------|----------|-------|
| `lat` | Float | ✅ | Latitude từ browser GPS |
| `lon` | Float | ✅ | Longitude từ browser GPS |
| `accuracy` | Float | ✅ | GPS accuracy (mét) |

### Response: Success
```json
{
  "result": {
    "success": true,
    "attendance_id": 42,
    "location_name": "Cơ sở Q1",
    "check_in": "07:32",
    "geo_suspicious": false,
    "ip_suspicious": false
  }
}
```

### Response: Error Cases
```json
// Ngoài vùng geofence
{ "result": { "success": false, "error": "out_of_range", "distance_m": 250, "radius_m": 100 } }

// Đã check-in rồi
{ "result": { "success": false, "error": "already_checked_in", "check_in": "07:32" } }

// Chưa cấu hình geofence
{ "result": { "success": false, "error": "no_location_configured" } }

// Không tìm thấy nhân viên
{ "result": { "success": false, "error": "no_employee" } }

// IP bị chặn (strict mode)
{ "result": { "success": false, "error": "ip_blocked", "message": "Thiết bị không kết nối đúng mạng WiFi văn phòng." } }
```

### Server-side validation sequence
1. Tìm employee từ `request.env.user.employee_id` → `no_employee` nếu không có
2. Extract `client_ip` từ `X-Forwarded-For` (rightmost) hoặc `REMOTE_ADDR`
3. Query tất cả `trcf.geo.location` active, tính Haversine distance
4. Nếu không有 location nào trong radius → `out_of_range`
5. Chọn `geo_location` closest to employee
6. Kiểm tra `_check_ip(geo_location, client_ip)` → có thể raise UserError (strict) → `ip_blocked`
7. Kiểm tra open attendance record → `already_checked_in`
8. Tính `geo_suspicious` (accuracy < 5m AND/OR velocity > 500km/h)
9. Tạo `hr.attendance(check_in=datetime.now(), attendance_source='geo', geo_location_id=..., request_ip=client_ip, ...)`

---

## Route 2: `POST /dang-ky-ca/geo-checkout`

**Auth**: `auth='user'` | **Type**: `jsonrpc`

### Request
```json
{
  "jsonrpc": "2.0",
  "method": "call",
  "params": {
    "lat": 10.7769,
    "lon": 106.7009,
    "accuracy": 15.0
  }
}
```

### Response: Success
```json
{
  "result": {
    "success": true,
    "check_out": "16:45",
    "worked_hours_display": "8h30m",
    "salary_display": "500.000"
  }
}
```

### Response: Error Cases
```json
// Không có phiên đang mở
{ "result": { "success": false, "error": "no_open_session" } }

// Ngoài vùng geofence (check-out cũng cần GPS hợp lệ)
{ "result": { "success": false, "error": "out_of_range", "distance_m": 180, "radius_m": 100 } }

// IP bị chặn (strict mode)
{ "result": { "success": false, "error": "ip_blocked", "message": "Thiết bị không kết nối đúng mạng WiFi văn phòng." } }

// Không tìm thấy nhân viên
{ "result": { "success": false, "error": "no_employee" } }
```

### Server-side logic
1. Tìm employee → `no_employee`
2. Extract `client_ip`
3. Tìm `hr.attendance` record hôm nay có `check_in != False AND check_out == False` → `no_open_session`
4. Lấy `geo_location_id` từ bản ghi đang mở (FK đã lưu lúc check-in)
5. Validate GPS: Haversine distance với location → `out_of_range`
6. Validate IP: `_check_ip(geo_location, client_ip)` → có thể `ip_blocked`
7. Cập nhật `check_out = datetime.now()` + `geo_check_out_*` + `request_ip` (IP lúc checkout)
8. Return `worked_hours` và salary từ computed fields

---

## Route 3: `GET /dang-ky-ca/geo-status`

**Auth**: `auth='user'` | **Type**: `http` (json response)

### Response Variants
```json
// Chưa check-in hôm nay
{ "status": "idle" }

// Đang trong ca
{
  "status": "checked_in",
  "attendance_id": 42,
  "check_in_display": "07:32",
  "location_name": "Cơ sở Q1",
  "elapsed_display": "4h15m"
}

// Đã hoàn thành ca hôm nay
{
  "status": "done",
  "check_in_display": "07:32",
  "check_out_display": "16:45",
  "worked_hours_display": "8h30m",
  "salary_display": "500.000"
}
```

---

## Route 4: `GET /dang-ky-ca` (modified)

**Thay đổi**: Controller trả thêm 2 biến vào template context:

| Variable | Type | Mô tả |
|----------|------|-------|
| `geo_locations` | List[dict] | `[{id, name, lat, lon, radius}]` — active locations |
| `current_attendance` | dict\|None | Trạng thái check-in hiện tại |

`geo_locations` được serialize thành JSON string để JS đọc.

---

## Helper Methods (server-side)

```python
def _get_client_ip(self):
    """Lấy public IP đáng tin từ request."""
    xff = request.httprequest.environ.get('HTTP_X_FORWARDED_FOR', '')
    return xff.split(',')[-1].strip() if xff else request.httprequest.remote_addr

def _check_ip(self, location, client_ip):
    """Kiểm tra IP theo ip_check_mode của location. Raise UserError nếu strict."""
    if not location.allowed_ips or location.ip_check_mode == 'none':
        return False
    allowed = [ip.strip() for ip in location.allowed_ips.split(',') if ip.strip()]
    if client_ip in allowed:
        return False
    if location.ip_check_mode == 'strict':
        raise UserError(_("Thiết bị không kết nối đúng mạng WiFi văn phòng."))
    return True  # 'warning' → ip_suspicious = True

def _haversine(self, lat1, lon1, lat2, lon2):
    """Tính khoảng cách (mét) giữa 2 điểm GPS."""
    R = 6371000
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    dφ = math.radians(lat2 - lat1)
    dλ = math.radians(lon2 - lon1)
    a = math.sin(dφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(dλ/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
```
