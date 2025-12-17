---
description: Quy tắc đặt tên và conventions cho Odoo modules
---

# Naming Conventions & Code Standards

Tài liệu này mô tả các quy tắc đặt tên và coding standards được sử dụng trong dự án Odoo.

## 🏷️ Module Naming

### Module Directory
```
trcf_<feature_name>
```

**Examples:**
- `trcf_payment_momo` - MoMo payment integration
- `trcf_kitchen_screen` - Kitchen display screen
- `trcf_zkteco_attendance_sync` - ZKTeco attendance sync
- `trcf_ai_business_assistant` - AI business assistant

**Rules:**
- ✅ Lowercase only
- ✅ Underscores for word separation
- ✅ Prefix `trcf_` (Tuấn Rang Cà Phê)
- ✅ Descriptive, clear purpose
- ❌ No hyphens, no spaces, no camelCase

## 📦 Model Naming

### Model Technical Names
```python
_name = 'trcf.<feature>.<entity>'
```

**Examples:**
```python
class TrcfKitchenScreen(models.Model):
    _name = 'trcf.kitchenscreen'
    _description = 'Kitchen Screen for Tuấn Rang Cà Phê'

class TrcfMomoTransaction(models.Model):
    _name = 'trcf.momo.transaction'
    _description = 'MoMo Payment Transaction'

class TrcfWorkShift(models.Model):
    _name = 'trcf.work.shift'
    _description = 'Work Shift'
```

### Model Class Names
```python
class Trcf<Feature><Entity>(models.Model):
```

**Rules:**
- ✅ PascalCase
- ✅ Prefix `Trcf`
- ✅ Descriptive entity name
- ✅ Inherit from `models.Model` or `models.TransientModel`

**Examples:**
- `TrcfKitchenScreen`
- `TrcfPosPaymentMethod`
- `TrcfHrAttendance`
- `TrcfInventoryCheck`

## 📄 File Naming

### Python Files
```
trcf_<entity_name>.py
```

**Examples:**
- `models/trcf_kitchen_screen.py`
- `models/trcf_pos_payment_method.py`
- `controllers/trcf_dashboard_controller.py`
- `wizard/trcf_generate_week_tasks_wizard.py`

### XML Files
```
trcf_<entity_name>_<type>.xml
```

**Examples:**
- `views/trcf_kitchen_screen_views.xml`
- `views/trcf_shift_registration_templates.xml`
- `data/trcf_shift_task_cron.xml`
- `security/ir.model.access.csv`

### JavaScript/CSS Files
```
trcf_<component_name>.js
trcf_<component_name>.css
```

**Examples:**
- `static/src/js/trcf_kitchen_dashboard.js`
- `static/src/css/trcf_kitchen_dashboard.css`
- `static/src/xml/trcf_kitchen_dashboard.xml`

## 🔤 Field Naming

### Database Fields
```python
field_name = fields.Type('Label', ...)
```

**Rules:**
- ✅ Lowercase with underscores (snake_case)
- ✅ Descriptive, clear purpose
- ✅ Avoid abbreviations unless very common

**Examples:**
```python
screen_name = fields.Char('Tên màn hình', required=True)
pos_config_id = fields.Many2one('pos.config', string='POS áp dụng')
momo_qr_code = fields.Binary('Mã QR MoMo')
is_active = fields.Boolean('Đang hoạt động', default=True)
```

### Computed Fields
```python
_compute_<field_name>
```

**Example:**
```python
custom_total = fields.Float(compute='_compute_custom_total')

@api.depends('order_line')
def _compute_custom_total(self):
    for record in self:
        record.custom_total = sum(record.order_line.mapped('price'))
```

## 🎯 Function/Method Naming

### Public Methods
```python
def action_<verb>_<object>(self):
    """Action methods triggered by buttons"""
    pass

def get_<data>(self):
    """Getter methods"""
    pass

def create_<entity>(self):
    """Creation methods"""
    pass
```

**Examples:**
```python
def action_confirm_order(self):
    """Confirm the order"""
    pass

def get_sales_data(self):
    """Get sales data from database"""
    pass

def create_momo_payment_rpc(self, order_id, amount):
    """Create MoMo payment via RPC"""
    pass
```

### Private/Internal Methods
```python
def _internal_method(self):
    """Internal helper method"""
    pass
```

**Examples:**
```python
def _compute_custom_total(self):
    pass

def _get_payment_terminal_selection(self):
    pass

def _load_pos_data_fields(self, config):
    pass
```

## 🌐 Controller Routes

### Route Naming
```python
@http.route('/module_name/action', type='json', auth='user')
```

**Examples:**
```python
@http.route('/momo/ipn', type='json', auth='public')
def momo_ipn_webhook(self):
    pass

@http.route('/agent/query', type='json', auth='user')
def agent_query(self, message):
    pass

@http.route('/kitchen/dashboard', type='http', auth='user')
def kitchen_dashboard(self):
    pass
```

## 📋 XML IDs

### Format
```xml
<record id="prefix_entity_type" model="...">
```

**Examples:**
```xml
<!-- Views -->
<record id="trcf_kitchen_screen_view_form" model="ir.ui.view">
<record id="trcf_momo_transaction_view_tree" model="ir.ui.view">

<!-- Actions -->
<record id="trcf_kitchen_screen_action" model="ir.actions.act_window">

<!-- Menu Items -->
<menuitem id="trcf_kitchen_screen_menu" name="Kitchen Screen"/>

<!-- Security -->
<record id="access_trcf_kitchen_screen_user" model="ir.model.access">
```

## 🎨 OWL Component Naming

### Component Class
```javascript
class TrcfComponentName extends Component {
    static template = 'trcf_module.ComponentName';
}
```

**Example:**
```javascript
class TrcfKitchenDashboard extends Component {
    static template = 'trcf_kitchen_screen.KitchenDashboard';
}
```

### Template XML
```xml
<templates id="template" xml:space="preserve">
    <t t-name="trcf_module.ComponentName">
        ...
    </t>
</templates>
```

## 📝 Documentation Standards

### Docstrings
```python
def method_name(self, param1, param2):
    """
    Brief description of what this method does.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ExceptionType: When this exception is raised
    """
    pass
```

### Comments
```python
# Single line comment for simple explanations

# Multi-line comment for complex logic:
# - Point 1
# - Point 2
# - Point 3
```

## 🏗️ Module Structure Standard

```
trcf_module_name/
├── __init__.py                      # Module init
├── __manifest__.py                  # Module manifest
├── models/
│   ├── __init__.py
│   ├── trcf_main_model.py          # Main business model
│   ├── business_logic.py           # Compilable logic (optional)
│   └── ...
├── controllers/
│   ├── __init__.py
│   └── trcf_main_controller.py
├── views/
│   ├── trcf_model_views.xml        # Form, tree, search views
│   └── trcf_templates.xml          # QWeb templates
├── static/
│   ├── src/
│   │   ├── js/
│   │   │   └── trcf_component.js
│   │   ├── css/
│   │   │   └── trcf_component.css
│   │   └── xml/
│   │       └── trcf_component.xml
│   └── description/
│       └── icon.png
├── security/
│   └── ir.model.access.csv
├── data/
│   └── trcf_default_data.xml
├── wizard/                          # Optional
│   ├── __init__.py
│   └── trcf_wizard.py
└── README.md                        # Optional
```

## ✅ Manifest Standards

```python
{
    'name': 'TRCF Module Name',
    'version': '1.0',
    'category': 'Category',
    'summary': 'Brief summary',
    'description': """
        Detailed description
        ====================
        
        Features:
        ---------
        * Feature 1
        * Feature 2
    """,
    'author': 'Tuấn Rang Cà Phê',
    'website': 'https://coffeetree.vn',
    'depends': ['base', 'other_module'],
    'external_dependencies': {
        'python': ['library_name'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/trcf_views.xml',
        'data/trcf_data.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'module/static/src/js/file.js',
            'module/static/src/xml/file.xml',
        ],
    },
    'installable': True,
    'application': True,  # or False
    'license': 'LGPL-3',
}
```

## 🔐 Security Standards

### Access Rights CSV
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_trcf_model_user,trcf.model.user,model_trcf_model,base.group_user,1,1,1,1
access_trcf_model_manager,trcf.model.manager,model_trcf_model,base.group_system,1,1,1,1
```

## 📚 Import Standards

### Python Imports Order
```python
# 1. Standard library
import logging
import json
from datetime import datetime

# 2. Odoo imports
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

# 3. Local imports
from .business_logic import calculate_total
```

## 🎯 Best Practices Summary

1. **Consistency**: Follow conventions across all modules
2. **Clarity**: Names should be self-documenting
3. **Prefix**: Always use `trcf_` prefix
4. **Documentation**: Add docstrings and comments
5. **Structure**: Follow standard module structure
6. **Security**: Define proper access rights
7. **Testing**: Test before committing

## 📖 References

- Odoo Guidelines: https://www.odoo.com/documentation/19.0/developer/reference/backend/guidelines.html
- Python PEP 8: https://peps.python.org/pep-0008/
- Project modules: `custom_addons/trcf_*`
