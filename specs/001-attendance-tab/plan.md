# Implementation Plan: Trang /dang-ky-ca – Thêm Tab Bảng Giờ Công Tháng

**Branch**: `001-attendance-tab` | **Date**: 2026-03-05 | **Spec**: [spec.md](./spec.md)

---

## Summary

Thêm tab "Bảng giờ công" vào trang `/dang-ky-ca` hiện có trong module `trcf_zkteco_attendance_sync`. Tất cả dữ liệu cần thiết đã có sẵn trên model `hr.attendance` mở rộng (fields `check_in_status`, `check_out_status`, `trcf_hourly_salary_sum`). Chỉ cần:
1. Thêm route JSON mới `/dang-ky-ca/gio-cong` để trả dữ liệu giờ công theo tháng.
2. Cập nhật template QWeb: thêm 2-tab UI, bảng giờ công, bộ lọc tháng/năm, footer tổng.
3. Không thay đổi bất kỳ model hay business logic nào.

---

## Technical Context

**Language/Version**: Python 3.11 / Odoo 19 Community  
**Primary Dependencies**: `trcf_zkteco_attendance_sync` (hr.attendance extended), `trcf.shift.registration`  
**Storage**: PostgreSQL (qua Odoo ORM) — không thay đổi schema  
**Testing**: Odoo test runner + manual browser test  
**Target Platform**: Odoo website controller (QWeb + vanilla JS)  
**Performance Goals**: Tải bảng giờ công tháng < 3 giây (SC-005)  
**Constraints**: Không thay đổi tab Đăng ký ca; nhân viên chỉ thấy dữ liệu của mình  
**Scale/Scope**: ~31 records/tháng/nhân viên — không cần pagination

---

## Constitution Check

| # | Principle | Gate Question | Status |
|---|-----------|---------------|--------|
| I | Odoo 19-First | Dùng `hr.attendance` native + extend đã có; không tạo model mới không cần thiết | ✅ |
| II | Backend UX/UI | Không ảnh hưởng backend views | ✅ N/A |
| III | Frontend UX/UI | Template QWeb + vanilla JS; không dùng React/Vue | ✅ |
| IV | Code Quality | Sẽ thêm docstring vào method mới; tuân thủ PEP8 | ✅ |
| V | Performance | Query dùng domain chặt (employee + tháng) + fields giới hạn; ~31 records/tháng | ✅ |
| VI | Maintainability | Không thay đổi schema → không cần migration; logic tách route riêng | ✅ |
| S | Security | Route mới `auth='user'`; filter bằng `employee_id = request.env.user.employee_id` không dùng sudo | ✅ |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-attendance-tab/
├── plan.md           ← This file
├── research.md       ← Phase 0 output ✅
├── data-model.md     ← Phase 1 output ✅
└── tasks.md          ← Phase 2 output (/speckit.tasks)
```

### Source Code (files sẽ thay đổi)

```text
trcf_zkteco_attendance_sync/
├── controllers/
│   └── trcf_shift_registration_controller.py   ← MODIFY: thêm route /gio-cong
├── views/
│   └── trcf_shift_registration_templates.xml   ← MODIFY: thêm tab UI + bảng giờ công
└── static/src/css/
    └── shift_registration.css                  ← MODIFY: thêm style cho tab + bảng mới
```

**Không tạo file mới, không thay đổi model.**

---

## Proposed Changes

### Controller: `trcf_shift_registration_controller.py`

**Thêm route JSON mới** `GET /dang-ky-ca/gio-cong`:

```python
@http.route('/dang-ky-ca/gio-cong', type='json', auth='user', methods=['GET', 'POST'])
def get_attendance_data(self, month=None, year=None, **kwargs):
    """Trả về dữ liệu giờ công tháng của nhân viên đang đăng nhập"""
    employee = request.env.user.employee_id
    if not employee:
        return {'success': False, 'message': 'Không tìm thấy thông tin nhân viên'}
    
    # Mặc định tháng hiện tại
    today = datetime.now()
    month = int(month or today.month)
    year = int(year or today.year)
    
    # Tính domain theo tháng
    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1)
    else:
        last_day = datetime(year, month + 1, 1)
    
    # Query hr.attendance với domain chặt chẽ
    attendances = request.env['hr.attendance'].search([
        ('employee_id', '=', employee.id),
        ('check_in', '>=', first_day),
        ('check_in', '<', last_day),
    ], order='check_in asc')
    
    records = []
    total_salary = 0.0
    for att in attendances:
        local_in = fields.Datetime.context_timestamp(att, att.check_in)
        local_out = fields.Datetime.context_timestamp(att, att.check_out) if att.check_out else None
        
        worked = att.worked_hours or 0.0
        h = int(worked)
        m = int((worked - h) * 60)
        
        salary = att.trcf_hourly_salary_sum or 0.0
        total_salary += salary
        
        records.append({
            'date': local_in.strftime('%d/%m/%Y'),
            'check_in': local_in.strftime('%H:%M'),
            'check_out': local_out.strftime('%H:%M') if local_out else '',
            'worked_hours_display': f'{h}h{m:02d}m' if worked else '–',
            'check_in_status': att.check_in_status or '–',
            'check_out_status': att.check_out_status or '–',
            'salary': salary,
            'salary_display': f'{salary:,.0f}'.replace(',', '.'),
        })
    
    return {
        'success': True,
        'month': month,
        'year': year,
        'records': records,
        'total_salary_display': f'{total_salary:,.0f}'.replace(',', '.'),
        'is_provisional': True,  # Luôn là tạm tính trong phiên bản này
    }
```

---

### Template: `trcf_shift_registration_templates.xml`

**Cải tổ cấu trúc** template `shift_registration_form`:

1. **Header**: giữ nguyên chào tên nhân viên
2. **Tab bar**: thêm 2 tab button `#tab-dang-ky-ca` và `#tab-gio-cong`
3. **Panel "Đăng ký ca"**: toàn bộ nội dung hiện tại (bảng, legend, nút lưu) move vào `div#panel-dang-ky-ca`
4. **Panel "Bảng giờ công"** mới (`div#panel-gio-cong`):
   - Bộ lọc tháng/năm (select month + year)
   - Bảng 6 cột: Ngày / Giờ vào / Giờ ra / Thời gian làm việc / Đi / Về / Lương phiên (*)
   - Footer tổng lương tháng + nhãn "Tạm tính"
   - Empty state khi không có dữ liệu
5. **JavaScript**: thêm logic:
   - Tab switching (CSS class active)
   - Fetch `/dang-ky-ca/gio-cong` khi mở tab lần đầu (lazy load)
   - Re-fetch khi thay đổi bộ lọc tháng/năm
   - Render rows động từ JSON

> (*) Tên cột trong header: "Lương phiên (Tạm tính)" để phản ánh Q5.

---

### CSS: `shift_registration.css`

Thêm style cho:
- `.tab-nav`, `.tab-btn`, `.tab-btn.active`
- `.attendance-table`, `.attendance-footer`
- Loading spinner cho lazy load
- Responsive cho mobile (nhân viên xem trên điện thoại)

---

## Verification Plan

### Manual Testing (Primary)

**Setup**: Đăng nhập bằng tài khoản nhân viên có dữ liệu chấm công. Truy cập `http://localhost:8069/dang-ky-ca`.

1. **Tab switching regression test**:
   - Tab mặc định là "Đăng ký ca" → ✅ hiện bảng đăng ký ca như cũ
   - Click "Bảng giờ công" → ✅ hiện bảng giờ công, ẩn bảng đăng ký ca
   - Click lại "Đăng ký ca" → ✅ trở về, dữ liệu không bị reset

2. **Bảng giờ công – dữ liệu đúng**:
   - Kiểm tra tháng hiện tại hiển thị đúng records
   - So sánh với dữ liệu tại `https://coffeetreepos.io.vn/odoo/action-649`
   - Cột Đi/Về khớp với `check_in_status` / `check_out_status` trên backend

3. **Bộ lọc tháng/năm**:
   - Chọn tháng trước → bảng cập nhật đúng
   - Chọn tháng không có dữ liệu → hiện thông báo "Không có dữ liệu"

4. **Security**:
   - Thử truy cập `/dang-ky-ca/gio-cong` khi chưa đăng nhập → redirect đến login
   - Không thể lấy data của nhân viên khác bằng cách thay đổi tham số

5. **Regression – Tab Đăng ký ca**:
   - Thực hiện đăng ký ca mới → thành công
   - Hủy đăng ký draft → thành công

### Automated Test (Odoo Test Runner)

File: `trcf_zkteco_attendance_sync/tests/test_attendance_tab_controller.py`

```bash
python odoo-bin -d <DB_NAME> --test-enable --stop-after-init -i trcf_zkteco_attendance_sync
```

Test cases:
- `test_route_requires_auth`: GET `/dang-ky-ca/gio-cong` không có session → 302 redirect
- `test_returns_only_own_data`: Response chỉ chứa records của employee đang login
- `test_month_filter`: Truyền `month=1&year=2026` → chỉ trả records tháng 1/2026
- `test_worked_hours_display_format`: `worked_hours=8.5` → `"8h30m"`
- `test_empty_month`: Tháng không có data → `records=[]`, `total_salary_display="0"`

---

## Out of Scope (deferred)

- Hiển thị tổng lương chính thức từ `hr.payslip` đã duyệt (FR-010 phần payslip) → defer sang iteration sau
- Export Excel/PDF
- Chỉnh sửa chấm công từ trang này
