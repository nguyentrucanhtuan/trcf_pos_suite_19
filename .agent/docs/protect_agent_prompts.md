# Bảo vệ Agent Prompts với Cython

Hướng dẫn compile và bảo vệ agent prompts/instructions để che giấu logic nghiệp vụ.

## 🎯 Vấn đề

Khi deploy ADK Agent, **instruction/prompt** chứa:
- Business logic và quy trình
- Proprietary knowledge
- Decision-making rules
- Competitive advantages

➡️ **Cần bảo vệ** để khách hàng không thấy được.

## 💡 Giải pháp: Tách Prompt ra file riêng + Compile

### **Architecture Pattern:**

```
models/
├── business_logic.py          # ✅ COMPILE - Data processing
├── prompt_config.py            # ✅ COMPILE - Agent prompts/instructions
└── agent_wrapper.py            # ❌ NO COMPILE - Agent initialization
```

## 📝 Implementation

### 1. Tạo file `prompt_config.py` (COMPILE)

```python
# -*- coding: utf-8 -*-
"""
Prompt Configuration - File này SẼ ĐƯỢC COMPILE
Chứa tất cả prompts, instructions, và business rules
"""

def get_agent_instruction():
    """
    Trả về instruction cho agent.
    Function này sẽ được compile để bảo vệ prompt logic.
    """
    instruction = """
    Bạn là chuyên gia R&D đồ uống cấp cao cho chuỗi cà phê.
    
    NHIỆM VỤ:
    1. Phân tích dữ liệu bán hàng để hiểu sở thích khách hàng
    2. Tìm kiếm xu hướng đồ uống mới từ thị trường
    3. Đề xuất công thức món mới dựa trên:
       - Dữ liệu bán chạy hiện tại
       - Trend thị trường
       - Quy tắc pha chế của quán
    
    QUY TRÌNH 3 BƯỚC:
    
    BƯỚC 1: PHÂN TÍCH HIỆN TẠI
    - Dùng tool `get_shop_best_sellers` để xem món bán chạy
    - Phân tích: Khách thích vị gì? (Ngọt/Đắng/Chua/Béo)
    - Xác định pattern: Thời tiết nào bán tốt?
    
    BƯỚC 2: TÌM KIẾM XU HƯỚNG
    - Dùng tool `google_search` để tìm trend mới
    - Keywords: "[hương vị bán chạy] + trends 2025"
    - Lọc: Chỉ lấy ideas phù hợp với thiết bị quán
    
    BƯỚC 3: SÁNG TẠO & KIỂM TRA
    - Kết hợp: Món bán chạy + Trend mới
    - Dùng tool `consult_mixing_rules` để verify:
      * Không vi phạm quy tắc pha chế
      * Tỷ lệ nguyên liệu hợp lý
      * Có thể thực hiện với thiết bị hiện tại
    
    ĐẦU RA:
    - Tên món (Tiếng Việt, hấp dẫn, dễ nhớ)
    - Lý do (Tại sao sẽ bán chạy? Cite data + trend)
    - Công thức sơ bộ (Nguyên liệu + Tỷ lệ)
    - Chi phí ước tính
    - Giá bán đề xuất
    
    QUY TẮC VÀNG:
    - Luôn cite nguồn dữ liệu (bán hàng/trend)
    - Không đề xuất món quá phức tạp (>5 nguyên liệu)
    - Ưu tiên nguyên liệu sẵn có
    - Margin tối thiểu: 60%
    """
    return instruction

def get_tool_instructions():
    """Hướng dẫn sử dụng tools - Cũng nên bảo vệ"""
    return {
        'get_shop_best_sellers': """
            Dùng khi cần biết món nào đang bán chạy.
            Output: Top 3-5 món + doanh số + mô tả vị.
        """,
        'google_search': """
            Dùng để tìm trend, công thức mới.
            Tips: Search bằng tiếng Anh để có kết quả tốt hơn.
        """,
        'consult_mixing_rules': """
            Kiểm tra công thức có hợp lệ không.
            Bắt buộc gọi trước khi finalize công thức.
        """
    }

def get_system_rules():
    """Business rules - Proprietary logic"""
    return {
        'min_margin': 0.6,  # 60% margin tối thiểu
        'max_ingredients': 5,
        'forbidden_combinations': [
            ('milk', 'citrus'),  # Sữa + cam/chanh = kết tủa
            ('coffee', 'yogurt'),  # Cà phê + sữa chua = vị lạ
        ],
        'seasonal_multiplier': {
            'summer': {'cold_drinks': 1.5, 'hot_drinks': 0.7},
            'winter': {'cold_drinks': 0.8, 'hot_drinks': 1.3},
        }
    }
```

### 2. Update `agent_wrapper.py` (KHÔNG COMPILE)

```python
# -*- coding: utf-8 -*-
from google.adk.agents import Agent
from google.adk.tools import google_search
from odoo import models, fields
from .business_logic import (
    get_shop_best_sellers_internal,
    consult_mixing_rules_internal
)
from .prompt_config import (  # Import từ file sẽ compile
    get_agent_instruction,
    get_tool_instructions,
    get_system_rules
)

class TrcfAgentWrapper(models.Model):
    _name = 'trcf.agent.wrapper'
    _description = 'ADK Agent Wrapper'
    
    name = fields.Char('Agent Name', required=True)
    
    def _create_tools(self):
        """Tool wrappers - Đơn giản, không cần compile"""
        env = self.env
        
        def get_shop_best_sellers() -> str:
            """Wrapper gọi compiled function"""
            data = get_shop_best_sellers_internal(env)
            return data
        
        def consult_mixing_rules(query: str) -> str:
            """Wrapper gọi compiled function"""
            rules = get_system_rules()  # Từ compiled file
            result = consult_mixing_rules_internal(query, rules)
            return result
        
        return [get_shop_best_sellers, consult_mixing_rules, google_search]
    
    def create_agent(self):
        """Tạo agent - Không compile file này"""
        tools = self._create_tools()
        
        # Lấy instruction từ compiled file
        instruction = get_agent_instruction()
        
        agent = Agent(
            name=self.name,
            model='gemini-2.5-flash',
            tools=tools,
            instruction=instruction  # Prompt đã được bảo vệ
        )
        
        return agent
```

### 3. Compile Strategy

```bash
cd custom_addons/trcf_my_agent

# Compile business logic
cythonize -i models/business_logic.py

# Compile prompt config (QUAN TRỌNG!)
cythonize -i models/prompt_config.py

# KHÔNG compile agent_wrapper.py
```

## 🔐 Kết quả

### **Trước khi deploy:**
```
models/
├── business_logic.py          # Source code
├── prompt_config.py            # Source code - CHỨA PROMPT
├── agent_wrapper.py            # Source code
```

### **Sau khi compile & deploy:**
```
models/
├── business_logic.so           # Compiled ✅
├── prompt_config.so            # Compiled ✅ - PROMPT ĐÃ BẢO VỆ
├── agent_wrapper.py            # Source (không chứa logic quan trọng)
```

**Xóa source files trước khi deploy:**
```bash
rm models/business_logic.py
rm models/prompt_config.py
# Giữ agent_wrapper.py
```

## ✅ Lợi ích

1. **Bảo vệ IP**: Khách hàng không thấy được prompt logic
2. **Che giấu quy trình**: Business rules được compile
3. **Bảo mật chiến lược**: Decision-making logic ẩn
4. **Dễ maintain**: Tách prompt ra file riêng, dễ update

## 🎯 Best Practices

### 1. **Tách rõ ràng:**
```python
# prompt_config.py - COMPILE
- Agent instructions
- System prompts
- Business rules
- Decision logic

# agent_wrapper.py - KHÔNG COMPILE
- Agent initialization
- Tool registration
- Simple wrappers
```

### 2. **Modular Prompts:**
```python
def get_agent_instruction():
    base = get_base_instruction()
    rules = get_business_rules()
    examples = get_examples()
    return f"{base}\n\n{rules}\n\n{examples}"
```

### 3. **Dynamic Prompts:**
```python
def get_agent_instruction(context=None):
    """Generate prompt based on context"""
    instruction = BASE_TEMPLATE
    
    if context and context.get('season') == 'summer':
        instruction += SUMMER_RULES
    
    return instruction
```

### 4. **Versioning:**
```python
PROMPT_VERSION = "2.1.0"

def get_agent_instruction():
    """Prompt v2.1.0 - Updated 2025-01-15"""
    return f"""
    [Version {PROMPT_VERSION}]
    ...
    """
```

## ⚠️ Lưu ý

### **Không nên compile:**
- Agent class initialization
- Tool registration code
- HTTP routing
- Odoo model definitions

### **Nên compile:**
- ✅ Prompt templates
- ✅ Business rules
- ✅ Decision logic
- ✅ Proprietary algorithms
- ✅ System instructions

## 📋 Checklist

- [ ] Tạo `prompt_config.py` riêng
- [ ] Move tất cả prompts vào `prompt_config.py`
- [ ] Move business rules vào `prompt_config.py`
- [ ] Update `agent_wrapper.py` import từ `prompt_config`
- [ ] Test agent hoạt động với prompts từ file mới
- [ ] Compile `prompt_config.py`
- [ ] Verify compiled version hoạt động
- [ ] Xóa `prompt_config.py` source trước deploy
- [ ] Deploy chỉ với `.so` files

## 📚 Tham khảo

- Cython Guide: `docs/cython_compilation.md`
- ADK Reference: `docs/google_adk_reference.md`
