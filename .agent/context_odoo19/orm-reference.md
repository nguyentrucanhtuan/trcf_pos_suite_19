# Odoo 19 ORM Reference

> **Source**: https://www.odoo.com/documentation/19.0/vi/developer/reference/backend/orm.html
>
> **Last Updated**: 2025-12-22

---

## 1. Model Types

| Type | Mô tả | Sử dụng |
|------|-------|---------|
| `models.Model` | Database-persisted | Model thông thường |
| `models.TransientModel` | Temporary, auto-vacuumed | Wizard dialogs |
| `models.AbstractModel` | Abstract base class | Shared logic |

### Ví dụ
```python
from odoo import models, fields, api

class MyModel(models.Model):
    _name = 'my.model'
    _description = 'My Model'
    _order = 'create_date desc'
    
    name = fields.Char('Name', required=True)
```

---

## 2. Model Attributes

| Attribute | Mô tả | Ví dụ |
|-----------|-------|-------|
| `_name` | Tên model (required) | `'trcf.my.model'` |
| `_description` | Mô tả model | `'My Model Description'` |
| `_inherit` | Inherit từ model khác | `'sale.order'` |
| `_order` | Default sort order | `'date desc, name'` |
| `_rec_name` | Field hiển thị làm name | `'display_name'` |
| `_sql_constraints` | SQL constraints | Xem bên dưới |

### SQL Constraints
```python
_sql_constraints = [
    ('name_unique', 'UNIQUE(name)', 'Name must be unique!'),
    ('check_amount', 'CHECK(amount >= 0)', 'Amount must be positive!'),
]
```

---

## 3. Field Types

### Basic Fields
| Field | Python Type | Ví dụ |
|-------|-------------|-------|
| `Char` | str | `name = fields.Char('Name', required=True)` |
| `Text` | str | `description = fields.Text('Description')` |
| `Integer` | int | `quantity = fields.Integer('Qty', default=1)` |
| `Float` | float | `price = fields.Float('Price', digits=(16, 2))` |
| `Boolean` | bool | `active = fields.Boolean('Active', default=True)` |
| `Date` | date | `date = fields.Date(default=fields.Date.today)` |
| `Datetime` | datetime | `date_time = fields.Datetime()` |
| `Selection` | str/int | `state = fields.Selection([...], default='draft')` |
| `Binary` | bytes | `image = fields.Binary('Image')` |
| `Html` | str | `content = fields.Html('Content')` |

### Relational Fields
| Field | Mô tả | Ví dụ |
|-------|-------|-------|
| `Many2one` | Many-to-one | `partner_id = fields.Many2one('res.partner', 'Partner')` |
| `One2many` | One-to-many | `line_ids = fields.One2many('model.line', 'parent_id')` |
| `Many2many` | Many-to-many | `tag_ids = fields.Many2many('my.tag', string='Tags')` |

### Computed Fields
```python
total = fields.Float('Total', compute='_compute_total', store=True)

@api.depends('line_ids.amount')
def _compute_total(self):
    for rec in self:
        rec.total = sum(rec.line_ids.mapped('amount'))
```

---

## 4. Field Parameters

| Parameter | Type | Mô tả |
|-----------|------|-------|
| `string` | str | Label hiển thị |
| `required` | bool | Bắt buộc nhập |
| `readonly` | bool | Chỉ đọc |
| `default` | value/callable | Giá trị mặc định |
| `index` | str/bool | Index database: `True`, `'btree'`, `'trigram'` |
| `groups` | str | Groups có quyền: `'base.group_user'` |
| `copy` | bool | Copy khi duplicate |
| `store` | bool | Lưu database (computed fields) |
| `compute` | str | Tên method compute |
| `inverse` | str | Method inverse cho computed |
| `ondelete` | str | Many2one: `'cascade'`, `'restrict'`, `'set null'` |

---

## 5. API Decorators

### @api.depends
```python
@api.depends('field1', 'field2', 'related_id.field')
def _compute_something(self):
    for rec in self:
        rec.computed_field = ...
```

### @api.constrains
```python
@api.constrains('amount')
def _check_amount(self):
    for rec in self:
        if rec.amount < 0:
            raise ValidationError(_('Amount must be positive!'))
```

### @api.onchange
```python
@api.onchange('partner_id')
def _onchange_partner(self):
    if self.partner_id:
        self.name = self.partner_id.name
```

### @api.model
```python
@api.model
def create(self, vals):
    # Called on model, not recordset
    return super().create(vals)
```

### @api.model_create_multi
```python
@api.model_create_multi
def create(self, vals_list):
    # Batch create (Odoo 17+)
    return super().create(vals_list)
```

---

## 6. Common ORM Methods

### CRUD
```python
# Create
record = self.env['model'].create({'name': 'New'})

# Read
records = self.env['model'].search([('active', '=', True)])
data = records.read(['name', 'amount'])

# Update
record.write({'name': 'Updated'})

# Delete
record.unlink()
```

### Search Methods
```python
# search() - Returns recordset
records = self.env['model'].search([
    ('state', '=', 'done'),
    ('date', '>=', '2024-01-01'),
], limit=10, order='date desc')

# search_count() - Returns int
count = self.env['model'].search_count([('active', '=', True)])

# search_read() - Returns list of dicts
data = self.env['model'].search_read([...], ['name', 'amount'], limit=5)

# browse() - Get by IDs
record = self.env['model'].browse(123)
records = self.env['model'].browse([1, 2, 3])
```

### Recordset Operations
```python
# Iteration
for record in records:
    print(record.name)

# Filter
filtered = records.filtered(lambda r: r.amount > 100)

# Map
names = records.mapped('name')
partner_names = records.mapped('partner_id.name')

# Sort
sorted_records = records.sorted(key=lambda r: r.date, reverse=True)
```

---

## 7. Environment

```python
# Access current user
user = self.env.user

# Access current company
company = self.env.company

# Access context
lang = self.env.context.get('lang')

# Change context
new_env = self.env(context={'lang': 'vi_VN'})

# Sudo (bypass access rights)
records = self.env['model'].sudo().search([])

# With user
records = self.env['model'].with_user(user_id).search([])
```

---

## 8. Inheritance Patterns

### Extend Existing Model
```python
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    custom_field = fields.Char('Custom')
    
    def action_confirm(self):
        # Custom logic before
        result = super().action_confirm()
        # Custom logic after
        return result
```

### Create New Model Based on Existing
```python
class MyOrder(models.Model):
    _name = 'my.order'
    _inherit = 'sale.order'  # Copy all fields/methods
```

### Abstract Model (Mixin)
```python
class MyMixin(models.AbstractModel):
    _name = 'my.mixin'
    
    notes = fields.Text('Notes')

class MyModel(models.Model):
    _name = 'my.model'
    _inherit = ['my.mixin']
```

---

## 9. Exceptions

```python
from odoo.exceptions import UserError, ValidationError, AccessError

# UserError - User-facing error
raise UserError(_('Cannot delete confirmed record!'))

# ValidationError - Constraint violation
raise ValidationError(_('Invalid data!'))

# AccessError - Permission denied
raise AccessError(_('You do not have access to this record!'))
```

---

## 📌 Quick Reference

```python
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class TrcfMyModel(models.Model):
    _name = 'trcf.my.model'
    _description = 'My Model'
    _order = 'date desc'
    
    # Fields
    name = fields.Char('Name', required=True, index=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft')
    partner_id = fields.Many2one('res.partner', 'Partner')
    line_ids = fields.One2many('trcf.my.model.line', 'parent_id')
    total = fields.Float(compute='_compute_total', store=True)
    
    # Computed
    @api.depends('line_ids.amount')
    def _compute_total(self):
        for rec in self:
            rec.total = sum(rec.line_ids.mapped('amount'))
    
    # Constraint
    @api.constrains('total')
    def _check_total(self):
        if any(r.total < 0 for r in self):
            raise ValidationError(_('Total cannot be negative!'))
    
    # Action
    def action_done(self):
        self.write({'state': 'done'})
```

---

## 🔗 Tham khảo

- **ORM API**: https://www.odoo.com/documentation/19.0/vi/developer/reference/backend/orm.html
