---
description: Chiến lược compile Odoo modules với Cython
---

# Cython Compilation Strategy

Hướng dẫn compile Odoo modules với Cython để bảo vệ intellectual property và tăng performance.

## 🎯 Mục tiêu

1. **Bảo vệ IP**: Che giấu business logic, algorithms proprietary
2. **Tăng performance**: Tăng tốc code Python (đặc biệt loops, calculations)
3. **Deployment**: Deploy compiled code (.so files) thay vì source code

## ⚖️ Quyết định: Compile hay không?

### ✅ NÊN COMPILE

**Business Logic:**
```python
# models/business_logic.py
def calculate_profit_margin(cost, price, tax_rate):
    """Proprietary algorithm - NÊN compile"""
    # Complex calculation logic
    margin = (price - cost) / price
    adjusted = margin * (1 - tax_rate)
    return adjusted * secret_multiplier()  # Bảo vệ công thức

def process_large_dataset(data):
    """Heavy computation - NÊN compile để tăng tốc"""
    result = []
    for item in data:  # Loop lớn -> Cython sẽ nhanh hơn
        processed = complex_transform(item)
        result.append(processed)
    return result
```

**Data Processing:**
```python
# models/data_processor.py
def transform_sales_data(records):
    """Data transformation - NÊN compile"""
    # String operations, loops, calculations
    pass

def validate_and_clean(input_data):
    """Validation logic - NÊN compile"""
    # Complex validation rules
    pass
```

**Helper Utilities:**
```python
# models/utils.py
def custom_hash_algorithm(data):
    """Custom algorithm - NÊN compile"""
    pass

def proprietary_scoring(metrics):
    """Scoring algorithm - NÊN compile"""
    pass
```

### ❌ KHÔNG NÊN COMPILE

**Odoo Model Definitions:**
```python
# models/my_model.py - KHÔNG COMPILE
from odoo import models, fields, api

class MyModel(models.Model):
    _name = 'my.model'
    
    name = fields.Char('Name')
    
    @api.depends('field1')
    def _compute_something(self):
        # Odoo cần reflection, decorators
        pass
```

**Lý do:**
- Odoo dùng metaclasses, decorators
- Dynamic model registration
- Reflection và introspection
- Cython sẽ break những features này

**Controllers:**
```python
# controllers/main.py - KHÔNG COMPILE
from odoo import http

class MyController(http.Controller):
    @http.route('/my/route', auth='user')
    def my_route(self):
        # HTTP routing cần decorators
        pass
```

**Agent Wrappers:**
```python
# models/agent_wrapper.py - KHÔNG COMPILE
from google.adk.agents import Agent  # External library
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

agent = Agent(...)  # External library, không nên compile
```

**Init Files:**
```python
# __init__.py, __manifest__.py - KHÔNG BAO GIỜ COMPILE
```

## 🏗️ Recommended Architecture

### Cấu trúc Module với Cython

```
trcf_my_module/
├── __init__.py                    # ❌ Không compile
├── __manifest__.py                # ❌ Không compile
├── models/
│   ├── __init__.py               # ❌ Không compile
│   ├── my_model.py               # ❌ Không compile (Odoo model)
│   ├── business_logic.py         # ✅ COMPILE
│   ├── data_processor.py         # ✅ COMPILE
│   └── utils.py                  # ✅ COMPILE
├── controllers/
│   ├── __init__.py               # ❌ Không compile
│   └── main_controller.py        # ⚠️ Tách logic ra, chỉ compile logic
└── ...
```

### Pattern: Tách Logic khỏi Odoo Model

**TRƯỚC (Tất cả trong model):**
```python
# models/sale_order.py - Khó compile
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.depends('order_line')
    def _compute_custom_total(self):
        for order in self:
            # Complex calculation logic ở đây
            total = 0
            for line in order.order_line:
                total += line.price * secret_multiplier(line)
            order.custom_total = total
```

**SAU (Tách logic):**
```python
# models/business_logic.py - ✅ CÓ THỂ COMPILE
def calculate_custom_total(order_lines):
    """Business logic - Có thể compile"""
    total = 0
    for line in order_lines:
        total += line['price'] * secret_multiplier(line)
    return total

def secret_multiplier(line):
    """Proprietary algorithm - Compile để bảo vệ"""
    # Secret formula
    return 1.15

# models/sale_order.py - ❌ Không compile
from odoo import models, fields, api
from .business_logic import calculate_custom_total

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    @api.depends('order_line')
    def _compute_custom_total(self):
        for order in self:
            # Gọi compiled function
            line_data = order.order_line.read(['price', 'quantity'])
            order.custom_total = calculate_custom_total(line_data)
```

## 🔧 Compilation Process

### Setup

```bash
# Install Cython
pip install cython

# Install build tools
# macOS:
xcode-select --install

# Ubuntu/Debian:
sudo apt-get install build-essential python3-dev
```

### Method 1: Manual Compilation (Từng file)

```bash
cd custom_addons/trcf_my_module

# Compile một file
cythonize -i models/business_logic.py

# Kết quả:
# - business_logic.c (C source)
# - business_logic.cpython-39-darwin.so (compiled binary)
# - business_logic.py (giữ nguyên hoặc xóa)
```

### Method 2: Setup Script (Recommended)

Tạo file `setup.py` trong module:

```python
# setup.py
from setuptools import setup
from Cython.Build import cythonize
import os

# List files cần compile
files_to_compile = [
    "models/business_logic.py",
    "models/data_processor.py",
    "models/utils.py",
]

setup(
    name="trcf_my_module",
    ext_modules=cythonize(
        files_to_compile,
        compiler_directives={
            'language_level': "3",
            'embedsignature': True,
        }
    ),
)
```

Compile:
```bash
python setup.py build_ext --inplace
```

### Method 3: Automated Script

Tạo script: `custom_addons/.agent/scripts/compile_module.py`

```python
#!/usr/bin/env python3
import os
import sys
import subprocess

def compile_module(module_path):
    """Compile business logic files trong module"""
    
    files_to_compile = [
        'models/business_logic.py',
        'models/data_processor.py',
        'models/utils.py',
    ]
    
    for file_path in files_to_compile:
        full_path = os.path.join(module_path, file_path)
        if os.path.exists(full_path):
            print(f"Compiling {full_path}...")
            subprocess.run(['cythonize', '-i', full_path])
        else:
            print(f"Skipping {full_path} (not found)")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python compile_module.py <module_path>")
        sys.exit(1)
    
    module_path = sys.argv[1]
    compile_module(module_path)
```

Sử dụng:
```bash
python custom_addons/.agent/scripts/compile_module.py custom_addons/trcf_my_module
```

## 📦 Deployment

### Option 1: Deploy với Source + Compiled

```
trcf_my_module/
├── models/
│   ├── business_logic.py           # Source (optional, có thể xóa)
│   ├── business_logic.so           # Compiled ✅
│   ├── my_model.py                 # Source ✅
│   └── ...
```

Python sẽ ưu tiên import `.so` nếu có.

### Option 2: Deploy chỉ Compiled (Bảo mật cao nhất)

```bash
# Xóa source files đã compile
rm models/business_logic.py
rm models/data_processor.py

# Giữ lại .so files
# Giữ lại các files không compile
```

**Lưu ý:** Backup source code ở nơi khác!

## ⚠️ Caveats & Limitations

### 1. Platform-Specific
`.so` files là platform-specific:
- macOS: `.cpython-39-darwin.so`
- Linux: `.cpython-39-x86_64-linux-gnu.so`
- Windows: `.pyd`

**Giải pháp:** Compile trên target platform hoặc dùng Docker.

### 2. Python Version
Compiled files gắn với Python version (3.9, 3.10, etc.)

**Giải pháp:** Compile với đúng Python version của production.

### 3. Debugging
Compiled code khó debug hơn.

**Giải pháp:** 
- Test kỹ trước khi compile
- Giữ source code cho development
- Chỉ compile cho production

### 4. Import Issues
Nếu import bị lỗi sau khi compile:

```python
# Đảm bảo __init__.py import đúng
from . import business_logic  # Sẽ tự động load .so nếu có
```

## ✅ Best Practices

1. **Version Control:**
   - Commit source `.py` files
   - Add `.so`, `.c` vào `.gitignore`
   - Compile khi deploy

2. **Testing:**
   - Test thoroughly trước khi compile
   - Test cả source và compiled versions

3. **Documentation:**
   - Document files nào được compile
   - Document dependencies

4. **Gradual Adoption:**
   - Bắt đầu compile một vài files
   - Verify hoạt động ổn định
   - Mở rộng dần

## 📚 Tham khảo

- Cython Documentation: https://cython.readthedocs.io/
- Odoo + Cython: Best practices từ community
- Example: Module `trcf_ai_business_assistant`
