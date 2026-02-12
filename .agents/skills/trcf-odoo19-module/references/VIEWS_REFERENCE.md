# Odoo 19 Views Reference (Full Syntax)

Hướng dẫn chi tiết về cấu trúc XML của các loại View trong Odoo 19.
Validation Status: Verified (aligned with Odoo 19 view architecture syntax).

## Table of Contents
- 1. List View (`<list>`)
- 2. Form View
- 3. Search View
- 4. Action & Menu

## 1. List View (`<list>`)
Thay thế cho `<tree>`. Hỗ trợ các thuộc tính trang trí dựa trên logic Python.

```xml
<list decoration-danger="state == 'cancelled'" 
      decoration-success="state == 'done'"
      default_order="date desc">
    <field name="name"/>
    <field name="partner_id"/>
    <field name="amount" sum="Tổng tiền"/>
    <field name="state" widget="badge" 
           decoration-info="state == 'draft'" 
           decoration-success="state == 'confirmed'"/>
</list>
```

## 2. Form View
Cấu trúc phân tầng: Header -> Sheet -> Groups.

```xml
<form>
    <header>
        <button name="action_confirm" string="Xác nhận" type="object" 
                invisible="state != 'draft'" class="oe_highlight"/>
        <field name="state" widget="statusbar" statusbar_visible="draft,confirmed,done"/>
    </header>
    <sheet>
        <div class="oe_button_box" name="button_box">
             <!-- Smart Buttons ở đây -->
        </div>
        <widget name="web_ribbon" title="Đã hủy" bg_color="text-bg-danger" invisible="state != 'cancelled'"/>
        <div class="oe_title">
            <label for="name"/>
            <h1><field name="name" placeholder="VD: Đơn hàng mới..."/></h1>
        </div>
        <group>
            <group name="info_left">
                <field name="partner_id" readonly="state != 'draft'"/>
                <field name="date"/>
            </group>
            <group name="info_right">
                <field name="user_id" widget="many2one_avatar_user"/>
                <field name="company_id" groups="base.group_multi_company"/>
            </group>
        </group>
        <notebook>
            <page string="Chi tiết">
                <field name="line_ids">
                    <list editable="bottom">
                        <field name="product_id"/>
                        <field name="qty"/>
                        <field name="price_unit"/>
                        <field name="price_subtotal"/>
                    </list>
                </field>
            </page>
        </notebook>
    </sheet>
    <div class="oe_chatter">
        <field name="message_follower_ids"/>
        <field name="activity_ids"/>
        <field name="message_ids"/>
    </div>
</form>
```

## 3. Search View
Gồm `<field>` (tìm kiếm text/mã), `<filter>` (lọc điều kiện), `<group>` (gom nhóm).

```xml
<search>
    <field name="name" string="Tên hoặc Mã" filter_domain="['|', ('name', 'ilike', self), ('code', 'ilike', self)]"/>
    <field name="partner_id"/>
    
    <filter string="Của tôi" name="my_orders" domain="[('user_id', '=', uid)]"/>
    <filter string="Chưa xong" name="not_done" domain="[('state', '!=', 'done')]"/>
    
    <separator/>
    <filter string="Ngày hôm nay" name="today" domain="[('date', '=', context_today().strftime('%Y-%m-%d'))]"/>

    <group expand="0" string="Gom nhóm theo">
        <filter string="Khách hàng" name="group_partner" context="{'group_by': 'partner_id'}"/>
        <filter string="Trạng thái" name="group_state" context="{'group_by': 'state'}"/>
    </group>
</search>
```

## 4. Action & Menu
```xml
<record id="action_trcf_order" model="ir.actions.act_window">
    <field name="name">Đơn hàng</field>
    <field name="res_model">trcf.order</field>
    <field name="view_mode">list,form</field>
    <field name="help" type="html">
        <p class="o_view_nocontent_smiling_face">Tạo đơn hàng đầu tiên!</p>
    </field>
</record>

<menuitem id="menu_trcf_root" name="TRCF Quản lý" sequence="10"/>
<menuitem id="menu_trcf_order" parent="menu_trcf_root" action="action_trcf_order" sequence="1"/>
```
