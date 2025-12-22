---
description: Tạo Odoo module chuẩn (không dùng ADK)
---

# Workflow: Tạo Odoo Module Chuẩn

> **Odoo 19**: Dùng `<list>` thay `<tree>`, `view_mode="list,form"`
> **Docs**: `context_odoo19/orm-reference.md`, `views-reference.md`, `owl-components.md`

## 📝 Quick Start

### 1. Tạo cấu trúc

```bash
cd custom_addons
MODULE="trcf_my_module"
mkdir -p $MODULE/{models,views,security,static/src/{js,xml}}
touch $MODULE/{__init__.py,__manifest__.py} $MODULE/models/__init__.py
```

### 2. Manifest (`__manifest__.py`)

```python
{
    'name': 'TRCF My Module',
    'version': '19.0.1.0.0',
    'category': 'Category',
    'summary': 'Brief summary',
    'author': 'Tuấn Rang Cà Phê',
    'depends': ['base'],
    'data': ['security/ir.model.access.csv', 'views/trcf_my_model_views.xml'],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
```

### 3. Init Files

```python
# __init__.py
from . import models

# models/__init__.py
from . import trcf_my_model
```

### 4. Model (`models/trcf_my_model.py`)

```python
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class TrcfMyModel(models.Model):
    _name = 'trcf.my.model'
    _description = 'My Model'
    _order = 'create_date desc'
    
    name = fields.Char('Name', required=True, index=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([('draft','Draft'),('done','Done')], default='draft')
    partner_id = fields.Many2one('res.partner', 'Partner')
    line_ids = fields.One2many('trcf.my.model.line', 'parent_id', 'Lines')
    total = fields.Float(compute='_compute_total', store=True)
    date = fields.Date(default=fields.Date.context_today)
    
    @api.depends('line_ids.amount')
    def _compute_total(self):
        for rec in self:
            rec.total = sum(rec.line_ids.mapped('amount'))
    
    def action_done(self):
        self.write({'state': 'done'})

class TrcfMyModelLine(models.Model):
    _name = 'trcf.my.model.line'
    _description = 'Line'
    parent_id = fields.Many2one('trcf.my.model', required=True, ondelete='cascade')
    name = fields.Char('Description', required=True)
    amount = fields.Float()
```

### 5. Views (`views/trcf_my_model_views.xml`)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- List (Odoo 19: <list> không còn <tree>) -->
    <record id="trcf_my_model_view_list" model="ir.ui.view">
        <field name="name">trcf.my.model.list</field>
        <field name="model">trcf.my.model</field>
        <field name="arch" type="xml">
            <list decoration-muted="not active">
                <field name="name"/>
                <field name="partner_id"/>
                <field name="total" sum="Total"/>
                <field name="state" widget="badge"/>
            </list>
        </field>
    </record>

    <!-- Form -->
    <record id="trcf_my_model_view_form" model="ir.ui.view">
        <field name="name">trcf.my.model.form</field>
        <field name="model">trcf.my.model</field>
        <field name="arch" type="xml">
            <form>
                <header>
                    <button name="action_done" string="Done" type="object" 
                            class="oe_highlight" invisible="state != 'draft'"/>
                    <field name="state" widget="statusbar"/>
                </header>
                <sheet>
                    <group>
                        <group><field name="name"/><field name="partner_id"/></group>
                        <group><field name="date"/><field name="total"/></group>
                    </group>
                    <notebook>
                        <page string="Lines">
                            <field name="line_ids">
                                <list editable="bottom">
                                    <field name="name"/><field name="amount"/>
                                </list>
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
                <field name="name"/><field name="partner_id"/>
                <filter string="Draft" name="draft" domain="[('state','=','draft')]"/>
            </search>
        </field>
    </record>

    <!-- Action + Menu -->
    <record id="trcf_my_model_action" model="ir.actions.act_window">
        <field name="name">My Models</field>
        <field name="res_model">trcf.my.model</field>
        <field name="view_mode">list,form</field>
    </record>
    <menuitem id="trcf_menu_root" name="My Module"/>
    <menuitem id="trcf_my_model_menu" name="Models" parent="trcf_menu_root" action="trcf_my_model_action"/>
</odoo>
```

### 6. Security (`security/ir.model.access.csv`)

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_trcf_my_model,trcf.my.model,model_trcf_my_model,base.group_user,1,1,1,1
access_trcf_my_model_line,trcf.my.model.line,model_trcf_my_model_line,base.group_user,1,1,1,1
```

### 7. OWL Component (Optional)

```javascript
/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class TrcfMyComponent extends Component {
    static template = "trcf_my_module.TrcfMyComponent";
    setup() {
        this.orm = useService("orm");
        this.state = useState({ items: [], loading: true });
        onWillStart(async () => {
            this.state.items = await this.orm.searchRead("trcf.my.model", [], ["name"]);
            this.state.loading = false;
        });
    }
}
registry.category("actions").add("trcf_my_component", TrcfMyComponent);
```

```xml
<!-- static/src/xml/trcf_my_component.xml -->
<templates><t t-name="trcf_my_module.TrcfMyComponent">
    <div class="p-3">
        <t t-if="state.loading">Loading...</t>
        <ul t-else="" t-foreach="state.items" t-as="item" t-key="item.id">
            <li t-esc="item.name"/>
        </ul>
    </div>
</t></templates>
```

### 8. Install & Test

// turbo
```bash
./odoo-bin -c odoo19.conf -u trcf_my_module --stop-after-init 2>&1 | tail -50
```

**Lỗi thường gặp:** `SyntaxError`→Python, `ParseError`→XML, `AccessError`→Security

## ✅ Checklist

- [ ] Manifest + Init
- [ ] Model + Views (`<list>` không `<tree>`)
- [ ] Security + Menu
- [ ] Test