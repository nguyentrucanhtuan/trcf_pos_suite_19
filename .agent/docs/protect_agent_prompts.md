# Bảo vệ Agent Prompts với Cython

> **Last Updated**: 2025-12-22
>
> **Mục đích**: Tách và compile prompts/instructions để bảo vệ business logic khi deploy cho khách hàng.

---

## 🎯 Vấn đề

Khi deploy ADK Agent, **instruction/prompt** chứa:
- Business logic và quy trình
- Proprietary knowledge
- Decision-making rules
- Competitive advantages

➡️ **Cần compile** để khách hàng không thấy được source code.

---

## 💡 Giải pháp: Tách Prompt + Compile

### Architecture Pattern

```
models/
├── agents/
│   └── my_agent/
│       ├── __init__.py       # ❌ KHÔNG compile
│       ├── agent.py          # ❌ KHÔNG compile (Agent wrapper)
│       ├── prompts.py        # ✅ COMPILE - Prompts/Instructions
│       └── business_logic.py # ✅ COMPILE - Tool logic
```

**Nguyên tắc:**
- **COMPILE**: Files chứa logic proprietary
- **KHÔNG COMPILE**: Agent wrapper, Odoo models, __init__.py

---

## 📝 Implementation

### 1. `prompts.py` (✅ COMPILE)

```python
# -*- coding: utf-8 -*-
"""
Prompt Configuration - SẼ ĐƯỢC COMPILE
"""

def get_system_instruction(today_str=None):
    """
    System instruction cho agent.
    
    Function này sẽ được compile để bảo vệ prompt logic.
    """
    base = f"""Bạn là chuyên gia R&D đồ uống cho chuỗi cà phê.
HÔM NAY: {today_str or 'không xác định'}

NHIỆM VỤ:
1. Phân tích dữ liệu bán hàng
2. Tìm kiếm xu hướng mới
3. Đề xuất công thức món mới

QUY TRÌNH:
1. Dùng tool `get_best_sellers` để xem món bán chạy
2. Dùng tool `search_trends` để tìm xu hướng
3. Dùng tool `validate_recipe` để kiểm tra công thức

QUY TẮC:
- Margin tối thiểu: 60%
- Không quá 5 nguyên liệu
- Ưu tiên nguyên liệu sẵn có"""
    
    return base

def get_business_rules():
    """Business rules - Proprietary logic."""
    return {
        'min_margin': 0.6,
        'max_ingredients': 5,
        'forbidden_combinations': [
            ('milk', 'citrus'),
            ('coffee', 'yogurt'),
        ],
        'seasonal_multiplier': {
            'summer': {'cold_drinks': 1.5, 'hot_drinks': 0.7},
            'winter': {'cold_drinks': 0.8, 'hot_drinks': 1.3},
        }
    }
```

### 2. `business_logic.py` (✅ COMPILE)

```python
# -*- coding: utf-8 -*-
"""
Business Logic - SẼ ĐƯỢC COMPILE
Chứa thuật toán proprietary
"""
import logging
_logger = logging.getLogger(__name__)

def get_best_sellers_data(env):
    """Lấy và xử lý dữ liệu bán chạy."""
    try:
        # Query Odoo data
        lines = env['pos.order.line'].search([...], limit=100)
        
        # Proprietary analysis
        analyzed = analyze_sales_data(lines)
        return analyzed
    except Exception as e:
        _logger.error(f"Error: {e}")
        return []

def analyze_sales_data(lines):
    """Phân tích data - Proprietary algorithm."""
    results = []
    for line in lines:
        score = calculate_popularity_score(line)
        results.append({
            'product': line.product_id.name,
            'score': score,
            'quantity': line.qty
        })
    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:5]

def calculate_popularity_score(line):
    """Scoring algorithm - Bảo vệ công thức."""
    # Proprietary formula
    base = line.qty * line.price_subtotal
    margin_bonus = base * 0.15
    return base + margin_bonus

def validate_recipe_logic(ingredients, rules):
    """Validate công thức - Business rules."""
    violations = []
    
    for combo in rules.get('forbidden_combinations', []):
        if all(i in ingredients for i in combo):
            violations.append(f"Không kết hợp {combo}")
    
    if len(ingredients) > rules.get('max_ingredients', 5):
        violations.append("Quá nhiều nguyên liệu")
    
    return {
        'valid': len(violations) == 0,
        'violations': violations
    }
```

### 3. `agent.py` (❌ KHÔNG COMPILE)

```python
# -*- coding: utf-8 -*-
"""
Agent Wrapper - KHÔNG COMPILE
Thin wrapper, import từ compiled modules
"""
import os
import asyncio

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import TỪ FILES SẼ COMPILE
from . import prompts         # prompts.so
from . import business_logic  # business_logic.so

APP_NAME = "my_agent"

class MyAgent:
    def __init__(self, env):
        self.env = env
    
    def _create_tools(self):
        """Tool wrappers - chỉ gọi compiled logic."""
        env = self.env
        
        # ⚠️ Tools TRẢ VỀ DICT (theo Google ADK docs)
        def get_best_sellers() -> dict:
            """Get top selling products."""
            try:
                data = business_logic.get_best_sellers_data(env)
                return {
                    "status": "success",
                    "report": f"Top sellers: {data}"
                }
            except Exception as e:
                return {"status": "error", "error_message": str(e)}
        
        def validate_recipe(ingredients: str) -> dict:
            """Validate a recipe."""
            try:
                items = [i.strip() for i in ingredients.split(',')]
                rules = prompts.get_business_rules()
                result = business_logic.validate_recipe_logic(items, rules)
                
                if result['valid']:
                    return {"status": "success", "report": "Công thức hợp lệ"}
                else:
                    return {"status": "error", "error_message": str(result['violations'])}
            except Exception as e:
                return {"status": "error", "error_message": str(e)}
        
        return [get_best_sellers, validate_recipe]
    
    def create_agent(self):
        """Tạo agent - dùng prompts từ compiled module."""
        api_key = self.env['ir.config_parameter'].sudo().get_param('trcf.gemini_api_key', '')
        os.environ['GOOGLE_API_KEY'] = api_key
        
        from odoo import fields
        today = fields.Date.today().strftime('%d-%m-%Y')
        
        # Instruction TỪ COMPILED prompts.so
        instruction = prompts.get_system_instruction(today)
        
        return Agent(
            name="my_agent",
            model="gemini-2.0-flash",
            description="AI Agent for business analysis",
            instruction=instruction,  # Từ compiled module!
            tools=self._create_tools()
        )
```

---

## 🔧 Compilation Commands

```bash
cd custom_addons/trcf_my_agent/models/agents/my_agent

# Compile prompts và business logic
cythonize -i prompts.py
cythonize -i business_logic.py

# KHÔNG compile agent.py
```

---

## 📦 Deploy Structure

**Trước compile:**
```
my_agent/
├── __init__.py
├── agent.py           # Source
├── prompts.py         # Source - CHỨA PROMPTS
├── business_logic.py  # Source - CHỨA ALGORITHMS
```

**Sau compile (deploy):**
```
my_agent/
├── __init__.py                    # Giữ nguyên
├── agent.py                       # Giữ nguyên (thin wrapper)
├── prompts.cpython-39-darwin.so   # ✅ Compiled
├── business_logic.cpython-39-darwin.so  # ✅ Compiled
```

**Xóa source trước deploy:**
```bash
rm prompts.py business_logic.py
# Giữ lại agent.py (nó chỉ là wrapper)
```

---

## ✅ Lợi ích

1. **Bảo vệ Prompts**: Khách không thấy được instructions
2. **Bảo vệ Algorithms**: Business logic được compile
3. **Dễ maintain**: agent.py vẫn readable, dễ debug
4. **Flexible**: Update compiled files mà không đổi wrapper

---

## 📋 Checklist

- [ ] Tách prompts vào `prompts.py`
- [ ] Tách business logic vào `business_logic.py`
- [ ] `agent.py` chỉ còn thin wrappers
- [ ] **Tools trả về `dict` với status/report** (theo ADK docs)
- [ ] Test agent hoạt động với source files
- [ ] Compile `prompts.py` và `business_logic.py`
- [ ] Test agent với compiled files
- [ ] Xóa `.py` source, giữ `.so`
- [ ] Deploy

---

## 🔗 Tham khảo

- Cython Guide: `docs/cython_compilation.md`
- Tool Logic Protection: `docs/compile_tool_logic.md`
- ADK Concepts: `context_adk_agent/core-concepts.md`
