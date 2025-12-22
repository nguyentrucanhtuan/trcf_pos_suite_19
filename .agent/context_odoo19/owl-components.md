# Odoo 19 OWL Components

> **Source**: https://www.odoo.com/documentation/19.0/vi/developer/reference/frontend/owl_components.html
>
> **Last Updated**: 2025-12-22

---

## 1. OWL Basics

Odoo 19 sử dụng OWL 2 (Odoo Web Library) cho frontend components.

### Import cơ bản
```javascript
/** @odoo-module **/
import { Component, useState, onWillStart, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
```

---

## 2. Component Structure

### Component cơ bản
```javascript
/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class TrcfMyComponent extends Component {
    static template = "trcf_my_module.TrcfMyComponent";
    static props = {
        title: { type: String, optional: true },
        recordId: { type: Number, optional: true },
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({
            items: [],
            loading: true,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        try {
            this.state.items = await this.orm.searchRead(
                "trcf.my.model",
                [],
                ["name", "amount"]
            );
        } finally {
            this.state.loading = false;
        }
    }

    onItemClick(item) {
        this.notification.add(`Selected: ${item.name}`, { type: "info" });
    }
}

// Register component
registry.category("actions").add("trcf_my_component", TrcfMyComponent);
```

### Template XML
```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="trcf_my_module.TrcfMyComponent">
        <div class="o_trcf_component p-3">
            <h2 t-esc="props.title or 'My Component'"/>
            
            <t t-if="state.loading">
                <p>Loading...</p>
            </t>
            <t t-else="">
                <ul class="list-group">
                    <li t-foreach="state.items" t-as="item" t-key="item.id"
                        class="list-group-item d-flex justify-content-between"
                        t-on-click="() => this.onItemClick(item)">
                        <span t-esc="item.name"/>
                        <span class="badge bg-primary" t-esc="item.amount"/>
                    </li>
                </ul>
            </t>
        </div>
    </t>
</templates>
```

---

## 3. Lifecycle Hooks

```javascript
setup() {
    // Component setup - ALWAYS first
    this.state = useState({});
    
    onWillStart(async () => {
        // Before first render (async allowed)
        await this.fetchData();
    });
    
    onMounted(() => {
        // After DOM mounted
        console.log("Component mounted");
    });
    
    onWillUpdateProps(async (nextProps) => {
        // Before props update
    });
    
    onPatched(() => {
        // After re-render
    });
    
    onWillUnmount(() => {
        // Before destroy
    });
}
```

---

## 4. Services

### Thường dùng
```javascript
setup() {
    // ORM Service - Database operations
    this.orm = useService("orm");
    
    // RPC Service - Custom endpoints
    this.rpc = useService("rpc");
    
    // Notification
    this.notification = useService("notification");
    
    // Action Service
    this.action = useService("action");
    
    // Dialog Service
    this.dialog = useService("dialog");
    
    // User Service
    this.user = useService("user");
}
```

### ORM Service
```javascript
// Search Read
const records = await this.orm.searchRead(
    "trcf.my.model",
    [["state", "=", "done"]],  // domain
    ["name", "amount"],         // fields
    { limit: 10, order: "date desc" }
);

// Read
const data = await this.orm.read("trcf.my.model", [1, 2, 3], ["name"]);

// Create
const newId = await this.orm.create("trcf.my.model", { name: "New" });

// Write
await this.orm.write("trcf.my.model", [recordId], { name: "Updated" });

// Unlink
await this.orm.unlink("trcf.my.model", [recordId]);

// Call method
const result = await this.orm.call(
    "trcf.my.model",
    "custom_method",
    [recordId],
    { arg1: "value" }
);
```

### RPC Service
```javascript
const result = await this.rpc("/my_module/api/endpoint", {
    param1: "value",
    param2: 123,
});
```

### Notification
```javascript
this.notification.add("Message", { type: "info" });
this.notification.add("Success!", { type: "success" });
this.notification.add("Warning!", { type: "warning" });
this.notification.add("Error!", { type: "danger" });
```

### Action Service
```javascript
// Open form
this.action.doAction({
    type: "ir.actions.act_window",
    res_model: "trcf.my.model",
    res_id: recordId,
    views: [[false, "form"]],
    target: "current",
});

// Open new form
this.action.doAction({
    type: "ir.actions.act_window",
    res_model: "trcf.my.model",
    views: [[false, "form"]],
    target: "new",
    context: { default_name: "New Record" },
});
```

---

## 5. Props Validation

```javascript
static props = {
    // Required
    recordId: { type: Number },
    
    // Optional with default
    title: { type: String, optional: true },
    
    // Multiple types
    value: { type: [String, Number] },
    
    // Array
    items: { type: Array },
    
    // Object
    config: { type: Object },
    
    // Function
    onSelect: { type: Function, optional: true },
    
    // Any
    data: true,
};
```

---

## 6. Assets Registration

### `__manifest__.py`
```python
'assets': {
    'web.assets_backend': [
        'trcf_my_module/static/src/js/*.js',
        'trcf_my_module/static/src/xml/*.xml',
        'trcf_my_module/static/src/css/*.css',
    ],
    'point_of_sale._assets_pos': [
        'trcf_my_module/static/src/pos/**/*',
    ],
},
```

---

## 7. Patching Existing Components

```javascript
/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

patch(FormController.prototype, {
    setup() {
        super.setup();
        // Custom setup
        console.log("Patched FormController");
    },
    
    async save() {
        // Before save
        console.log("Before save");
        const result = await super.save();
        // After save
        console.log("After save");
        return result;
    },
    
    // New method
    customMethod() {
        return "Custom";
    },
});
```

---

## 8. Client Action Component

### Register as Action
```javascript
import { registry } from "@web/core/registry";

export class TrcfDashboard extends Component {
    static template = "trcf_my_module.Dashboard";
}

registry.category("actions").add("trcf_dashboard", TrcfDashboard);
```

### Call from XML
```xml
<record id="trcf_dashboard_action" model="ir.actions.client">
    <field name="name">Dashboard</field>
    <field name="tag">trcf_dashboard</field>
</record>

<menuitem id="trcf_dashboard_menu" name="Dashboard"
          action="trcf_dashboard_action"/>
```

---

## 9. Common Patterns

### Modal/Dialog
```javascript
import { Dialog } from "@web/core/dialog/dialog";

setup() {
    this.dialog = useService("dialog");
}

openConfirmDialog() {
    this.dialog.add(Dialog, {
        title: "Confirm",
        body: "Are you sure?",
        buttons: [
            { text: "Yes", click: () => this.onConfirm(), close: true },
            { text: "No", close: true },
        ],
    });
}
```

### Reactive State
```javascript
import { useState, useRef } from "@odoo/owl";

setup() {
    this.state = useState({
        count: 0,
        items: [],
    });
    
    this.inputRef = useRef("input");
}

increment() {
    this.state.count++;  // Auto re-render
}
```

---

## 📌 Template Nhanh

### Component File: `static/src/js/my_component.js`
```javascript
/** @odoo-module **/
import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class TrcfMyComponent extends Component {
    static template = "trcf_my_module.TrcfMyComponent";
    static props = { title: { type: String, optional: true } };

    setup() {
        this.orm = useService("orm");
        this.state = useState({ items: [], loading: true });
        onWillStart(() => this.loadData());
    }

    async loadData() {
        this.state.items = await this.orm.searchRead("trcf.my.model", [], ["name"]);
        this.state.loading = false;
    }
}

registry.category("actions").add("trcf_my_component", TrcfMyComponent);
```

### Template File: `static/src/xml/my_component.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<templates xml:space="preserve">
    <t t-name="trcf_my_module.TrcfMyComponent">
        <div class="p-3">
            <h2 t-esc="props.title or 'Component'"/>
            <t t-if="state.loading"><p>Loading...</p></t>
            <t t-else="">
                <ul t-foreach="state.items" t-as="item" t-key="item.id">
                    <li t-esc="item.name"/>
                </ul>
            </t>
        </div>
    </t>
</templates>
```

---

## 🔗 Tham khảo

- **OWL**: https://www.odoo.com/documentation/19.0/vi/developer/reference/frontend/owl_components.html
- **JavaScript Reference**: https://www.odoo.com/documentation/19.0/vi/developer/reference/frontend/javascript_reference.html
