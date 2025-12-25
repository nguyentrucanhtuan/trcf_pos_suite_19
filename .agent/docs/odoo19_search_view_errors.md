# Odoo 19 Search View - Common Errors & Solutions

> 📝 Document này ghi lại các lỗi XML validation thường gặp khi tạo search views trong Odoo 19

## ❌ Lỗi đã gặp trong trcf_minvoice optimization

### 1. Python Expressions Phức Tạp trong Domain

**Lỗi**:
```xml
<filter name="filter_today" 
    domain="[('date_order', '>=', datetime.datetime.combine(context_today(), datetime.time(0,0,0)))]"/>
```

**Error message**:
```
ParseError: Invalid view definition
```

**Nguyên nhân**: Odoo XML parser không hỗ trợ `datetime.datetime.combine()` và các nested function calls phức tạp.

**Giải pháp**:
```xml
<filter name="filter_today" 
    domain="[('date_order','>=',datetime.datetime.now().replace(hour=0,minute=0,second=0).strftime('%Y-%m-%d %H:%M:%S'))]"/>
```

---

### 2. Group Element với Invalid Attributes

**Lỗi**:
```xml
<group expand="0" string="Nhóm theo">
    <filter name="group_by_date" context="{'group_by':'date'}"/>
</group>
```

**Error message**:
```
ERROR:RELAXNGV:RELAXNG_ERR_INVALIDATTR: Invalid attribute expand for element group
ERROR:RELAXNGV:RELAXNG_ERR_INVALIDATTR: Invalid attribute string for element group
ERROR:RELAXNGV:RELAXNG_ERR_NOELEM: Expecting an element field, got nothing
```

**Nguyên nhân**: 
- Odoo 19 search view `<group>` không hỗ trợ attributes `expand` và `string`
- `<group>` phải chứa `<field>` elements, không phải `<filter>`

**Giải pháp**: Bỏ `<group>` wrapper hoàn toàn
```xml
<separator/>
<filter name="group_by_date" string="Ngày" context="{'group_by':'date:day'}"/>
<filter name="group_by_status" string="Trạng thái" context="{'group_by':'state'}"/>
```

---

### 3. Field Elements Đặt Sai Vị Trí

**Lỗi**:
```xml
<search>
    <filter name="my_filter" domain="[...]"/>
    <field name="name"/>  <!-- SAI: field sau filter -->
</search>
```

**Error message**:
```
ERROR:RELAXNGV:RELAXNG_ERR_EXTRACONTENT: Element search has extra content: field
```

**Nguyên nhân**: Odoo 19 schema yêu cầu `<field>` elements phải đứng trước `<filter>` elements.

**Giải pháp**:
```xml
<search>
    <field name="name"/>
    <field name="partner_id"/>
    <filter name="my_filter" domain="[...]"/>
</search>
```

---

### 4. Frontend Domain Evaluation Error

**Lỗi**:
```xml
<filter name="filter_today" 
    domain="[('date_order','>=',datetime.datetime.now().replace(hour=0,minute=0,second=0).strftime('%Y-%m-%d %H:%M:%S'))]"/>
```

**Error message** (trong browser console):
```
OwlError: An error occured in the owl lifecycle
Caused by: TypeError: Function.prototype.apply was called on undefined
```

**Nguyên nhân**: 
- Domain filter được evaluate **2 lần**: Backend (Python) khi load view + Frontend (JavaScript) khi hiển thị filter
- `datetime.datetime.now()` chỉ tồn tại trong Python, không có trong JavaScript
- Khi Odoo frontend cố parse domain này → lỗi vì JS không có module `datetime`

**Giải pháp**: Dùng các functions được Odoo hỗ trợ cả backend và frontend

```xml
<!-- ✅ ĐÚNG - Dùng time.strftime() cho ngày hiện tại -->
<filter name="filter_today" string="Hôm nay" 
    domain="[('date_order','>=',time.strftime('%Y-%m-%d 00:00:00')),('date_order','<=',time.strftime('%Y-%m-%d 23:59:59'))]"/>

<!-- ✅ ĐÚNG - Dùng context_today() cho date calculations -->
<filter name="filter_last_7_days" string="7 ngày qua" 
    domain="[('date_order','>=',(context_today()-datetime.timedelta(days=7)).strftime('%Y-%m-%d'))]"/>
```

**Functions được hỗ trợ trong domain filters:**
- ✅ `time.strftime()` - Format thời gian hiện tại
- ✅ `context_today()` - Ngày hiện tại (date object)
- ✅ `datetime.timedelta()` - Tính toán khoảng thời gian
- ✅ `uid` - User ID hiện tại
- ✅ `context.get()` - Lấy giá trị từ context
- ❌ `datetime.datetime.now()` - KHÔNG work ở frontend
- ❌ `datetime.datetime.combine()` - KHÔNG work ở frontend

---

## ✅ Template Chuẩn (Luôn Work)

```xml
<?xml version="1.0" encoding="utf-8"?>
<odoo>
    <record id="view_model_search" model="ir.ui.view">
        <field name="name">model.name.search</field>
        <field name="model">model.name</field>
        <field name="arch" type="xml">
            <search>
                <!-- 1. Fields PHẢI đứng đầu -->
                <field name="name"/>
                <field name="partner_id"/>
                <field name="date_field"/>
                
                <!-- 2. Filters -->
                <filter name="filter_today" string="Hôm nay" 
                    domain="[('date_field','>=',time.strftime('%Y-%m-%d 00:00:00')),('date_field','<=',time.strftime('%Y-%m-%d 23:59:59'))]"/>
                
                <filter name="filter_active" string="Active" 
                    domain="[('active','=',True)]"/>
                
                <filter name="filter_last_7_days" string="7 ngày qua" 
                    domain="[('date_field','>=',(context_today()-datetime.timedelta(days=7)).strftime('%Y-%m-%d'))]"/>
                
                <!-- 3. Separator trước group-by -->
                <separator/>
                
                <!-- 4. Group-by filters (KHÔNG dùng <group> wrapper) -->
                <filter name="group_by_date" string="Ngày" 
                    context="{'group_by':'date_field:day'}"/>
                
                <filter name="group_by_partner" string="Khách hàng" 
                    context="{'group_by':'partner_id'}"/>
            </search>
        </field>
    </record>
</odoo>
```

---

## 🔧 Set Default Filter

**Trong action XML**:
```xml
<record id="action_my_model" model="ir.actions.act_window">
    <field name="name">My Model</field>
    <field name="res_model">my.model</field>
    <field name="view_mode">list,form</field>
    
    <!-- Set filter "today" active mặc định -->
    <field name="context">{'search_default_filter_today': 1}</field>
    
    <!-- Link search view -->
    <field name="search_view_id" ref="view_model_search"/>
</record>
```

**Context key format**: `search_default_<filter_name>: 1`

---

## 📋 Checklist Khi Tạo Search View

- [ ] `<field>` elements đứng trước `<filter>` elements
- [ ] Không dùng `<group>` wrapper cho group-by filters
- [ ] Không dùng attributes `expand` hoặc `string` trong `<group>`
- [ ] Domain filters dùng expressions đơn giản (tránh nested functions)
- [ ] Dùng `datetime.datetime.now().replace()` thay vì `datetime.datetime.combine()`
- [ ] Dùng `.strftime('%Y-%m-%d %H:%M:%S')` để format datetime
- [ ] Set default filter qua `search_default_<name>` trong action context
- [ ] Link search view qua `search_view_id` trong action

---

## 🎯 Bài học rút ra

1. **Keep it simple**: Odoo 19 XML parser rất strict, dùng cú pháp đơn giản nhất
2. **No wrappers**: Bỏ các `<group>` wrappers không cần thiết
3. **Order matters**: `<field>` trước, `<filter>` sau
4. **Frontend-compatible domains**: Chỉ dùng functions được hỗ trợ cả backend và frontend (`time.strftime()`, `context_today()`)
5. **Avoid datetime.datetime.now()**: Function này chỉ work ở backend, gây lỗi khi frontend parse domain
6. **Test incrementally**: Thêm từng filter một và test ngay để catch errors sớm
7. **Use template**: Copy template chuẩn và modify thay vì viết từ đầu

