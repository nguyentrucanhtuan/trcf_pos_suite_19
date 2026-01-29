# Odoo 19 Best Practices (TRCF Wisdom)

Kinh nghiệm thực chiến giúp viết code Odoo 19 tối ưu hơn.

## 1. Tối ưu Truy vấn

### Dùng `_read_group` thay vì loop
```python
# ❌ Chậm
total = sum(rec.amount for rec in self.env['sale.order'].search([]))

# ✅ Nhanh
result = self.env['sale.order']._read_group(
    domain=[],
    groupby=[],
    aggregates=['amount:sum']
)
total = result[0][0]
```

### Sử dụng `filtered()` và `mapped()`
```python
# ✅ Thay vì list comprehension
done_orders = orders.filtered(lambda o: o.state == 'done')
partner_names = orders.mapped('partner_id.name')
```

## 2. Trải nghiệm người dùng (UX)

- **Statusbar**: Luôn hiển thị trạng thái quan trọng
- **Chatter**: Bắt buộc cho model có quy trình nghiệp vụ
- **Smart Buttons**: Dùng để hiển thị số lượng liên quan

## 3. Cấu trúc Code

### Compute Fields
```python
# ✅ store=True nếu field được dùng để lọc/tìm kiếm
total = fields.Float(compute='_compute_total', store=True)
```

### Multi-company
```python
company_id = fields.Many2one(
    'res.company', 
    default=lambda self: self.env.company,
    required=True
)
```

## 4. Xử lý Timezone

```python
from odoo.tools import timezone
from pytz import timezone as pytz_tz

# Lấy timezone user
user_tz = self.env.user.tz or 'UTC'
local_tz = pytz_tz(user_tz)

# Convert UTC to local
local_dt = utc_dt.astimezone(local_tz)

# Convert local to UTC
utc_dt = local_tz.localize(naive_dt).astimezone(pytz_tz('UTC'))
```

## 5. Security Best Practices

### Record Rules (Multi-company)
```xml
<record id="rule_order_company" model="ir.rule">
    <field name="name">Order: Company</field>
    <field name="model_id" ref="model_trcf_order"/>
    <field name="domain_force">[('company_id', 'in', company_ids)]</field>
</record>
```

### Sudo Usage
```python
# ✅ Chỉ sudo() khi thật sự cần thiết
self.sudo().write({'system_field': value})

# ✅ Sudo với context
self.sudo().with_context(no_check=True).action()
```

## 6. Performance Patterns

### Prefetch
```python
# Force prefetch nhiều records
orders.mapped('partner_id')  # Prefetch partners
orders.mapped('line_ids')     # Prefetch lines
```

### Batch Processing
```python
# ✅ Xử lý batch thay vì từng record
for records in self.browse(ids)._cr_fetch(batch_size=1000):
    records.process()
```

## 7. Error Handling

```python
from odoo.exceptions import UserError, ValidationError

# UserError: Lỗi nghiệp vụ người dùng có thể sửa
raise UserError(_("Vui lòng chọn khách hàng trước"))

# ValidationError: Lỗi kiểm tra dữ liệu
@api.constrains('amount')
def _check_amount(self):
    if self.amount < 0:
        raise ValidationError(_("Số tiền không được âm"))
```

## 8. Logging

```python
import logging
_logger = logging.getLogger(__name__)

_logger.info("Order %s confirmed", order.name)
_logger.warning("Stock low for product %s", product.name)
_logger.error("Payment failed: %s", error_msg)
```

*(Tiếp tục cập nhật trong quá trình làm việc...)*
