# Odoo 19 OWL Guide (Full Structure)

Hướng dẫn chi tiết cách viết một OWL Component chuẩn ESM trong Odoo 19.

## 1. Cấu trúc Component File (`.js`)
Sử dụng ES Modules và tích hợp các Services của Odoo.

```javascript
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class TrcfDashboard extends Component {
    static template = "trcf_module.DashboardTemplate";
    
    setup() {
        // Khai báo Services
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        // Quản lý trạng thái phản xạ (Reactive)
        this.state = useState({
            records: [],
            loading: true,
        });

        // Lifecycle Hook
        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;
        this.state.records = await this.orm.searchRead("trcf.order", [], ["name", "amount"]);
        this.state.loading = false;
    }

    onItemClick(id) {
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "trcf.order",
            res_id: id,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

// Đăng ký vào Registry nếu cần (VD: làm trang Client Action)
registry.category("actions").add("trcf_dashboard_action", TrcfDashboard);
```

## 2. Cấu trúc Template File (`.xml`)
Sử dụng thẻ `<t t-name="...">` và cú pháp OWL.

```xml
<templates xml:space="preserve">
    <t t-name="trcf_module.DashboardTemplate">
        <div class="o_dashboard_container p-3">
            <h3>Bảng điều khiển TRCF</h3>
            <div t-if="state.loading" class="text-center">
                <i class="fa fa-spinner fa-spin"/> Đang tải...
            </div>
            <div t-else="" class="row">
                <t t-foreach="state.records" t-as="record" t-key="record.id">
                    <div class="col-4 p-2">
                        <div class="card pointer" t-on-click="() => this.onItemClick(record.id)">
                            <div class="card-body">
                                <h5 t-esc="record.name"/>
                                <p t-esc="record.amount"/>
                            </div>
                        </div>
                    </div>
                </t>
            </div>
        </div>
    </t>
</templates>
```

## 3. Các Hooks thông dụng
- **`onWillStart`**: Chạy trước khi render (thường dùng để load data).
- **`onMounted`**: Chạy ngay sau khi component xuất hiện trên DOM.
- **`onWillUnmount`**: Chạy trước khi component bị hủy.
- **`onWillUpdateProps`**: Chạy khi props thay đổi.

## 4. Gọi Backend (ORM Service)
```javascript
// Search Read
const data = await this.orm.searchRead(model, domain, fields);

// Call Method (Hàm trong Python)
const result = await this.orm.call(model, "action_confirm", [id]);

// Create
const newId = await this.orm.create(model, [{ name: "Mới" }]);
```
