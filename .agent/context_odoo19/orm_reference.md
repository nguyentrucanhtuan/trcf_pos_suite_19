# Odoo 19 ORM Reference (Full Syntax)

Bản hướng dẫn đầy đủ về cú pháp Model và Fields trong Odoo 19.

## 1. Định nghĩa Model
Mọi model phải kế thừa từ `models.Model`, `models.TransientModel` hoặc `models.AbstractModel`.

```python
class TrcfOrder(models.Model):
    _name = 'trcf.order'  # Kỹ thuật: Luôn có trcf. prefix
    _description = 'Thông tin đơn hàng'
    _inherit = ['mail.thread', 'mail.activity.mixin'] # Chat Tracking
    _order = 'date desc, id desc'
```

## 2. Các loại Fields thông dụng
### Basic Fields
- **Char**: `name = fields.Char(string="Tên", required=True, tracking=True)`
- **Text**: `note = fields.Text(string="Ghi chú")`
- **Integer**: `priority = fields.Integer(string="Ưu tiên", default=10)`
- **Float**: `amount = fields.Float(string="Số tiền", digits=(16, 2))`
- **Monetary**: `price = fields.Monetary(string="Giá", currency_field='currency_id')`
- **Boolean**: `active = fields.Boolean(default=True)`
- **Date/Datetime**: `date = fields.Date(default=fields.Date.context_today)`
- **Selection**: 
    ```python
    state = fields.Selection([
        ('draft', 'Nháp'),
        ('done', 'Hoàn tất')
    ], string="Trạng thái", default='draft')
    ```

### Relational Fields
- **Many2one**: `partner_id = fields.Many2one('res.partner', string="Khách hàng")`
- **One2many**: `line_ids = fields.One2many('trcf.order.line', 'order_id', string="Chi tiết")`
- **Many2many**: `tag_ids = fields.Many2many('trcf.tag', string="Nhãn")`

## 3. Thuộc tính của Field (Odoo 19)
- `string`: Nhãn hiển thị.
- `help`: Gợi ý khi di chuột.
- `readonly`, `required`, `invisible`: true/false hoặc biểu thức.
- `index=True`: Tạo index trong DB (khuyên dùng cho fields search nhiều).
- `tracking=True`: Lưu log vào Chatter.
- `compute='_compute_method'`, `store=True`: Field tính toán.

## 4. API Methods (Odoo 19 Syntax)
### Hàm CRUD
```python
@api.model_create_multi
def create(self, vals_list):
    # Luôn dùng create_multi cho Odoo 19
    return super().create(vals_list)

def write(self, vals):
    # record.env.user thay cho self._uid
    return super().write(vals)
```

### Business Logic
```python
def action_confirm(self):
    for record in self:
        record.write({'state': 'confirmed'})
```

## 5. Environment (record.env)
Sử dụng `env` để truy cập các tài nguyên hệ thống:
- `self.env.user`: Người dùng hiện tại.
- `self.env.company`: Công ty hiện tại.
- `self.env['model.name']`: Gọi model khác.
- `self.env.cr`: Cursor database.
- `self.env.context`: Ngữ cảnh hiện tại.
