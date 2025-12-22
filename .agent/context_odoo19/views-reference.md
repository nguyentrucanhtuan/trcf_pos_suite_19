# Odoo 19 Views Reference

> **Source**: https://www.odoo.com/documentation/19.0/vi/developer/reference/user_interface/view_architectures.html
>
> **Last Updated**: 2025-12-22

---

## ⚠️ QUAN TRỌNG: Thay đổi trong Odoo 19

> **`<tree>` → `<list>`**: Trong Odoo 19, element `<tree>` đã được đổi tên thành `<list>`. Tên cũ `<tree>` vẫn hoạt động nhưng deprecated.

---

## 1. View Types

| Type | Mô tả | XML Element |
|------|-------|-------------|
| Form | Chi tiết record | `<form>` |
| **List** | Danh sách records | `<list>` (**Odoo 19**, cũ: `<tree>`) |
| Search | Filter/Group | `<search>` |
| Kanban | Cards view | `<kanban>` |
| Calendar | Calendar view | `<calendar>` |
| Graph | Charts | `<graph>` |
| Pivot | Pivot table | `<pivot>` |

---

## 2. Form View

### Cấu trúc cơ bản
```xml
<record id="trcf_my_model_view_form" model="ir.ui.view">
    <field name="name">trcf.my.model.form</field>
    <field name="model">trcf.my.model</field>
    <field name="arch" type="xml">
        <form>
            <header>
                <!-- Buttons & Status -->
            </header>
            <sheet>
                <!-- Main content -->
            </sheet>
            <chatter/>
        </form>
    </field>
</record>
```

### Header với Buttons và Statusbar
```xml
<header>
    <button name="action_confirm" string="Confirm" type="object"
            class="oe_highlight" invisible="state != 'draft'"/>
    <button name="action_done" string="Done" type="object"
            invisible="state != 'confirmed'"/>
    <field name="state" widget="statusbar" 
           statusbar_visible="draft,confirmed,done"/>
</header>
```

### Sheet với Groups
```xml
<sheet>
    <div class="oe_title">
        <h1><field name="name" placeholder="Title..."/></h1>
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
                <list editable="bottom">
                    <field name="name"/>
                    <field name="amount"/>
                </list>
            </field>
        </page>
        <page string="Notes">
            <field name="notes"/>
        </page>
    </notebook>
</sheet>
```

### invisible Attribute (Odoo 17+)
```xml
<!-- Odoo 17+: dùng expression Python -->
<field name="field1" invisible="state != 'draft'"/>
<button invisible="not active"/>

<!-- Nhiều điều kiện -->
<field invisible="state == 'done' or not partner_id"/>
```

### Widgets thường dùng
```xml
<field name="state" widget="statusbar"/>
<field name="tags" widget="many2many_tags"/>
<field name="color" widget="color"/>
<field name="image" widget="image"/>
<field name="date" widget="date"/>
<field name="amount" widget="monetary"/>
<field name="progress" widget="progressbar"/>
<field name="html_content" widget="html"/>
```

---

## 3. List View (Odoo 19: `<list>`, cũ: `<tree>`)

### Cấu trúc cơ bản
```xml
<record id="trcf_my_model_view_list" model="ir.ui.view">
    <field name="name">trcf.my.model.list</field>
    <field name="model">trcf.my.model</field>
    <field name="arch" type="xml">
        <list decoration-muted="not active"
              decoration-danger="state == 'cancel'">
            <field name="name"/>
            <field name="partner_id"/>
            <field name="date"/>
            <field name="total_amount" sum="Total"/>
            <field name="state" widget="badge"/>
        </list>
    </field>
</record>
```

### Decorations
```xml
<list decoration-muted="not active"
      decoration-info="state == 'draft'"
      decoration-success="state == 'done'"
      decoration-warning="state == 'pending'"
      decoration-danger="state == 'cancel'">
```

### Editable List
```xml
<list editable="bottom">
    <!-- editable="bottom" hoặc "top" -->
</list>
```

### Optional Fields
```xml
<field name="partner_id" optional="show"/>
<field name="date" optional="hide"/>
```

---

## 4. Search View

```xml
<record id="trcf_my_model_view_search" model="ir.ui.view">
    <field name="name">trcf.my.model.search</field>
    <field name="model">trcf.my.model</field>
    <field name="arch" type="xml">
        <search>
            <!-- Search fields -->
            <field name="name"/>
            <field name="partner_id"/>
            
            <!-- Filters -->
            <filter string="Active" name="active" 
                    domain="[('active', '=', True)]"/>
            <filter string="Draft" name="draft" 
                    domain="[('state', '=', 'draft')]"/>
            <separator/>
            <filter string="Archived" name="inactive" 
                    domain="[('active', '=', False)]"/>
            
            <!-- Group By -->
            <group expand="0" string="Group By">
                <filter string="Partner" name="group_partner" 
                        context="{'group_by': 'partner_id'}"/>
                <filter string="State" name="group_state" 
                        context="{'group_by': 'state'}"/>
                <filter string="Date" name="group_date" 
                        context="{'group_by': 'date:month'}"/>
            </group>
        </search>
    </field>
</record>
```

---

## 5. Actions

### Window Action
```xml
<record id="trcf_my_model_action" model="ir.actions.act_window">
    <field name="name">My Models</field>
    <field name="res_model">trcf.my.model</field>
    <field name="view_mode">list,form</field>
    <field name="context">{'default_active': True}</field>
    <field name="domain">[('state', '!=', 'cancel')]</field>
    <field name="help" type="html">
        <p class="o_view_nocontent_smiling_face">
            Create your first record!
        </p>
    </field>
</record>
```

### Action với Search
```xml
<record id="trcf_my_model_action" model="ir.actions.act_window">
    <field name="name">My Models</field>
    <field name="res_model">trcf.my.model</field>
    <field name="view_mode">list,form</field>
    <field name="search_view_id" ref="trcf_my_model_view_search"/>
    <field name="context">{'search_default_active': 1}</field>
</record>
```

---

## 6. Menu Items

```xml
<!-- Root menu -->
<menuitem id="trcf_my_module_menu_root" 
          name="My Module"
          web_icon="trcf_my_module,static/description/icon.png"/>

<!-- Child menu -->
<menuitem id="trcf_my_model_menu" 
          name="My Models"
          parent="trcf_my_module_menu_root"
          action="trcf_my_model_action"
          sequence="10"/>

<!-- Submenu under existing Odoo menu -->
<menuitem id="trcf_product_menu"
          name="Custom Products"
          parent="sale.sale_menu_root"
          action="trcf_product_action"/>
```

---

## 7. Inherit Views

### Extend Form View
```xml
<record id="view_partner_form_inherit" model="ir.ui.view">
    <field name="name">res.partner.form.inherit.trcf</field>
    <field name="model">res.partner</field>
    <field name="inherit_id" ref="base.view_partner_form"/>
    <field name="arch" type="xml">
        <!-- Add field after -->
        <field name="phone" position="after">
            <field name="custom_field"/>
        </field>
        
        <!-- Add inside -->
        <page name="sales_purchases" position="inside">
            <group string="Custom Info">
                <field name="custom_note"/>
            </group>
        </page>
        
        <!-- Replace -->
        <field name="comment" position="replace">
            <field name="comment" widget="html"/>
        </field>
        
        <!-- Add attributes -->
        <field name="email" position="attributes">
            <attribute name="required">1</attribute>
        </field>
    </field>
</record>
```

### Position Options
| Position | Mô tả |
|----------|-------|
| `after` | Thêm sau element |
| `before` | Thêm trước element |
| `inside` | Thêm vào trong element |
| `replace` | Thay thế element |
| `attributes` | Sửa attributes |

---

## 8. Buttons

### Object Button (Call Python method)
```xml
<button name="action_confirm" string="Confirm" type="object"
        class="oe_highlight" confirm="Are you sure?"/>
```

### Action Button (Open action)
```xml
<button name="%(trcf_my_action)d" string="Open" type="action"/>
```

### Smart Button
```xml
<div class="oe_button_box" name="button_box">
    <button class="oe_stat_button" type="object"
            name="action_view_orders" icon="fa-shopping-cart">
        <field name="order_count" widget="statinfo" string="Orders"/>
    </button>
</div>
```

---

## 📌 Template Nhanh

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <!-- List (Odoo 19: <list>, không còn dùng <tree>) -->
    <record id="trcf_MODEL_view_list" model="ir.ui.view">
        <field name="name">trcf.MODEL.list</field>
        <field name="model">trcf.MODEL</field>
        <field name="arch" type="xml">
            <list>
                <field name="name"/>
                <field name="state" widget="badge"/>
            </list>
        </field>
    </record>

    <!-- Form -->
    <record id="trcf_MODEL_view_form" model="ir.ui.view">
        <field name="name">trcf.MODEL.form</field>
        <field name="model">trcf.MODEL</field>
        <field name="arch" type="xml">
            <form>
                <header>
                    <field name="state" widget="statusbar"/>
                </header>
                <sheet>
                    <group>
                        <field name="name"/>
                    </group>
                </sheet>
            </form>
        </field>
    </record>

    <!-- Search -->
    <record id="trcf_MODEL_view_search" model="ir.ui.view">
        <field name="name">trcf.MODEL.search</field>
        <field name="model">trcf.MODEL</field>
        <field name="arch" type="xml">
            <search>
                <field name="name"/>
            </search>
        </field>
    </record>

    <!-- Action -->
    <record id="trcf_MODEL_action" model="ir.actions.act_window">
        <field name="name">Models</field>
        <field name="res_model">trcf.MODEL</field>
        <field name="view_mode">list,form</field>
    </record>

    <!-- Menu -->
    <menuitem id="trcf_menu_root" name="My Module"/>
    <menuitem id="trcf_MODEL_menu" name="Models" 
              parent="trcf_menu_root" action="trcf_MODEL_action"/>
</odoo>
```

---

## 🔗 Tham khảo

- **Views**: https://www.odoo.com/documentation/19.0/vi/developer/reference/user_interface/view_architectures.html
