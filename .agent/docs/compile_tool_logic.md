# Compile Tool Logic - Bảo vệ Business Rules

> **Last Updated**: 2025-12-22
>
> **Mục đích**: Compile logic của ADK Agent tools để bảo vệ thuật toán và business rules.

---

## 🎯 Vấn đề

Tools chứa:
- **Scoring algorithms** - Thuật toán tính điểm, xếp hạng
- **Validation rules** - Quy tắc kiểm tra, constraints
- **Business logic** - Logic nghiệp vụ proprietary
- **Decision making** - Thuật toán ra quyết định

➡️ **Cần compile** để bảo vệ IP

---

## 💡 Architecture

```
models/agents/my_agent/
├── __init__.py         # ❌ KHÔNG compile
├── agent.py            # ❌ KHÔNG compile - Thin wrappers
├── prompts.py          # ✅ COMPILE - Agent prompts
└── business_logic.py   # ✅ COMPILE - Tool algorithms ⭐
```

---

## 📝 Implementation

### 1. `business_logic.py` (✅ COMPILE)

```python
# -*- coding: utf-8 -*-
"""
Business Logic - SẼ ĐƯỢC COMPILE
Chứa tất cả thuật toán proprietary
"""
import logging
_logger = logging.getLogger(__name__)

def analyze_best_sellers(sales_data):
    """
    Phân tích món bán chạy - Proprietary algorithm.
    """
    analyzed = []
    for item in sales_data:
        score = calculate_popularity_score(item)
        trend = detect_trend(item)
        analyzed.append({
            'product': item['name'],
            'score': score,
            'trend': trend,
        })
    
    analyzed.sort(key=lambda x: x['score'], reverse=True)
    return analyzed[:5]

def calculate_popularity_score(item):
    """Thuật toán scoring - Bảo vệ công thức."""
    base = item['quantity'] * item['price']
    time_factor = get_time_decay(item.get('date'))
    margin_bonus = item.get('margin', 0) * 1.5
    
    # Proprietary formula
    score = base * time_factor + margin_bonus
    return score

def get_time_decay(date):
    """Time decay factor."""
    # Proprietary logic
    return 0.9

def detect_trend(item):
    """Detect trend - Proprietary."""
    return "stable"

def validate_mixing_rules(ingredients, rules):
    """
    Validate công thức - Business rules.
    """
    violations = []
    
    # Check forbidden combinations
    for combo in rules.get('forbidden', []):
        if all(i in ingredients for i in combo):
            violations.append(f"Không kết hợp {combo}")
    
    # Check limits
    if len(ingredients) > rules.get('max_ingredients', 5):
        violations.append("Quá nhiều nguyên liệu")
    
    return {
        'valid': len(violations) == 0,
        'violations': violations
    }

def calculate_cost(ingredients, prices):
    """Tính cost - Proprietary pricing."""
    total = sum(prices.get(i, 0) for i in ingredients)
    
    # Secret markup formula
    markup = total * 0.6  # 60% margin
    suggested_price = total + markup
    
    return {
        'cost': total,
        'price': suggested_price,
        'margin': markup / suggested_price if suggested_price > 0 else 0
    }
```

### 2. `agent.py` (❌ KHÔNG COMPILE)

```python
# -*- coding: utf-8 -*-
"""Agent Wrapper - KHÔNG COMPILE"""
import os
import asyncio

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

# Import TỪ COMPILED modules
from . import prompts
from . import business_logic

class MyAgent:
    def __init__(self, env):
        self.env = env
    
    def _create_tools(self):
        """Thin wrappers - Không chứa logic."""
        env = self.env
        
        # ⚠️ Tools TRẢ VỀ DICT (theo Google ADK docs)
        def get_best_sellers() -> dict:
            """Get top selling products."""
            try:
                # Get data từ Odoo
                lines = env['pos.order.line'].sudo().search([], limit=50)
                data = [{'name': l.product_id.name, 'quantity': l.qty, 'price': l.price_subtotal} for l in lines]
                
                # Analyze VỚI COMPILED logic
                result = business_logic.analyze_best_sellers(data)
                
                return {
                    "status": "success",
                    "report": f"Top 5 best sellers: {result}"
                }
            except Exception as e:
                return {"status": "error", "error_message": str(e)}
        
        def validate_recipe(ingredients: str) -> dict:
            """Validate recipe rules."""
            try:
                items = [i.strip() for i in ingredients.split(',')]
                rules = prompts.get_business_rules()
                
                # Validate VỚI COMPILED logic
                validation = business_logic.validate_mixing_rules(items, rules)
                
                if validation['valid']:
                    return {"status": "success", "report": "Công thức hợp lệ ✅"}
                else:
                    return {"status": "error", "error_message": str(validation['violations'])}
            except Exception as e:
                return {"status": "error", "error_message": str(e)}
        
        def calculate_pricing(ingredients: str) -> dict:
            """Calculate cost and pricing."""
            try:
                items = [i.strip() for i in ingredients.split(',')]
                prices = {'coffee': 5000, 'milk': 3000, 'sugar': 1000}  # Example
                
                # Calculate VỚI COMPILED logic
                pricing = business_logic.calculate_cost(items, prices)
                
                return {
                    "status": "success", 
                    "report": f"Cost: {pricing['cost']:,}đ, Price: {pricing['price']:,}đ, Margin: {pricing['margin']:.0%}"
                }
            except Exception as e:
                return {"status": "error", "error_message": str(e)}
        
        return [get_best_sellers, validate_recipe, calculate_pricing]
```

---

## 🔧 Compilation

```bash
cd custom_addons/trcf_my_agent/models/agents/my_agent

# Compile business logic
cythonize -i business_logic.py

# Compile prompts
cythonize -i prompts.py
```

---

## 📦 Deploy Structure

**Trước compile:**
```
my_agent/
├── __init__.py
├── business_logic.py   # ← Source - chứa algorithms
├── prompts.py          # ← Source - chứa prompts
├── agent.py
```

**Sau compile & deploy:**
```
my_agent/
├── __init__.py
├── business_logic.so   # ✅ Compiled - algorithms protected
├── prompts.so          # ✅ Compiled - prompts protected
├── agent.py            # Source (thin wrappers only)
```

---

## ✅ Best Practices

### 1. Tách rõ Logic vs Wrapper

**❌ Không tốt - Logic trong wrapper:**
```python
def get_best_sellers() -> dict:
    data = get_data()
    # Complex scoring logic ở đây (KHÔNG được bảo vệ!)
    score = data['qty'] * data['price'] * 1.5
    return {"status": "success", "report": str(score)}
```

**✅ Tốt - Logic tách riêng:**
```python
# business_logic.py (COMPILE)
def calculate_score(data):
    return data['qty'] * data['price'] * 1.5

# agent.py (KHÔNG COMPILE)
def get_best_sellers() -> dict:
    data = get_data()
    score = business_logic.calculate_score(data)  # Gọi compiled
    return {"status": "success", "report": str(score)}
```

### 2. Tools Return Dict

```python
# ⚠️ QUAN TRỌNG: Theo Google ADK docs, tools trả về dict

def my_tool(param: str) -> dict:
    """Tool description."""
    if success:
        return {"status": "success", "report": "..."}
    else:
        return {"status": "error", "error_message": "..."}
```

---

## 📋 Checklist

- [ ] Tạo `business_logic.py` với algorithms
- [ ] Move tool logic vào `business_logic.py`
- [ ] Move validation rules vào `business_logic.py`
- [ ] Move pricing logic vào `business_logic.py`
- [ ] `agent.py` chỉ còn thin wrappers
- [ ] **Tools trả về dict với status/report**
- [ ] Test tools hoạt động
- [ ] Compile `business_logic.py`
- [ ] Verify compiled version
- [ ] Deploy với `.so` files

---

## 🔗 Tham khảo

- Protect Prompts: `docs/protect_agent_prompts.md`
- Cython Guide: `docs/cython_compilation.md`
- ADK Concepts: `context_adk_agent/core-concepts.md`
