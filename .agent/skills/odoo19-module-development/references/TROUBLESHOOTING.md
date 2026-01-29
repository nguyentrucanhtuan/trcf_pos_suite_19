# Odoo 19 Troubleshooting & Bug Fixes

Nhật ký ghi lại các lỗi kỹ thuật và cách khắc phục trong Odoo 19.

> [!TIP]
> **Quy tắc**: Mỗi khi giải quyết xong lỗi phức tạp, cập nhật ngay vào file này.

## 1. Lỗi Giao diện (UI/XML)

### Thẻ `<tree>` không hoạt động
- **Hiện tượng**: Giao diện không load hoặc báo lỗi parser
- **Nguyên nhân**: Odoo 19 đã chuyển sang dùng `<list>`
- **Khắc phục**: Thay `<tree>` bằng `<list>`

### Thuộc tính `attrs` bị lỗi
- **Hiện tượng**: `Unknown attribute 'attrs'`
- **Nguyên nhân**: Odoo 19 bỏ `attrs`
- **Khắc phục**: Dùng `invisible="expression"`, `readonly="expression"`

```xml
<!-- ❌ Cũ -->
<field name="amount" attrs="{'invisible': [('state', '=', 'draft')]}"/>

<!-- ✅ Mới -->
<field name="amount" invisible="state == 'draft'"/>
```

### Lỗi `OwlError: field is undefined`
- **Hiện tượng**: `OwlError: "model"."field_name" field is undefined`
- **Nguyên nhân**: Field chưa được declare hoặc module chưa update
- **Khắc phục**:
  1. Kiểm tra field đã declare trong model Python
  2. Update module: `./odoo-bin -u module_name`
  3. Clear browser cache (Cmd+Shift+R)

## 2. Lỗi Backend (Python/ORM)

### Lỗi truy cập `self._context`
- **Hiện tượng**: `AttributeError: object has no attribute '_context'`
- **Khắc phục**: Dùng `self.env.context`

### KeyError trong date operations (Timezone)
- **Hiện tượng**: `KeyError: '2025-12-15'` khi tính overtime
- **Nguyên nhân**: Timezone mismatch giữa UTC và local
- **Khắc phục**:

```python
from pytz import timezone, UTC

user_tz = timezone(self.env.user.tz or 'UTC')

# Convert UTC to local trước khi so sánh
local_date = utc_datetime.astimezone(user_tz).date()
```

### Lỗi Multi-company access
- **Hiện tượng**: `AccessError: Record does not exist or was deleted`
- **Nguyên nhân**: Record thuộc company khác
- **Khắc phục**:

```python
# Thêm context bypass nếu cần
record.with_company(company_id).action()

# Hoặc check company trước
if record.company_id != self.env.company:
    raise UserError(_("Không có quyền truy cập"))
```

## 3. Lỗi OWL/Javascript

### Lỗi `Service rpc is not available`
- **Hiện tượng**: Không gọi được RPC trong OWL
- **Nguyên nhân**: Odoo 19 `rpc` không còn là service
- **Khắc phục**:

```javascript
// ❌ Cũ
this.rpc = useService("rpc");

// ✅ Mới
import { rpc } from "@web/core/network/rpc";
await rpc("/url", params);
```

### Lỗi JS không cập nhật (Cache)
- **Hiện tượng**: Sửa code nhưng browser vẫn chạy code cũ
- **Khắc phục**:
  - Mac: **Cmd + Shift + R**
  - Win: **Ctrl + F5**
  - Hoặc: DevTools → Application → Clear site data

### Component không render
- **Hiện tượng**: Component OWL không hiển thị
- **Nguyên nhân**: Template name không khớp hoặc chưa import
- **Khắc phục**:

```javascript
// Check template name khớp với XML
static template = "module_name.TemplateName";

// Đảm bảo import trong __manifest__.py
'assets': {
    'web.assets_backend': [
        'module_name/static/src/js/*.js',
        'module_name/static/src/xml/*.xml',
    ],
},
```

## 4. Bảo mật & Iframe

### Lỗi `X-Frame-Options: deny`
- **Hiện tượng**: Iframe bị trắng hoặc báo lỗi bảo mật
- **Khắc phục**:

```python
@http.route('/my/route', type='http', auth='public', allow_frames=True)
def my_route(self):
    return request.render('template')
```

Hoặc System Parameter: `web.browser_security_disable_x_frame_options` = `True`

## 5. Attendance & HR

### Shift không match với check_in/check_out
- **Hiện tượng**: `shift_registration_id` không tự động populate
- **Nguyên nhân**: check_in/check_out là UTC, shift là local time
- **Khắc phục**: Convert về local timezone trước khi match

```python
user_tz = timezone(self.employee_id.user_id.tz or 'UTC')
local_check_in = self.check_in.astimezone(user_tz)

# Tìm shift theo local time
shift = self.env['trcf.shift.registration'].search([
    ('date', '=', local_check_in.date()),
    ('employee_id', '=', self.employee_id.id),
])
```

## 6. Cron Jobs

### Cron không chạy đúng giờ
- **Hiện tượng**: Cron chạy sai giờ so với mong đợi
- **Nguyên nhân**: `nextcall` lưu UTC, nhưng user muốn local time
- **Khắc phục**: Convert local to UTC khi set `nextcall`

```python
from datetime import datetime
import pytz

local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
local_time = local_tz.localize(datetime.strptime('07:00', '%H:%M'))
utc_time = local_time.astimezone(pytz.UTC)

cron.write({'nextcall': utc_time.strftime('%Y-%m-%d %H:%M:%S')})
```

*(Tiếp tục cập nhật khi phát hiện lỗi mới...)*
