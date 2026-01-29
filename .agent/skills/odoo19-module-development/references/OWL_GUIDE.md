# Odoo 19 OWL Guide (Full Structure)

Hướng dẫn chi tiết cách viết OWL Component chuẩn ESM trong Odoo 19.

## 1. Cấu trúc Component File (`.js`)

```javascript
/** @odoo-module **/

import { Component, useState, useRef, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class TrcfDashboard extends Component {
    static template = "trcf_module.DashboardTemplate";
    static props = {
        title: { type: String, optional: true },
        records: { type: Array, optional: true },
    };
    
    setup() {
        // Services
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.user = useService("user");
        
        // Refs (DOM access)
        this.containerRef = useRef("container");
        
        // Reactive state
        this.state = useState({
            records: [],
            loading: true,
            searchQuery: "",
        });
        
        // Lifecycle hooks
        onWillStart(async () => {
            await this.loadData();
        });
        
        onMounted(() => {
            console.log("Component mounted, DOM ready");
            this.containerRef.el?.focus();
        });
    }

    async loadData() {
        this.state.loading = true;
        try {
            this.state.records = await this.orm.searchRead(
                "trcf.order",
                [],
                ["name", "amount", "state"]
            );
        } catch (error) {
            this.notification.add(_t("Lỗi khi tải dữ liệu"), { type: "danger" });
        }
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
    
    onSearchChange(ev) {
        this.state.searchQuery = ev.target.value;
    }
}

// Đăng ký làm Client Action
registry.category("actions").add("trcf_dashboard_action", TrcfDashboard);
```

## 2. Template File (`.xml`)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="trcf_module.DashboardTemplate">
        <div class="o_dashboard_container p-3" t-ref="container">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h3><t t-esc="props.title or 'Bảng điều khiển TRCF'"/></h3>
                <input 
                    type="text" 
                    class="form-control w-25"
                    placeholder="Tìm kiếm..."
                    t-on-input="onSearchChange"
                />
            </div>
            
            <!-- Loading state -->
            <div t-if="state.loading" class="text-center py-5">
                <i class="fa fa-spinner fa-spin fa-2x"/> 
                <p class="mt-2">Đang tải...</p>
            </div>
            
            <!-- Empty state -->
            <div t-elif="!state.records.length" class="text-center py-5 text-muted">
                <i class="fa fa-inbox fa-3x"/>
                <p class="mt-2">Không có dữ liệu</p>
            </div>
            
            <!-- Data display -->
            <div t-else="" class="row g-3">
                <t t-foreach="filteredRecords" t-as="record" t-key="record.id">
                    <div class="col-md-4">
                        <div 
                            class="card h-100 shadow-sm" 
                            role="button"
                            t-on-click="() => this.onItemClick(record.id)"
                        >
                            <div class="card-body">
                                <h5 class="card-title" t-esc="record.name"/>
                                <p class="card-text">
                                    Số tiền: <strong t-esc="record.amount"/>
                                </p>
                                <span 
                                    class="badge"
                                    t-att-class="{
                                        'bg-secondary': record.state === 'draft',
                                        'bg-primary': record.state === 'confirmed',
                                        'bg-success': record.state === 'done',
                                    }"
                                    t-esc="record.state"
                                />
                            </div>
                        </div>
                    </div>
                </t>
            </div>
        </div>
    </t>
</templates>
```

## 3. Lifecycle Hooks

```javascript
import { 
    onWillStart,      // Trước render lần đầu (async OK)
    onMounted,        // Sau khi mount vào DOM
    onWillUpdateProps,// Khi props thay đổi
    onWillPatch,      // Trước khi DOM update
    onPatched,        // Sau khi DOM update
    onWillUnmount,    // Trước khi unmount
    onWillDestroy,    // Trước khi destroy
} from "@odoo/owl";

setup() {
    onWillStart(async () => {
        // Load data, check permissions, etc.
        await this.loadInitialData();
    });
    
    onMounted(() => {
        // DOM manipulation, event listeners
        document.addEventListener("keydown", this.handleKeydown);
    });
    
    onWillUnmount(() => {
        // Cleanup
        document.removeEventListener("keydown", this.handleKeydown);
    });
}
```

## 4. Props và Events

### Định nghĩa Props
```javascript
static props = {
    // Required
    recordId: Number,
    
    // Optional với default
    title: { type: String, optional: true },
    
    // Array/Object
    records: { type: Array, optional: true },
    config: { type: Object, optional: true },
    
    // Callback function
    onSelect: { type: Function, optional: true },
    
    // Wildcard (accept any props)
    "*": true,
};
```

### Truyền Props từ XML
```xml
<MyComponent 
    recordId="123"
    title="'Danh sách'"
    records="state.items"
    onSelect.bind="handleSelect"
/>
```

### Custom Events
```javascript
// Parent component
class Parent extends Component {
    onChildEvent(data) {
        console.log("Received from child:", data);
    }
}

// In parent template
<ChildComponent onCustomEvent.bind="onChildEvent"/>

// Child component - trigger event
class ChildComponent extends Component {
    triggerEvent() {
        this.props.onCustomEvent({ id: 123, action: "click" });
    }
}
```

## 5. ORM Service Methods

```javascript
this.orm = useService("orm");

// Search Read (tối ưu nhất)
const records = await this.orm.searchRead(
    "trcf.order",                          // model
    [["state", "=", "confirmed"]],          // domain
    ["name", "amount", "partner_id"],       // fields
    { limit: 100, order: "date desc" }      // kwargs
);

// Read (by IDs)
const records = await this.orm.read("trcf.order", [1, 2, 3], ["name"]);

// Search (return IDs only)
const ids = await this.orm.search("trcf.order", [["state", "=", "draft"]]);

// Create
const newId = await this.orm.create("trcf.order", { name: "Đơn mới" });

// Write
await this.orm.write("trcf.order", [1, 2], { state: "confirmed" });

// Unlink
await this.orm.unlink("trcf.order", [1, 2]);

// Call Python method
const result = await this.orm.call(
    "trcf.order",           // model
    "action_confirm",       // method name
    [[1, 2, 3]],            // args (IDs)
    { force: true }         // kwargs
);

// Read Group
const groups = await this.orm.readGroup(
    "trcf.order",
    [["state", "!=", "cancel"]],
    ["amount:sum"],
    ["state"]
);
```

## 6. RPC (Non-ORM calls)

```javascript
import { rpc } from "@web/core/network/rpc";

// Call controller route
const result = await rpc("/trcf/api/calculate", {
    order_id: 123,
    include_tax: true,
});

// JSON-RPC to custom endpoint
const data = await rpc("/web/dataset/call_kw", {
    model: "trcf.order",
    method: "custom_action",
    args: [[1, 2, 3]],
    kwargs: {},
});
```

## 7. Notifications

```javascript
this.notification = useService("notification");

// Success
this.notification.add(_t("Đã lưu thành công!"), { type: "success" });

// Warning
this.notification.add(_t("Vui lòng kiểm tra lại"), { type: "warning" });

// Error
this.notification.add(_t("Có lỗi xảy ra"), { type: "danger" });

// With options
this.notification.add(_t("Thông báo"), {
    type: "info",
    sticky: true,     // Không tự đóng
    title: "Title",
    buttons: [
        {
            name: "Xem chi tiết",
            onClick: () => this.viewDetails(),
        },
    ],
});
```

## 8. Dialogs

```javascript
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

this.dialog = useService("dialog");

// Confirmation dialog
this.dialog.add(ConfirmationDialog, {
    title: _t("Xác nhận"),
    body: _t("Bạn có chắc chắn muốn xóa?"),
    confirm: async () => {
        await this.deleteRecord();
    },
    cancel: () => {},
});
```

## 9. Manifest Setup

```python
# __manifest__.py
{
    'assets': {
        'web.assets_backend': [
            'trcf_module/static/src/js/**/*.js',
            'trcf_module/static/src/xml/**/*.xml',
            'trcf_module/static/src/css/**/*.css',
        ],
        # Nếu cần cho POS
        'point_of_sale._assets_pos': [
            'trcf_module/static/src/pos/**/*',
        ],
    },
}
```

## 10. Common Patterns

### Computed Getters
```javascript
get filteredRecords() {
    if (!this.state.searchQuery) return this.state.records;
    const query = this.state.searchQuery.toLowerCase();
    return this.state.records.filter(r => 
        r.name.toLowerCase().includes(query)
    );
}
```

### Debounce
```javascript
import { debounce } from "@web/core/utils/timing";

setup() {
    this.debouncedSearch = debounce(this.doSearch.bind(this), 300);
}

onSearchInput(ev) {
    this.debouncedSearch(ev.target.value);
}
```

### Formatting
```javascript
import { formatMonetary } from "@web/views/fields/formatters";
import { formatDate, formatDateTime } from "@web/core/l10n/dates";

const formattedAmount = formatMonetary(1000000, { currencyId: 1 });
const formattedDate = formatDate(luxon.DateTime.now());
```
