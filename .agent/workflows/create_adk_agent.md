---
description: Tạo Odoo module với Google ADK Agent
---

# Workflow: Tạo Google ADK Agent Module cho Odoo

Workflow này hướng dẫn tạo một Odoo module tích hợp Google ADK Agent, với cấu trúc tối ưu cho Cython compilation.

## 📋 Prerequisites

- [ ] Google ADK đã được cài đặt: `pip install google-adk`
- [ ] Đã đọc `custom_addons/.agent/docs/google_adk_reference.md`
- [ ] Hiểu rõ business logic cần implement

## 🎯 Mục tiêu

Tạo module với cấu trúc:
- **Business logic** tách riêng (có thể compile với Cython)
- **Agent wrapper** đơn giản (không compile)
- **Tools** rõ ràng, focused
- **Integration** với Odoo ORM

## 📝 Steps

### 1. Tạo cấu trúc module

```bash
cd custom_addons
mkdir -p trcf_my_agent/{models,controllers,security,views,data}
touch trcf_my_agent/__init__.py
touch trcf_my_agent/__manifest__.py
```

### 2. Tạo `__manifest__.py`

```python
{
    'name': 'TRCF My Agent',
    'version': '1.0',
    'summary': 'AI Agent sử dụng Google ADK',
    'description': """
        Module tích hợp Google ADK Agent vào Odoo.
        Hỗ trợ [mô tả tính năng].
    """,
    'author': 'Tuấn Rang Cà Phê',
    'website': 'https://coffeetree.vn',
    'category': 'AI',
    'depends': ['base', 'mail'],  # Thêm dependencies cần thiết
    'external_dependencies': {
        'python': ['google-adk'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/agent_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
```

### 3. Tạo Business Logic (CÓ THỂ COMPILE)

File: `models/business_logic.py`

```python
# -*- coding: utf-8 -*-
"""
Business Logic - File này CÓ THỂ được compile với Cython
Chứa tất cả logic nghiệp vụ, data processing, algorithms
"""

def get_odoo_data_internal(env, model_name, domain, fields):
    """
    Lấy dữ liệu từ Odoo ORM.
    
    Args:
        env: Odoo environment
        model_name: Tên model (vd: 'sale.order')
        domain: Search domain
        fields: List of fields to read
        
    Returns:
        dict: Processed data
    """
    records = env[model_name].search(domain)
    data = records.read(fields)
    return process_data(data)  # Logic xử lý

def process_data(raw_data):
    """Xử lý và transform data - Logic phức tạp có thể compile"""
    # Business logic ở đây
    processed = []
    for item in raw_data:
        # Transform logic
        processed.append({
            'key': item.get('field'),
            'value': calculate_something(item)
        })
    return processed

def calculate_something(item):
    """Tính toán phức tạp - Nên compile để bảo vệ IP"""
    # Proprietary algorithm
    result = item.get('amount', 0) * 1.1  # Example
    return result

def format_output(data, format_type='text'):
    """Format output cho agent - Logic có thể compile"""
    if format_type == 'text':
        lines = []
        for item in data:
            lines.append(f"{item['key']}: {item['value']}")
        return '\n'.join(lines)
    elif format_type == 'json':
        import json
        return json.dumps(data, ensure_ascii=False, indent=2)
    return str(data)

def validate_input(user_input):
    """Validate và sanitize input - Nên compile"""
    # Validation logic
    cleaned = user_input.strip()
    # More validation...
    return cleaned
```

### 4. Tạo Agent Wrapper (KHÔNG COMPILE)

File: `models/agent_wrapper.py`

```python
# -*- coding: utf-8 -*-
"""
Agent Wrapper - File này KHÔNG NÊN compile
Chỉ chứa agent definition và tool wrappers đơn giản
"""

from google.adk.agents import Agent
from google.adk.tools import google_search
from odoo import api, models, fields
from .business_logic import (
    get_odoo_data_internal,
    format_output,
    validate_input
)

class TrcfAgentWrapper(models.Model):
    _name = 'trcf.agent.wrapper'
    _description = 'ADK Agent Wrapper'
    
    name = fields.Char('Agent Name', required=True)
    model_name = fields.Char('AI Model', default='gemini-2.5-flash')
    
    def _create_tools(self):
        """Tạo tools cho agent - Wrappers đơn giản"""
        env = self.env
        
        def get_sales_data(query: str) -> str:
            """
            Lấy dữ liệu bán hàng từ Odoo.
            Sử dụng tool này để truy vấn thông tin đơn hàng, doanh số.
            """
            # Validate input (gọi compiled function)
            clean_query = validate_input(query)
            
            # Parse query to domain (simple logic, không cần compile)
            domain = [('state', '=', 'sale')]
            
            # Gọi business logic (đã compile)
            data = get_odoo_data_internal(
                env, 
                'sale.order',
                domain,
                ['name', 'amount_total', 'date_order']
            )
            
            # Format output (gọi compiled function)
            return format_output(data, 'text')
        
        def get_inventory_status(product_name: str) -> str:
            """
            Kiểm tra tồn kho của sản phẩm.
            """
            clean_name = validate_input(product_name)
            domain = [('name', 'ilike', clean_name)]
            
            data = get_odoo_data_internal(
                env,
                'product.product',
                domain,
                ['name', 'qty_available', 'virtual_available']
            )
            
            return format_output(data, 'text')
        
        return [get_sales_data, get_inventory_status, google_search]
    
    def create_agent(self):
        """Tạo ADK Agent instance"""
        tools = self._create_tools()
        
        agent = Agent(
            name=self.name or "odoo_assistant",
            model=self.model_name,
            tools=tools,
            instruction="""
            Bạn là trợ lý kinh doanh thông minh cho hệ thống Odoo.
            
            NHIỆM VỤ:
            1. Phân tích dữ liệu bán hàng và tồn kho từ Odoo
            2. Tìm kiếm thông tin bổ sung từ Google khi cần
            3. Đưa ra insights và recommendations
            
            QUY TRÌNH:
            - Bước 1: Hiểu rõ câu hỏi của user
            - Bước 2: Sử dụng tools phù hợp để lấy dữ liệu
            - Bước 3: Phân tích và tổng hợp
            - Bước 4: Trả lời rõ ràng, có số liệu cụ thể
            
            LƯU Ý:
            - Luôn cite nguồn dữ liệu
            - Đưa ra con số cụ thể
            - Giải thích reasoning
            """
        )
        
        return agent
    
    def query(self, user_message):
        """Execute agent query"""
        agent = self.create_agent()
        response = agent.run(user_message)
        return response
```

### 5. Tạo Controller (HTTP Endpoint)

File: `controllers/agent_controller.py`

```python
# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class AgentController(http.Controller):
    
    @http.route('/agent/query', type='json', auth='user', methods=['POST'])
    def agent_query(self, message):
        """
        API endpoint để query agent
        
        POST /agent/query
        {
            "message": "Doanh số tháng này như thế nào?"
        }
        """
        try:
            agent_wrapper = request.env['trcf.agent.wrapper'].search([], limit=1)
            if not agent_wrapper:
                # Tạo default agent
                agent_wrapper = request.env['trcf.agent.wrapper'].create({
                    'name': 'default_assistant'
                })
            
            response = agent_wrapper.query(message)
            
            return {
                'success': True,
                'response': response
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

### 6. Tạo `__init__.py` files

File: `__init__.py`
```python
from . import models
from . import controllers
```

File: `models/__init__.py`
```python
from . import business_logic  # Import trước
from . import agent_wrapper
```

File: `controllers/__init__.py`
```python
from . import agent_controller
```

### 7. Tạo Security

File: `security/ir.model.access.csv`
```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_trcf_agent_wrapper_user,trcf.agent.wrapper.user,model_trcf_agent_wrapper,base.group_user,1,1,1,1
```

### 8. Install và Test

```bash
# Restart Odoo
# Vào Apps > Update Apps List
# Tìm "TRCF My Agent" > Install

# Test via Python
agent = env['trcf.agent.wrapper'].create({'name': 'test_agent'})
result = agent.query("Doanh số hôm nay như thế nào?")
print(result)
```

## 🔐 Cython Compilation Strategy

### **Files cần compile:**

1. **Business Logic** - Data processing
```bash
cythonize -i models/business_logic.py
```

2. **Prompt Config** - Agent instructions
```bash
cythonize -i models/prompt_config.py
```

3. **Tool Logic** - Tool algorithms & rules ⭐
```bash
cythonize -i models/tool_logic.py
```

### **Files KHÔNG compile:**
- `__init__.py`, `__manifest__.py`
- `models/agent_wrapper.py` (Agent initialization)
- `controllers/agent_controller.py` (HTTP routing)

### **Bảo vệ Prompts:**

Để che giấu logic prompt, tạo file riêng:

**`models/prompt_config.py`** (SẼ COMPILE):
```python
def get_agent_instruction():
    """Prompt sẽ được compile để bảo vệ"""
    return """
    Bạn là trợ lý kinh doanh...
    [Business logic, quy trình, rules...]
    """
```

**Update `agent_wrapper.py`**:
```python
from .prompt_config import get_agent_instruction

def create_agent(self):
    instruction = get_agent_instruction()  # Từ compiled file
    agent = Agent(..., instruction=instruction)
```

**Chi tiết:** Xem `docs/protect_agent_prompts.md`

## ✅ Checklist

- [ ] Module structure đã tạo
- [ ] Business logic tách riêng trong `business_logic.py`
- [ ] Prompts tách riêng trong `prompt_config.py` (để compile)
- [ ] Agent wrapper đơn giản trong `agent_wrapper.py`
- [ ] Tools có docstring rõ ràng
- [ ] Controller có error handling
- [ ] Security access rights đã set
- [ ] Module install thành công
- [ ] Test agent query hoạt động
- [ ] (Optional) Compile business logic + prompts với Cython

## 📚 Tham khảo

- Google ADK Reference: `docs/google_adk_reference.md`
- Cython Guide: `docs/cython_compilation.md`
- **Protect Prompts**: `docs/protect_agent_prompts.md` ⭐
- **Compile Tools**: `docs/compile_tool_logic.md` ⭐
- Example: `trcf_ai_business_assistant`
