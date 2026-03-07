# Data Model: Attendance Tab Feature

**Feature**: 001-attendance-tab  
**Date**: 2026-03-05

---

## Entities

### hr.attendance (extended by trcf_zkteco_attendance_sync)

> Model nguồn dữ liệu chính cho bảng giờ công. Không cần thêm field mới.

| Field | Type | Mô tả |
|-------|------|-------|
| `employee_id` | Many2one (hr.employee) | Nhân viên |
| `check_in` | Datetime (UTC) | Giờ vào thực tế |
| `check_out` | Datetime (UTC) | Giờ ra thực tế |
| `worked_hours` | Float | Số giờ làm việc (check_out - check_in) |
| `check_in_status` | Char (computed, stored) | Trạng thái Đi: "Trễ Xp" / "Sớm Xp" / "Đúng giờ" |
| `check_out_status` | Char (computed, stored) | Trạng thái Về: "Sớm Xp" / "Trễ Xp" / "Đúng giờ" |
| `shift_registration_id` | Many2one (computed, stored) | Ca đăng ký khớp với phiên |
| `trcf_hourly_salary_display` | Float (related) | Đơn giá lương/giờ = employee_id.trcf_hourly_salary |
| `trcf_hourly_salary_sum` | Float (computed, stored) | Lương phiên = worked_hours × trcf_hourly_salary |

**Validation rules**:
- Chỉ query record có `employee_id = current_user.employee_id`
- Filter theo tháng/năm bằng domain trên `check_in`
- Order by `check_in ASC`

**Edge cases**:
- `check_out = False` (đang trong ca): hiển thị giờ ra trống, `worked_hours = 0`
- `shift_registration_id = False`: `check_in_status` / `check_out_status` = `''` → template render "–"

---

### hr.employee (tham chiếu)

| Field | Dùng cho |
|-------|----------|
| `trcf_hourly_salary` | Đơn giá lương/giờ để verify tổng lương |

---

### hr.payslip (tham chiếu — phase sau)

> Không cần trong phiên bản này. Spec FR-010 đề cập nhưng kiểm tra payslip đã duyệt được **defer** sang iteration sau để giảm scope.

---

## Query Pattern (Controller)

```python
# Lấy dữ liệu giờ công tháng cho nhân viên hiện tại
domain = [
    ('employee_id', '=', employee.id),
    ('check_in', '>=', first_day_of_month),
    ('check_in', '<', first_day_of_next_month),
]
attendances = request.env['hr.attendance'].search(
    domain,
    order='check_in asc',
    fields=['check_in', 'check_out', 'worked_hours',
            'check_in_status', 'check_out_status',
            'trcf_hourly_salary_sum']
)
```

**Performance**: Dùng `domain` chặt chẽ + `fields` giới hạn → không load toàn bộ record. Chỉ index có sẵn trên `check_in` và `employee_id`.

---

## Response JSON Schema (route mới)

```json
{
  "success": true,
  "month": 3,
  "year": 2026,
  "employee_name": "Nguyễn Văn A",
  "records": [
    {
      "date": "05/03/2026",
      "check_in": "08:05",
      "check_out": "17:30",
      "worked_hours_display": "9h25m",
      "check_in_status": "Trễ 5p",
      "check_out_status": "Đúng giờ",
      "salary_display": "285,000"
    }
  ],
  "total_salary": "5,700,000",
  "is_provisional": true
}
```
