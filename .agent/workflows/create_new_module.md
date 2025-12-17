---
description: Tạo Odoo module chuẩn (không dùng ADK)
---

# Workflow: Tạo Odoo Module Chuẩn

Workflow tạo Odoo module thông thường theo chuẩn dự án.

## 📋 Prerequisites

- Odoo 19 đã cài đặt
- Đọc `custom_addons/.agent/docs/naming_conventions.md`

## 🎯 Module Types

1. **Simple Model** - CRUD cơ bản
2. **Extension** - Extend existing models
3. **POS Module** - Point of Sale integration
4. **Report** - Dashboard/Reports
5. **Integration** - External services

## 📝 Quick Start

### 1. Tạo cấu trúc

```bash
cd custom_addons
MODULE="trcf_my_module"
mkdir -p $MODULE/{models,views,security,static/src/{js,css,xml},data}
touch $MODULE/{__init__.py,__manifest__.py}
touch $MODULE/models/__init__.py
touch $MODULE/security/ir.model.access.csv
```

### 2. Manifest (`__manifest__.py`)

```python
{
    'name': 'TRCF My Module',
    'version': '1.0',
    'category': 'Category',
    'summary': 'Brief summary',
    'description': """Features: Feature 1, Feature 2""",
    'author': 'Tuấn Rang Cà Phê',
    'website': 'https://coffeetree.vn',
    'depends': ['base'],  # Add: sale, stock, point_of_sale, etc.
    'data': [
        'security/ir.model.access.csv',
        'views/trcf_my_model_views.xml',
    ],
    'assets': {
        # 'web.assets_backend': ['module/static/src/js/file.js'],
    },
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
```

### 3. Init Files

**`__init__.py`:**
```python
from . import models
```

**`models/__init__.py`:**
```python
from . import trcf_my_model
```

### 4. Model

#### A. New Model (`models/trcf_my_model.py`)

```python
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class TrcfMyModel(models.Model):
    _name = 'trcf.my.model'
    _description = 'My Model'
    _order = 'create_date desc'
    
    # Basic fields
    name = fields.Char('Name', required=True, index=True)
    description = fields.Text('Description')
    active = fields.Boolean('Active', default=True)
    
    # Selection
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
    ], default='draft', required=True)
    
    # Relations
    user_id = fields.Many2one('res.users', 'Responsible', 
                              default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', 'Partner')
    line_ids = fields.One2many('trcf.my.model.line', 'parent_id', 'Lines')
    tag_ids = fields.Many2many('trcf.my.tag', string='Tags')
    
    # Computed
    total_amount = fields.Float('Total', compute='_compute_total', store=True)
    line_count = fields.Integer('Lines', compute='_compute_line_count')
    
    # Dates
    date = fields.Date('Date', default=fields.Date.context_today, required=True)
    
    @api.depends('line_ids.amount')
    def _compute_total(self):
        for rec in self:
            rec.total_amount = sum(rec.line_ids.mapped('amount'))
    
    @api.depends('line_ids')
    def _compute_line_count(self):
        for rec in self:
            rec.line_count = len(rec.line_ids)
    
    @api.constrains('total_amount')
    def _check_total(self):
        if any(rec.total_amount < 0 for rec in self):
            raise ValidationError(_('Total cannot be negative!'))
    
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Name must be unique!'),
    ]
    
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_done(self):
        self.write({'state': 'done'})

class TrcfMyModelLine(models.Model):
    _name = 'trcf.my.model.line'
    _description = 'Line'
    
    parent_id = fields.Many2one('trcf.my.model', required=True, ondelete='cascade')
    name = fields.Char('Description', required=True)
    amount = fields.Float('Amount', default=0.0)
```

#### B. Inherit Model

```python
class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    custom_field = fields.Char('Custom Field')
    custom_total = fields.Float('Custom Total', compute='_compute_custom_total')
    
    @api.depends('order_line.price_total')
    def _compute_custom_total(self):
        for order in self:
            order.custom_total = sum(order.order_line.mapped('price_total'))
    
    def action_confirm(self):
        # Custom logic before
        result = super().action_confirm()
        # Custom logic after
        return result
```

### 5. Views (`views/trcf_my_model_views.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- Tree -->
    <record id="trcf_my_model_view_tree" model="ir.ui.view">
        <field name="name">trcf.my.model.tree</field>
        <field name="model">trcf.my.model</field>
        <field name="arch" type="xml">
            <tree decoration-muted="not active">
                <field name="name"/>
                <field name="partner_id"/>
                <field name="total_amount"/>
                <field name="state" widget="badge"/>
            </tree>
        </field>
    </record>

    <!-- Form -->
    <record id="trcf_my_model_view_form" model="ir.ui.view">
        <field name="name">trcf.my.model.form</field>
        <field name="model">trcf.my.model</field>
        <field name="arch" type="xml">
            <form>
                <header>
                    <button name="action_confirm" string="Confirm" type="object" 
                            class="oe_highlight" invisible="state != 'draft'"/>
                    <button name="action_done" string="Done" type="object" 
                            invisible="state != 'confirmed'"/>
                    <field name="state" widget="statusbar"/>
                </header>
                <sheet>
                    <div class="oe_title">
                        <h1><field name="name"/></h1>
                    </div>
                    <group>
                        <group>
                            <field name="partner_id"/>
                            <field name="date"/>
                        </group>
                        <group>
                            <field name="total_amount"/>
                            <field name="active"/>
                        </group>
                    </group>
                    <notebook>
                        <page string="Lines">
                            <field name="line_ids">
                                <tree editable="bottom">
                                    <field name="name"/>
                                    <field name="amount"/>
                                </tree>
                            </field>
                        </page>
                    </notebook>
                </sheet>
            </form>
        </field>
    </record>

    <!-- Search -->
    <record id="trcf_my_model_view_search" model="ir.ui.view">
        <field name="name">trcf.my.model.search</field>
        <field name="model">trcf.my.model</field>
        <field name="arch" type="xml">
            <search>
                <field name="name"/>
                <field name="partner_id"/>
                <filter string="Draft" name="draft" domain="[('state','=','draft')]"/>
                <filter string="Done" name="done" domain="[('state','=','done')]"/>
                <group expand="0" string="Group By">
                    <filter string="Partner" name="group_partner" 
                            context="{'group_by':'partner_id'}"/>
                    <filter string="Status" name="group_state" 
                            context="{'group_by':'state'}"/>
                </group>
            </search>
        </field>
    </record>

    <!-- Action -->
    <record id="trcf_my_model_action" model="ir.actions.act_window">
        <field name="name">My Models</field>
        <field name="res_model">trcf.my.model</field>
        <field name="view_mode">tree,form</field>
    </record>

    <!-- Menu -->
    <menuitem id="trcf_my_module_menu_root" name="My Module"/>
    <menuitem id="trcf_my_model_menu" name="My Models" 
              parent="trcf_my_module_menu_root" 
              action="trcf_my_model_action"/>
</odoo>
```

### 6. Security (`security/ir.model.access.csv`)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_trcf_my_model_user,trcf.my.model.user,model_trcf_my_model,base.group_user,1,1,1,0
access_trcf_my_model_manager,trcf.my.model.manager,model_trcf_my_model,base.group_system,1,1,1,1
access_trcf_my_model_line,trcf.my.model.line,model_trcf_my_model_line,base.group_user,1,1,1,1
```

### 7. (Optional) Controller

```bash
mkdir controllers
touch controllers/{__init__.py,trcf_main_controller.py}
```

**`controllers/trcf_main_controller.py`:**
```python
from odoo import http
from odoo.http import request

class TrcfController(http.Controller):
    
    @http.route('/my_module/api/data', type='json', auth='user')
    def get_data(self, **kw):
        records = request.env['trcf.my.model'].search([])
        return {'success': True, 'data': records.read(['name', 'total_amount'])}
```

Update root `__init__.py`:
```python
from . import models, controllers
```

### 8. Install & Test

```bash
# Restart Odoo or upgrade module
# Apps > Update Apps List > Install "TRCF My Module"
```

**Test via shell:**
```python
rec = env['trcf.my.model'].create({'name': 'Test'})
rec.action_confirm()
```

## 🔑 Key Patterns

### Model Patterns
- **New model**: `_name = 'trcf.feature.entity'`
- **Inherit**: `_inherit = 'existing.model'`
- **Computed**: `@api.depends()` + `compute=`
- **Constraints**: `@api.constrains()` + `_sql_constraints`
- **Actions**: `action_<verb>()` methods

### View Patterns
- **Tree**: List view with `decoration-*`
- **Form**: Header (buttons + statusbar) + Sheet + Notebook
- **Search**: Filters + Group By
- **Action**: `ir.actions.act_window`
- **Menu**: Hierarchical structure

### Naming (See `docs/naming_conventions.md`)
- Module: `trcf_<feature>`
- Model: `trcf.<feature>.<entity>`
- Class: `Trcf<Feature><Entity>`
- Files: `trcf_<entity>_<type>.xml`

## ✅ Checklist

- [ ] Structure created
- [ ] Manifest configured
- [ ] Models defined
- [ ] Views created (tree, form, search)
- [ ] Security set
- [ ] Menu items added
- [ ] Module installed
- [ ] CRUD tested
- [ ] Business logic verified

## 📚 References

- Examples: `trcf_kitchen_screen`, `trcf_payment_momo`
- Odoo Docs: https://www.odoo.com/documentation/19.0/