# ADK Best Practices (Thực hành tốt nhất)

> **Source**: https://google.github.io/adk-docs/tools-custom/function-tools/
> 
> **Last Updated**: 2025-12-22
>
> **IMPORTANT**: Nội dung dựa trên tài liệu chính thức Google ADK

---

## 1. Agent Design

### System Instructions (gọi là `instruction` trong ADK)
✅ **Nên làm:**
- Rõ ràng, cụ thể về vai trò của agent
- Liệt kê các khả năng và giới hạn
- Cung cấp context về Odoo environment
- Hướng dẫn cách sử dụng tools

❌ **Không nên:**
- Instructions quá dài, phức tạp
- Mơ hồ về mục đích
- Thiếu context về business domain

### Ví dụ tốt
```python
from google.adk.agents import Agent

agent = Agent(
    name="coffee_assistant",
    model="gemini-2.0-flash",
    description="Agent quản lý quán cà phê",
    instruction="""Bạn là trợ lý AI cho hệ thống quản lý quán cà phê.

Khả năng:
- Tìm kiếm sản phẩm trong menu
- Tạo đơn hàng mới
- Kiểm tra tồn kho

Giới hạn:
- Không thể xóa đơn hàng đã thanh toán
- Không có quyền thay đổi giá

Ngữ cảnh:
- Hệ thống Odoo 19
- Dữ liệu tiếng Việt""",
    tools=[search_products, create_order]
)
```

---

## 2. Tool Design (Từ tài liệu chính thức)

### ⚠️ QUAN TRỌNG: Tools TRẢ VỀ `dict`, KHÔNG PHẢI `str`!

Theo https://google.github.io/adk-docs/tools-custom/function-tools/:
> "The return value from this tool will be wrapped into a Map."

```python
# ✅ ĐÚNG - Tool trả về dict với status/report pattern
def search_products(query: str) -> dict:
    """
    Search products by name or code.
    
    Args:
        query (str): Search term
        
    Returns:
        dict: status and result or error msg.
    """
    if products_found:
        return {
            "status": "success",
            "report": f"Found {len(products)} products"
        }
    else:
        return {
            "status": "error",
            "error_message": f"No products found for '{query}'"
        }

# ❌ SAI - Đây là cách CŨ, không đúng!
def search_products(query: str) -> str:
    return json.dumps(results)  # KHÔNG ĐÚNG!
```

### Nguyên tắc từ Google ADK Docs

#### 1. Fewer Parameters are Better
> "Minimize the number of parameters to reduce complexity."

```python
# ✅ ĐÚNG - Ít parameters
def get_weather(city: str) -> dict:
    """Get weather for a city."""
    ...

# ❌ SAI - Quá nhiều parameters
def get_weather(city: str, unit: str, language: str, format: str, include_forecast: bool) -> dict:
    ...
```

#### 2. Simple Data Types
> "Favor primitive data types like str and int over custom classes whenever possible."

```python
# ✅ ĐÚNG
def get_product(product_id: int) -> dict:
    ...

# ❌ SAI
def get_product(product: ProductObject) -> dict:
    ...
```

#### 3. Meaningful Names
> "The function's name and parameter names significantly influence how the LLM interprets and utilizes the tool."

```python
# ✅ ĐÚNG - Tên có nghĩa
def search_products_by_name(product_name: str) -> dict:
    """Search products by their name in the catalog."""
    ...

# ❌ SAI - Tên chung chung
def do_stuff(data: str) -> dict:
    """Process data."""
    ...
```

#### 4. Clear Docstring
> "The ADK framework automatically inspects your Python function's signature—including its name, docstring, parameters, type hints—to generate a schema."

```python
def get_stock_price(symbol: str) -> dict:
    """
    Retrieves the current stock price for a given symbol.

    Args:
        symbol (str): The stock symbol (e.g., "AAPL", "GOOG").

    Returns:
        dict: status and result or error msg.
    """
    try:
        price = fetch_price(symbol)
        return {"status": "success", "report": f"Price of {symbol}: ${price}"}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
```

---

## 3. Error Handling trong Tools

### Pattern chuẩn từ Google
```python
def my_tool(param: str) -> dict:
    """Tool with proper error handling."""
    try:
        # Validate input
        if not param:
            return {
                "status": "error",
                "error_message": "Parameter 'param' is required"
            }
        
        # Execute logic
        result = do_something(param)
        
        # Return success
        return {
            "status": "success",
            "report": f"Result: {result}"
        }
        
    except Exception as e:
        _logger.error(f"Error in my_tool: {e}", exc_info=True)
        return {
            "status": "error",
            "error_message": f"Operation failed: {str(e)}"
        }
```

---

## 4. Security trong Odoo Tools

### Permission Checks
```python
def create_order(product_ids: str, quantities: str) -> dict:
    """Create sales order with permission check."""
    # Check permission FIRST
    if not env.user.has_group('sales_team.group_sale_salesman'):
        return {
            "status": "error",
            "error_message": "Bạn không có quyền tạo đơn hàng"
        }
    
    # Proceed with creation
    try:
        order = env['sale.order'].create({...})
        return {
            "status": "success",
            "report": f"Đã tạo đơn hàng #{order.name}"
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
```

### Input Validation
```python
# Whitelist allowed models
ALLOWED_MODELS = ['product.product', 'sale.order', 'stock.picking']

def search_records(model_name: str, query: str) -> dict:
    """Search records with validation."""
    if model_name not in ALLOWED_MODELS:
        return {
            "status": "error",
            "error_message": f"Model {model_name} not allowed"
        }
    
    # Continue with search...
```

---

## 5. Testing

### Unit Tests cho Tools
```python
from odoo.tests import TransactionCase
import json

class TestAgentTools(TransactionCase):
    
    def test_search_products_success(self):
        """Test product search returns dict with status."""
        result = search_products("coffee")
        
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'success')
        self.assertIn('report', result)
    
    def test_search_products_error(self):
        """Test error handling."""
        result = search_products("")  # Empty query
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['status'], 'error')
        self.assertIn('error_message', result)
```

---

## 6. Performance

### Cache Agent Instance
```python
from functools import lru_cache

class MyAgentModel(models.Model):
    
    @lru_cache(maxsize=1)
    def _get_agent(self):
        """Cache agent instance."""
        return Agent(
            name="my_agent",
            model="gemini-2.0-flash",
            instruction="...",
            tools=[...]
        )
```

### Limit Results trong Tools
```python
def search_products(query: str, limit: int = 10) -> dict:
    """Search with result limit."""
    MAX_LIMIT = 50
    limit = min(limit, MAX_LIMIT)  # Enforce maximum
    
    products = env['product.product'].search([
        ('name', 'ilike', query)
    ], limit=limit)
    
    return {
        "status": "success",
        "report": f"Found {len(products)} products (max {limit})"
    }
```

---

## 📌 Checklist Best Practices

### Agent Design
- [ ] Dùng `instruction` (KHÔNG PHẢI `system_instruction`)
- [ ] Dùng `description` để mô tả agent
- [ ] Import từ `google.adk.agents`

### Tool Design
- [ ] **Return `dict` với status/report pattern**
- [ ] Fewer parameters are better
- [ ] Simple data types (str, int)
- [ ] Meaningful function và parameter names
- [ ] Clear docstrings với Args và Returns

### Error Handling
- [ ] Try/except trong mỗi tool
- [ ] Return `{"status": "error", "error_message": "..."}`
- [ ] Log errors cho debugging

### Security
- [ ] Permission checks trong tools
- [ ] Input validation
- [ ] Model whitelist

---

## 🔗 Tham khảo

- **Function Tools**: https://google.github.io/adk-docs/tools-custom/function-tools/
- **Quickstart**: https://google.github.io/adk-docs/get-started/quickstart/
- Xem thêm: `core-concepts.md`
