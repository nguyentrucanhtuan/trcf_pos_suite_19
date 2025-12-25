---
description: Kiểm tra và tối ưu Odoo module hiện có
---

# Workflow: Tối ưu & Nâng cấp Module

Kiểm tra, sửa lỗi, tối ưu và thêm chức năng cho module Odoo 19.

> **Docs**: `context_odoo19/orm-reference.md`, `views-reference.md`

## 🎯 Chức năng

1. **Tối ưu** - Sửa deprecation, performance, security
2. **Nâng cấp** - Thêm fields, views, logic mới
3. **Refactor** - Cải thiện cấu trúc code

### 1. Phân tích Module

Kiểm tra cấu trúc module:
```bash
ls -la custom_addons/MODULE_NAME/
cat custom_addons/MODULE_NAME/__manifest__.py
```

### 2. Checklist Kiểm tra

#### A. Manifest
- [ ] Version format: `19.0.x.x.x`
- [ ] Depends đầy đủ
- [ ] Data files đúng thứ tự (security trước views)
- [ ] License: `LGPL-3`

#### B. Models
- [ ] Import đúng: `from odoo import api, fields, models, _`
- [ ] `_name`, `_description` đầy đủ
- [ ] Index trên fields thường search: `index=True`
- [ ] Computed fields có `store=True` nếu cần query
- [ ] `@api.depends()` đầy đủ dependencies
- [ ] `@api.constrains()` cho validation
- [ ] SQL constraints cho unique/check

#### C. Views (Odoo 19)
- [ ] Dùng `<list>` thay `<tree>`
- [ ] `view_mode="list,form"` thay `tree,form`
- [ ] `invisible="expression"` thay `attrs`
- [ ] Search view có filters và group by

#### D. Security
- [ ] File `ir.model.access.csv` có tất cả models
- [ ] Quyền đúng: user vs manager
- [ ] Record rules nếu cần

#### E. Performance
- [ ] Không dùng `search()` trong vòng lặp
- [ ] Dùng `mapped()` thay vì list comprehension với ORM
- [ ] Batch write với `write()` một lần
- [ ] Computed fields non-stored cho UI-only

### 3. Sửa lỗi phổ biến

**Lỗi `<tree>` deprecated:**
```xml
<!-- Sai -->
<tree>...</tree>
<!-- Đúng -->
<list>...</list>
```

**Lỗi `attrs` deprecated:**
```xml
<!-- Sai -->
<field name="x" attrs="{'invisible': [('state','=','done')]}"/>
<!-- Đúng -->
<field name="x" invisible="state == 'done'"/>
```

**Lỗi performance:**
```python
# Sai - N+1 query
for rec in self:
    partner = self.env['res.partner'].search([('id','=',rec.partner_id.id)])
    
# Đúng - Prefetch
partners = self.mapped('partner_id')
```

**Lỗi computed không store:**
```python
# Nếu cần search/filter, thêm store=True
total = fields.Float(compute='_compute_total', store=True)
```

**Lỗi Search View XML (Odoo 19):**

> ⚠️ **QUAN TRỌNG**: Odoo 19 có XML schema rất strict cho search views!

```xml
<!-- ❌ SAI - Dùng Python expressions phức tạp trong domain -->
<filter name="today" 
    domain="[('date','>=',datetime.datetime.combine(context_today(),datetime.time(0,0,0)))]"/>

<!-- ✅ ĐÚNG - Dùng expressions đơn giản -->
<filter name="today" 
    domain="[('date','>=',datetime.datetime.now().replace(hour=0,minute=0,second=0).strftime('%Y-%m-%d %H:%M:%S'))]"/>

<!-- ❌ SAI - Dùng <group> với string attribute cho group-by -->
<group expand="0" string="Nhóm theo">
    <filter name="group_date" context="{'group_by':'date'}"/>
</group>

<!-- ✅ ĐÚNG - Bỏ <group> wrapper, đặt filters trực tiếp -->
<separator/>
<filter name="group_date" string="Ngày" context="{'group_by':'date'}"/>
<filter name="group_status" string="Trạng thái" context="{'group_by':'state'}"/>

<!-- ❌ SAI - Đặt <field> sau <filter> -->
<search>
    <filter name="my_filter" domain="[...]"/>
    <field name="name"/>  <!-- Sai vị trí -->
</search>

<!-- ✅ ĐÚNG - <field> phải đứng trước <filter> -->
<search>
    <field name="name"/>
    <field name="partner_id"/>
    <filter name="my_filter" domain="[...]"/>
</search>
```

**Template search view tối giản (luôn work):**
```xml
<record id="view_my_search" model="ir.ui.view">
    <field name="name">my.model.search</field>
    <field name="model">my.model</field>
    <field name="arch" type="xml">
        <search>
            <field name="name"/>
            <field name="partner_id"/>
            <filter name="filter_today" string="Hôm nay" 
                domain="[('date','>=',datetime.datetime.now().replace(hour=0,minute=0,second=0).strftime('%Y-%m-%d %H:%M:%S'))]"/>
            <filter name="filter_active" string="Active" domain="[('active','=',True)]"/>
            <separator/>
            <filter name="group_by_date" string="Ngày" context="{'group_by':'date:day'}"/>
        </search>
    </field>
</record>
```

**Set default filter trong action:**
```xml
<field name="context">{'search_default_filter_today': 1}</field>
<field name="search_view_id" ref="view_my_search"/>
```

### 4. Test sau tối ưu

// turbo
```bash
./odoo-bin -c odoo19.conf -u MODULE_NAME --stop-after-init 2>&1 | tail -50
```

### 5. (Optional) Chuẩn bị Cython

Nếu cần bảo mật code, xem: `docs/cython_compilation.md`

```
models/
├── business_logic.py  # ✅ Compile
├── prompts.py         # ✅ Compile (nếu ADK)
└── my_model.py        # ❌ Không compile (Odoo model)
```

## 📝 Prompt mẫu

**Chỉ tối ưu:**
```
/trcf_optimize_module
Kiểm tra và sửa lỗi Odoo 19 cho module trcf_my_module
```

**Tối ưu + Thêm chức năng:**
```
/trcf_optimize_module
Tối ưu module trcf_inventory và thêm:
- Field tracking_number cho phiếu kiểm
- Button export Excel
- Filter theo ngày tạo
```

**Nâng cấp logic:**
```
/trcf_optimize_module
Nâng cấp trcf_pos_report:
- Thêm biểu đồ doanh thu theo giờ
- Tính toán margin tự động
```

## ✅ Output

Sau khi chạy workflow, AI sẽ:
1. Phân tích module hiện tại
2. Liệt kê vấn đề + đề xuất cải tiến
3. Thêm chức năng mới (nếu yêu cầu)
4. Áp dụng thay đổi (sau khi confirm)
5. Test lại module
