# Compile Tool Logic - Bảo vệ Business Rules

Hướng dẫn compile logic của ADK Agent tools để bảo vệ thuật toán và business rules.

## 🎯 Vấn đề

Tools chứa:
- **Scoring algorithms** - Thuật toán tính điểm, xếp hạng
- **Validation rules** - Quy tắc kiểm tra, constraints
- **Business logic** - Logic nghiệp vụ proprietary
- **Decision making** - Thuật toán ra quyết định

➡️ **Cần compile** để bảo vệ IP

## 💡 Architecture

```
models/
├── business_logic.py       # ✅ COMPILE - Odoo data access
├── prompt_config.py        # ✅ COMPILE - Agent prompts
├── tool_logic.py           # ✅ COMPILE - Tool algorithms ⭐
└── agent_wrapper.py        # ❌ NO COMPILE - Thin wrappers
```

## 📝 Implementation

### 1. Tạo `tool_logic.py` (COMPILE)

```python
# -*- coding: utf-8 -*-
"""
Tool Logic - SẼ ĐƯỢC COMPILE
Chứa tất cả business logic của tools
"""

def analyze_best_sellers_logic(sales_data):
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
    """Thuật toán scoring - Bảo vệ công thức"""
    base = item['quantity'] * item['price']
    time_factor = get_time_decay(item['date'])
    margin_bonus = item['margin'] * 1.5
    
    # Proprietary formula
    score = base * time_factor + margin_bonus
    return score

def validate_mixing_rules_logic(ingredients, rules):
    """
    Validate công thức - Business rules.
    """
    violations = []
    
    # Check forbidden combinations
    for combo in rules['forbidden']:
        if all(i in ingredients for i in combo):
            violations.append(f"Không kết hợp {combo}")
    
    # Check limits
    if len(ingredients) > rules['max_ingredients']:
        violations.append("Quá nhiều nguyên liệu")
    
    return {
        'valid': len(violations) == 0,
        'violations': violations
    }

def calculate_cost_logic(ingredients, prices):
    """Tính cost - Proprietary pricing"""
    total = sum(prices.get(i, 0) for i in ingredients)
    
    # Secret markup formula
    markup = total * 0.6  # 60% margin
    suggested_price = total + markup
    
    return {
        'cost': total,
        'price': suggested_price,
        'margin': markup / suggested_price
    }
```

### 2. Update `agent_wrapper.py` (KHÔNG COMPILE)

```python
# -*- coding: utf-8 -*-
from google.adk.agents import Agent
from odoo import models, fields
from .business_logic import get_odoo_data_internal
from .prompt_config import get_agent_instruction
from .tool_logic import (  # Import compiled logic
    analyze_best_sellers_logic,
    validate_mixing_rules_logic,
    calculate_cost_logic
)

class TrcfAgentWrapper(models.Model):
    _name = 'trcf.agent.wrapper'
    
    def _create_tools(self):
        """Thin wrappers - Không chứa logic"""
        env = self.env
        
        def get_best_sellers() -> str:
            """Get top selling products"""
            # Get data
            data = get_odoo_data_internal(env, 'pos.order.line', ...)
            
            # Analyze với compiled logic
            result = analyze_best_sellers_logic(data)
            
            # Format
            return format_results(result)
        
        def validate_recipe(recipe: str) -> str:
            """Validate recipe rules"""
            ingredients = parse_recipe(recipe)
            rules = get_rules()
            
            # Validate với compiled logic
            validation = validate_mixing_rules_logic(ingredients, rules)
            
            return format_validation(validation)
        
        def calculate_pricing(ingredients: str) -> str:
            """Calculate cost and pricing"""
            items = parse_ingredients(ingredients)
            prices = get_prices(env)
            
            # Calculate với compiled logic
            pricing = calculate_cost_logic(items, prices)
            
            return f"Cost: {pricing['cost']}, Price: {pricing['price']}"
        
        return [get_best_sellers, validate_recipe, calculate_pricing]
```

## 🔧 Compilation

```bash
cd custom_addons/trcf_my_agent

# Compile tool logic
cythonize -i models/tool_logic.py

# Cùng với các files khác
cythonize -i models/business_logic.py
cythonize -i models/prompt_config.py
```

## 📦 Deploy Structure

**Trước compile:**
```
models/
├── business_logic.py
├── prompt_config.py
├── tool_logic.py          # ← Chứa algorithms
├── agent_wrapper.py
```

**Sau compile & deploy:**
```
models/
├── business_logic.so      # ✅
├── prompt_config.so       # ✅
├── tool_logic.so          # ✅ Tool logic protected
├── agent_wrapper.py       # Source (thin wrappers only)
```

## ✅ Lợi ích

1. **Bảo vệ algorithms**: Scoring, ranking, analysis
2. **Che giấu rules**: Validation, constraints, limits
3. **Bảo mật pricing**: Cost calculations, margins
4. **IP protection**: Competitive advantages

## 🎯 Best Practices

### 1. Tách rõ Logic vs Wrapper

**❌ Không tốt - Logic trong wrapper:**
```python
def get_best_sellers() -> str:
    data = get_data()
    # Complex scoring logic here (không được bảo vệ)
    score = data['qty'] * data['price'] * 1.5
    return format(score)
```

**✅ Tốt - Logic tách riêng:**
```python
# tool_logic.py (COMPILE)
def calculate_score(data):
    return data['qty'] * data['price'] * 1.5

# agent_wrapper.py (NO COMPILE)
def get_best_sellers() -> str:
    data = get_data()
    score = calculate_score(data)  # Gọi compiled
    return format(score)
```

### 2. Modular Tool Logic

```python
# tool_logic.py
def analyze_sales(data):
    """Main analysis"""
    scores = calculate_scores(data)
    trends = detect_trends(data)
    return combine_results(scores, trends)

def calculate_scores(data):
    """Scoring sub-logic"""
    pass

def detect_trends(data):
    """Trend detection sub-logic"""
    pass
```

### 3. Configuration-Driven

```python
# tool_logic.py
SCORING_WEIGHTS = {
    'quantity': 1.0,
    'price': 0.8,
    'margin': 1.5,
    'repeat_customer': 2.0
}

def calculate_score(item):
    score = 0
    for factor, weight in SCORING_WEIGHTS.items():
        score += item.get(factor, 0) * weight
    return score
```

## 📋 Checklist

- [ ] Tạo `tool_logic.py`
- [ ] Move tool algorithms vào `tool_logic.py`
- [ ] Move validation rules vào `tool_logic.py`
- [ ] Move pricing logic vào `tool_logic.py`
- [ ] Update `agent_wrapper.py` import từ `tool_logic`
- [ ] Tool wrappers chỉ còn thin wrappers
- [ ] Test tools hoạt động
- [ ] Compile `tool_logic.py`
- [ ] Verify compiled version
- [ ] Deploy với `.so` files

## 📚 Tham khảo

- Protect Prompts: `docs/protect_agent_prompts.md`
- Cython Guide: `docs/cython_compilation.md`
