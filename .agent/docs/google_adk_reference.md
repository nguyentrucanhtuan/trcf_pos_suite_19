# Google Agent Development Kit (ADK) - Reference Guide

> **Source**: https://google.github.io/adk-docs/llms.txt
> 
> **Last Updated**: 2025-12-17
>
> **Full Documentation**: File gốc tại `google_adk_llms.txt`

## 📖 Tổng quan

Google Agent Development Kit (ADK) là một open-source, code-first toolkit để xây dựng, đánh giá và deploy các AI agents phức tạp với tính linh hoạt và kiểm soát cao.

## 🎯 Core Concepts

### 1. Agent Class
```python
from google.adk.agents import Agent

agent = Agent(
    name="agent_name",
    model="gemini-2.5-flash",  # hoặc model khác
    tools=[...],               # Danh sách tools
    instruction="..."          # System instruction
)
```

### 2. Tools
Tools là các functions mà agent có thể gọi:

```python
def my_tool(param: str) -> str:
    """
    Docstring này rất quan trọng - Agent sẽ đọc để hiểu cách dùng tool.
    
    Args:
        param: Mô tả parameter
        
    Returns:
        Mô tả return value
    """
    return result
```

**Best Practices cho Tools:**
- ✅ Docstring rõ ràng, chi tiết
- ✅ Type hints đầy đủ
- ✅ Functions đơn giản, focused
- ✅ Return string hoặc serializable data
- ❌ Không nên có side effects phức tạp
- ❌ Không nên blocking quá lâu

### 3. Built-in Tools
ADK cung cấp sẵn một số tools:

```python
from google.adk.tools import (
    google_search,      # Google Search
    code_execution,     # Execute code
    # ... và nhiều tools khác
)
```

### 4. Multi-Agent Systems
Có thể tạo team of agents:

```python
from google.adk.agents import Agent

researcher = Agent(name="researcher", ...)
writer = Agent(name="writer", ...)

# Agents có thể gọi nhau thông qua A2A protocol
```

## 🏗️ Architecture Patterns

### Pattern 1: Single Agent với Multiple Tools
```python
agent = Agent(
    name="assistant",
    tools=[tool1, tool2, tool3],
    instruction="Use tools to accomplish tasks"
)
```

### Pattern 2: Agent Team (Multi-Agent)
```python
# Agent chuyên môn hóa
data_agent = Agent(name="data_analyst", tools=[query_db, analyze_data])
report_agent = Agent(name="reporter", tools=[generate_report])
```

### Pattern 3: Streaming Agent
```python
# Cho real-time responses
from google.adk.agents import StreamingAgent

agent = StreamingAgent(
    name="chat_agent",
    model="gemini-2.5-flash",
    # ... config streaming
)
```

## 🔧 Integration với Odoo

### Recommended Structure cho Odoo Module

```
trcf_my_agent/
├── models/
│   ├── business_logic.py      # ✅ COMPILE - Logic nghiệp vụ
│   ├── data_service.py        # ✅ COMPILE - Odoo data access
│   └── agent_wrapper.py       # ❌ NO COMPILE - ADK agent definition
├── controllers/
│   └── agent_controller.py    # HTTP endpoints
└── ...
```

### Example: Odoo + ADK Integration

```python
# ===== models/business_logic.py (CÓ THỂ COMPILE) =====
def get_sales_data_internal(date_from, date_to):
    """Lấy dữ liệu từ Odoo - Logic có thể compile"""
    # Odoo ORM queries
    orders = env['sale.order'].search([...])
    return process_orders(orders)

def format_sales_report(data):
    """Format data - Logic có thể compile"""
    return formatted_string

# ===== models/agent_wrapper.py (KHÔNG COMPILE) =====
from google.adk.agents import Agent
from .business_logic import get_sales_data_internal, format_sales_report

def get_sales_data(query: str) -> str:
    """Tool wrapper cho ADK"""
    data = get_sales_data_internal(...)  # Gọi compiled logic
    return format_sales_report(data)

sales_agent = Agent(
    name="sales_analyst",
    model="gemini-2.5-flash",
    tools=[get_sales_data],
    instruction="Analyze sales data and provide insights"
)
```

## 📚 Key Documentation Links

Tham khảo file `google_adk_llms.txt` để xem full documentation structure:

- **Get Started**: Quickstart guides cho Python, TypeScript, Java, Go
- **Build Agents**: Tutorials, tools, custom tools
- **Run Agents**: Runtime, API server, deployment
- **Components**: Context, memory, callbacks, artifacts
- **Deploy**: Agent Engine, Cloud Run, GKE
- **Observability**: Logging, tracing, analytics

## 🎓 Best Practices

### 1. Separation of Concerns
- **Business Logic**: Tách riêng, có thể compile
- **Agent Definition**: Wrapper mỏng, không compile
- **Tools**: Simple functions, clear purpose

### 2. Tool Design
- Mỗi tool làm 1 việc cụ thể
- Docstring chi tiết
- Error handling rõ ràng
- Return format consistent

### 3. Instruction Writing
- Rõ ràng, cụ thể
- Mô tả workflow từng bước
- Đưa ra examples khi cần
- Định nghĩa expected output

### 4. Testing
- Test tools riêng biệt
- Test agent với mock tools
- Integration tests với real tools

## 🔐 Security & Compilation

### Khi dùng Cython:

**COMPILE:**
- ✅ Business logic functions
- ✅ Data processing
- ✅ Proprietary algorithms
- ✅ Helper utilities

**KHÔNG COMPILE:**
- ❌ Agent class definitions
- ❌ Tool wrapper functions (nếu đơn giản)
- ❌ External library imports
- ❌ Dynamic code generation

## 📖 Đọc thêm

- Full docs: https://google.github.io/adk-docs/
- Source file: `custom_addons/.agent/docs/google_adk_llms.txt`
- GitHub: https://github.com/google/adk
