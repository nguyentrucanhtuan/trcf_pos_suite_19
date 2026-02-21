# Odoo 19 Best Practices (TRCF Wisdom)

Kinh nghiệm thực chiến giúp viết code Odoo 19 tối ưu hơn.
Validation Status: Verified (cross-checked with Odoo 19 practices and internal conventions).

## Table of Contents
- 1. Tối ưu Truy vấn
- 2. Trải nghiệm người dùng (UX)
- 3. Cấu trúc Code
- 4. Xử lý Timezone
- 5. Security Best Practices
- 6. Performance Patterns
- 7. Error Handling
- 8. Logging

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

# 1. Lấy timezone user (quan trọng: handle trường hợp user không set tz)
user_tz = self.env.user.tz or 'UTC'
local_tz = pytz_tz(user_tz)

# 2. Convert UTC to local (để tính toán, hiển thị)
local_dt = utc_dt.astimezone(local_tz)
local_date = local_dt.date() # Lấy ngày theo giờ địa phương

# 3. Convert local to UTC (để lưu vào DB)
# Lưu ý: Luôn dùng localize() cho naive datetime
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

### Prefetch (Tránh N+1 Queries)
```python
# Force prefetch nhiều records cùng lúc
# Odoo tự động prefetch, nhưng đôi khi cần manual nếu tách context
orders.mapped('partner_id')  # Prefetch partners
orders.mapped('line_ids')     # Prefetch lines

# Dùng search_read / read_group thay vì loop search
data = self.env['model'].search_read(domain, ['field1', 'field2'])
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

## 9. Odoo 19 Migration Patterns

> ⚠️ **Checklist bắt buộc** trước khi viết code. AI thường viết theo pattern cũ!

| Pattern cũ | Odoo 19 | Ghi chú |
|---|---|---|
| `_sql_constraints = [...]` | `_name = models.Constraint(...)` | Class attribute, bắt đầu `_` |
| `<tree>` | `<list>` | Cả root và embedded |
| `attrs="{'invisible': [...]}"` | `invisible="expr"` | Inline Python expression |
| `attrs="{'readonly': [...]}"` | `readonly="expr"` | Inline Python expression |
| `point_of_sale.assets` | `point_of_sale._assets_pos` | POS asset bundle |
| `type='json'` (controller) | `type='jsonrpc'` | [Đã verified] |
| `fields.Date.today()` | `fields.Date.context_today(self)` | Cho timezone aware |

### Khi nào dùng `precompute=True`
```python
# ✅ Dùng: field phụ thuộc vào data có sẵn lúc create
currency_id = fields.Many2one(
    compute='_compute_currency_id',
    store=True, precompute=True,
)

# ❌ KHÔNG dùng: field phụ thuộc vào One2many
total = fields.Float(
    compute='_compute_total',  # depends order_line (One2many)
    store=True,  # KHÔNG precompute vì One2many chưa tồn tại lúc create
)
```

### Khi nào dùng `compute_sudo=True`
```python
# Dùng khi user không có quyền truy cập model phụ thuộc
# nhưng vẫn cần hiển thị giá trị computed
amount_paid = fields.Float(
    compute='_compute_amount_paid',
    compute_sudo=True,  # Cần truy cập payment.transaction
)
```
