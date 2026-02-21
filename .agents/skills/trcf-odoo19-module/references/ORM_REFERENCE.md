# Odoo 19 ORM Reference (Full Syntax)

Bản hướng dẫn đầy đủ về cú pháp Model và Fields trong Odoo 19.
Validation Status: Verified (compatible with Odoo 19 ORM patterns).

## Table of Contents
- 1. Định nghĩa Model
- 2. Các loại Fields thông dụng
- 3. Compute, Depends, Onchange
- 4. Constraints
- 5. API Methods (CRUD)
- 6. Search & Domain
- 7. Environment
- 8. Recordset Operations
- 9. Translations

## 1. Định nghĩa Model

Mọi model phải kế thừa từ `models.Model`, `models.TransientModel` hoặc `models.AbstractModel`.

```python
class TrcfOrder(models.Model):
    _name = 'trcf.order'  # Kỹ thuật: Luôn có trcf. prefix
    _description = 'Thông tin đơn hàng'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Chat Tracking
    _order = 'date desc, id desc'
    _rec_name = 'name'  # Field hiển thị khi Many2one
```

### Model Inheritance Types

```python
# 1. Class inheritance (thêm fields/methods vào model có sẵn)
class ResPartner(models.Model):
    _inherit = 'res.partner'
    custom_field = fields.Char("Custom")

# 2. Prototype inheritance (tạo bảng mới từ model cha)
class TrcfOrder(models.Model):
    _name = 'trcf.order'
    _inherit = 'sale.order'  # Copy tất cả từ sale.order

# 3. Delegation inheritance (link đến bảng cha)
class TrcfUser(models.Model):
    _name = 'trcf.user'
    _inherits = {'res.partner': 'partner_id'}
    partner_id = fields.Many2one('res.partner', required=True)
```

## 2. Các loại Fields thông dụng

### Basic Fields
```python
name = fields.Char(string="Tên", required=True, tracking=True, index=True)
note = fields.Text(string="Ghi chú")
html_content = fields.Html(string="Nội dung HTML", sanitize=True)
priority = fields.Integer(string="Ưu tiên", default=10)
amount = fields.Float(string="Số tiền", digits=(16, 2))
price = fields.Monetary(string="Giá", currency_field='currency_id')
active = fields.Boolean(default=True)
date = fields.Date(default=fields.Date.context_today)
datetime = fields.Datetime(default=fields.Datetime.now)
image = fields.Image(string="Ảnh", max_width=1024, max_height=1024)
binary_file = fields.Binary(string="File đính kèm")
file_name = fields.Char(string="Tên file")  # Dùng kèm Binary

state = fields.Selection([
    ('draft', 'Nháp'),
    ('confirmed', 'Xác nhận'),
    ('done', 'Hoàn tất'),
    ('cancel', 'Đã hủy'),
], string="Trạng thái", default='draft', tracking=True)
```

### Relational Fields
```python
# Many2one - Mối quan hệ n-1
partner_id = fields.Many2one(
    'res.partner',
    string="Khách hàng",
    ondelete='restrict',  # 'cascade', 'set null'
    domain="[('is_company', '=', True)]",
    context={'show_address': True},
)

# One2many - Mối quan hệ 1-n (cần inverse field ở model con)
line_ids = fields.One2many(
    'trcf.order.line',
    'order_id',  # Tên field Many2one ở model con
    string="Chi tiết",
)

# Many2many - Mối quan hệ n-n
tag_ids = fields.Many2many(
    'trcf.tag',
    'trcf_order_tag_rel',  # Tên bảng trung gian (optional)
    'order_id',            # Column 1 (optional)
    'tag_id',              # Column 2 (optional)
    string="Nhãn",
)
```

## 3. Compute, Depends, Onchange

### Compute Field
```python
total = fields.Float(
    string="Tổng tiền",
    compute='_compute_total',
    store=True,           # Lưu vào DB nếu cần search/group
    readonly=False,       # Cho phép user override giá trị computed
    precompute=True,      # Tính trước khi lưu lần đầu (giảm query)
)

# compute_sudo=True khi cần truy cập dữ liệu cross-company
credit_warning = fields.Text(
    compute='_compute_credit_warning',
    compute_sudo=True,
)

@api.depends('line_ids.subtotal')
def _compute_total(self):
    for order in self:
        order.total = sum(order.line_ids.mapped('subtotal'))
```

> **Khi nào dùng `precompute=True`?**
> - Dùng khi field phụ thuộc vào các field đã có sẵn lúc create (vd: `company_id`, `partner_id`)
> - KHÔNG dùng khi field phụ thuộc vào One2many/Many2many (vì chúng chưa tồn tại lúc precompute)

### Inverse (Compute 2 chiều)
```python
full_name = fields.Char(compute='_compute_full_name', inverse='_inverse_full_name')

def _compute_full_name(self):
    for rec in self:
        rec.full_name = f"{rec.first_name} {rec.last_name}"

def _inverse_full_name(self):
    for rec in self:
        parts = rec.full_name.split(' ', 1)
        rec.first_name = parts[0]
        rec.last_name = parts[1] if len(parts) > 1 else ''
```

### Onchange (UI realtime)
```python
@api.onchange('product_id')
def _onchange_product_id(self):
    if self.product_id:
        self.price_unit = self.product_id.lst_price
        self.name = self.product_id.name
        # Warning message
        return {
            'warning': {
                'title': 'Chú ý',
                'message': 'Giá sẽ được cập nhật tự động',
            }
        }
```

## 4. Constraints

### Python Constraint
```python
@api.constrains('amount', 'quantity')
def _check_positive(self):
    for rec in self:
        if rec.amount < 0 or rec.quantity < 0:
            raise ValidationError(_("Số lượng và số tiền phải >= 0"))
```

### SQL Constraint (Odoo 19 — `models.Constraint`)

> ⚠️ **`_sql_constraints` đã bị deprecated trong Odoo 19!** Sử dụng sẽ sinh WARNING:
> `Model attribute '_sql_constraints' is no longer supported, please define model.Constraint on the model.`

```python
# ❌ DEPRECATED (Odoo 16 và cũ hơn)
_sql_constraints = [
    ('code_unique', 'UNIQUE(code)', 'Mã phải là duy nhất!'),
]

# ✅ ĐÚNG (Odoo 19+) — Khai báo như class attribute
class TrcfOrder(models.Model):
    _name = 'trcf.order'
    _description = 'Đơn hàng'

    _code_unique = models.Constraint(
        'UNIQUE(code)',
        'Mã phải là duy nhất!',
    )
    _amount_positive = models.Constraint(
        'CHECK(amount >= 0)',
        'Số tiền phải >= 0!',
    )
    _conditional_required = models.Constraint(
        "CHECK((state = 'sale' AND date_order IS NOT NULL) OR state != 'sale')",
        'Đơn hàng đã xác nhận phải có ngày xác nhận.',
    )
```

**Quy tắc đặt tên**: Bắt đầu bằng `_`, mô tả mục đích (vd: `_code_unique`, `_amount_positive`).

### Database Index (Odoo 19 — `models.Index`)

```python
# Tạo index cho truy vấn nhanh hơn
_date_order_id_idx = models.Index("(date_order desc, id desc)")
```

## 5. API Methods (CRUD)

```python
@api.model_create_multi
def create(self, vals_list):
    for vals in vals_list:
        if not vals.get('code'):
            vals['code'] = self.env['ir.sequence'].next_by_code('trcf.order')
    return super().create(vals_list)

def write(self, vals):
    if 'state' in vals and vals['state'] == 'done':
        self._check_can_complete()
    return super().write(vals)

def unlink(self):
    if any(rec.state == 'done' for rec in self):
        raise UserError(_("Không thể xóa đơn hàng đã hoàn tất"))
    return super().unlink()

def copy(self, default=None):
    default = dict(default or {})
    default['name'] = f"{self.name} (Copy)"
    return super().copy(default)
```

## 6. Search & Domain

```python
# Basic search
orders = self.env['trcf.order'].search([
    ('state', '=', 'confirmed'),
    ('date', '>=', '2025-01-01'),
])

# Domain operators
# =, !=, <, >, <=, >=, in, not in
# like, ilike, =like, =ilike
# child_of, parent_of

# Logical operators
domain = [
    '|',
    ('state', '=', 'draft'),
    '&',
    ('state', '=', 'confirmed'),
    ('amount', '>', 1000),
]

# Search options
orders = self.env['trcf.order'].search(
    domain,
    limit=10,
    offset=0,
    order='date desc, id desc',
)

# Search count
count = self.env['trcf.order'].search_count(domain)

# Search read (tối ưu)
data = self.env['trcf.order'].search_read(
    domain,
    fields=['name', 'amount', 'partner_id'],
    limit=100,
)
```

## 7. Environment

```python
self.env.user           # res.users: Người dùng hiện tại
self.env.company        # res.company: Công ty hiện tại
self.env.companies      # Tất cả companies của user
self.env.context        # Dict context
self.env.lang           # Ngôn ngữ hiện tại
self.env.cr             # Database cursor
self.env.uid            # User ID
self.env.su             # Bool: đang chạy với sudo?

# Gọi model khác
partner = self.env['res.partner'].browse(1)
partners = self.env['res.partner'].search([])

# Context methods
self.with_context(key='value')
self.with_user(user_id)
self.with_company(company_id)
self.sudo()             # Bypass security
self.sudo(False)        # Re-apply security
```

## 8. Recordset Operations

```python
# Browse
record = self.env['trcf.order'].browse(1)
records = self.env['trcf.order'].browse([1, 2, 3])

# Filter
done = orders.filtered(lambda o: o.state == 'done')
done = orders.filtered_domain([('state', '=', 'done')])

# Map
names = orders.mapped('name')
partner_names = orders.mapped('partner_id.name')

# Sort
sorted_orders = orders.sorted(key=lambda o: o.date, reverse=True)

# Ensure one
order.ensure_one()  # Raises if not exactly 1 record

# Set operations
all_orders = orders1 | orders2   # Union
common = orders1 & orders2       # Intersection
diff = orders1 - orders2         # Difference
```

## 9. Translations

```python
from odoo import _

# Basic translation
raise UserError(_("Không thể xóa đơn hàng đã xác nhận"))

# With placeholders
message = _("Đơn hàng %s đã được xác nhận", order.name)

# With named placeholders
message = _("Tổng tiền: %(amount)s cho %(count)s sản phẩm") % {
    'amount': total,
    'count': len(products),
}
```
