# Google ADK - Core Concepts (Khái niệm cơ bản)

> **Source**: https://google.github.io/adk-docs/
> 
> **Last Updated**: 2025-12-22
>
> **IMPORTANT**: Nội dung này được trích xuất trực tiếp từ tài liệu chính thức của Google ADK.

---

## 📖 Tổng quan

Google Agent Development Kit (ADK) là một **open-source, code-first toolkit** để xây dựng, đánh giá và deploy các AI agents phức tạp với tính linh hoạt và kiểm soát cao.

---

## 1. Agents

### Định nghĩa (Từ tài liệu chính thức)
> "An Agent is a self-contained execution unit designed to act autonomously to achieve specific goals. Agents can perform tasks, interact with users, utilize external tools, and coordinate with other agents."

**BaseAgent** là foundation cho tất cả agents trong ADK.

### Core Agent Categories

1. **LLM Agents (LlmAgent, Agent)**
   - Sử dụng Large Language Models làm core engine
   - Hiểu natural language, reasoning, planning
   - Dynamically quyết định cách proceed hoặc tool nào sử dụng
   - Ideal cho flexible, language-centric tasks

2. **Workflow Agents (SequentialAgent, ParallelAgent, LoopAgent)**
   - Control execution flow của agents khác
   - Predefined, deterministic patterns
   - KHÔNG sử dụng LLM cho flow control
   - Perfect cho structured processes

3. **Custom Agents**
   - Extend BaseAgent directly
   - Unique operational logic
   - Specialized integrations

### Agent Class - Cú pháp CHÍNH XÁC
```python
from google.adk.agents import Agent

root_agent = Agent(
    name="weather_time_agent",              # Tên agent (required)
    model="gemini-2.0-flash",               # Model sử dụng (required)
    description=(                           # Mô tả agent làm gì
        "Agent to answer questions about the time and weather in a city."
    ),
    instruction=(                           # System instruction
        "You are a helpful agent who can answer user questions about the time and weather in a city."
    ),
    tools=[get_weather, get_current_time],  # List của functions
)
```

> ⚠️ **QUAN TRỌNG**: 
> - Import từ `google.adk.agents` KHÔNG PHẢI `adk`
> - Parameters: `name`, `model`, `description`, `instruction`, `tools`
> - KHÔNG có `system_instruction` - dùng `instruction`

---

## 2. Tools (Function Tools)

### Định nghĩa (Từ tài liệu chính thức)
> "Transforming a Python function into a tool is a straightforward way to integrate custom logic. When you assign a function to an agent's tools list, the framework automatically wraps it as a FunctionTool."

### Cách tạo Tool - MẪU CHÍNH XÁC từ Google
```python
def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city for which to retrieve the weather report.

    Returns:
        dict: status and result or error msg.
    """
    if city.lower() == "new york":
        return {
            "status": "success",
            "report": (
                "The weather in New York is sunny with a temperature of 25 degrees"
                " Celsius (77 degrees Fahrenheit)."
            ),
        }
    else:
        return {
            "status": "error",
            "error_message": f"Weather information for '{city}' is not available.",
        }
```

> ⚠️ **QUAN TRỌNG - TOOLS RETURN `dict` KHÔNG PHẢI `str`!**
> - Functions return `dict` với format `{"status": "success/error", "report/error_message": ...}`
> - KHÔNG return JSON string như tài liệu cũ nói

### Best Practices từ Google
- **Fewer Parameters are Better**: Minimize số parameters
- **Simple Data Types**: Favor `str`, `int` over custom classes
- **Meaningful Names**: Function name và parameter names ảnh hưởng cách LLM interpret tool
- **Docstring chi tiết**: LLM đọc docstring để hiểu cách dùng tool

---

## 3. Sessions

### Định nghĩa (Từ tài liệu chính thức)
> "Session represents a single, ongoing interaction between a user and your agent system. Contains the chronological sequence of messages and actions (Events)."

### Core Concepts
1. **Session**: Current conversation thread
   - Chronological sequence of Events
   - Holds temporary State

2. **State (session.state)**: Data within current conversation
   - Shopping cart items, user preferences
   - Chỉ relevant trong session hiện tại

3. **Memory**: Cross-session information
   - Spans multiple past sessions
   - Acts as searchable knowledge base

### Session Services
- **InMemorySessionService**: In-memory, mất khi restart
- **DatabaseSessionService**: Persistent storage

---

## 4. Runtime & Runner

### Runner (Từ tài liệu chính thức)
> "The main entry point and orchestrator for a single user query. Manages the overall Event Loop, receives events yielded by the Execution Logic."

### Cú pháp CHÍNH XÁC
```python
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

APP_NAME = "my_app"
USER_ID = "user_1234"
SESSION_ID = "session_1234"

# 1. Tạo Agent
agent = Agent(
    name="my_agent",
    model="gemini-2.0-flash",
    instruction="You are a helpful assistant.",
    tools=[my_tool]
)

# 2. Setup Session và Runner
async def setup_session_and_runner():
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME, 
        user_id=USER_ID, 
        session_id=SESSION_ID
    )
    runner = Runner(
        agent=agent, 
        app_name=APP_NAME, 
        session_service=session_service
    )
    return session, runner

# 3. Call Agent
async def call_agent_async(query):
    content = types.Content(
        role='user', 
        parts=[types.Part(text=query)]
    )
    session, runner = await setup_session_and_runner()
    
    events = runner.run_async(
        user_id=USER_ID, 
        session_id=SESSION_ID, 
        new_message=content
    )
    
    async for event in events:
        if event.is_final_response():
            final_response = event.content.parts[0].text
            print("Agent Response: ", final_response)
```

### Async vs Sync (Từ tài liệu chính thức)
> "Async is Primary. The ADK Runtime is fundamentally built on asynchronous patterns. `Runner.run_async` is the primary method. A synchronous `Runner.run` method exists mainly for convenience."

> ⚠️ **QUAN TRỌNG cho Odoo**:
> - Sử dụng `asyncio.run()` để chạy async code trong Odoo
> - Hoặc dùng `Runner.run()` (sync convenience method)

---

## 5. Content Types

### types.Content (Từ google.genai)
```python
from google.genai import types

# Tạo user message
content = types.Content(
    role='user',                              # 'user' hoặc 'model'
    parts=[types.Part(text="Hello, agent!")]  # List of Parts
)
```

> ⚠️ **QUAN TRỌNG**: 
> - Import từ `google.genai.types` KHÔNG PHẢI `adk.types`
> - `role='user'` cho user message, `role='model'` cho agent response

---

## 6. Project Structure (Từ Quickstart)

### Cấu trúc CHÍNH XÁC từ Google
```
parent_folder/
    multi_tool_agent/
        __init__.py
        agent.py
    .env
```

### __init__.py
```python
from . import agent
```

### agent.py
```python
from google.adk.agents import Agent

def my_tool(param: str) -> dict:
    """Tool description."""
    return {"status": "success", "report": "..."}

root_agent = Agent(
    name="my_agent",
    model="gemini-2.0-flash",
    description="Agent description",
    instruction="You are a helpful agent.",
    tools=[my_tool],
)
```

---

## 📌 Điểm QUAN TRỌNG cần nhớ (Từ tài liệu chính thức)

| Điểm | SAI (trước đây) | ĐÚNG (theo Google) |
|------|-----------------|-------------------|
| Import Agent | `from adk import Agent` | `from google.adk.agents import Agent` |
| Import types | `from adk import types` | `from google.genai import types` |
| Tool return | `str` hoặc JSON string | `dict` với status/report |
| Agent param | `system_instruction` | `instruction` |
| Runner | `InMemoryRunner` | `Runner` + `InMemorySessionService` |
| Run method | `runner.run(...)` | `runner.run_async(...)` (async primary) |

---

## 🔗 Tài liệu tham khảo

- **Official Docs**: https://google.github.io/adk-docs/
- **Quickstart**: https://google.github.io/adk-docs/get-started/quickstart/
- **Agents**: https://google.github.io/adk-docs/agents/
- **Tools**: https://google.github.io/adk-docs/tools-custom/function-tools/
- **Runtime**: https://google.github.io/adk-docs/runtime/
- **Sessions**: https://google.github.io/adk-docs/sessions/

---

> ⚠️ **LƯU Ý**: Tài liệu này được cập nhật trực tiếp từ https://google.github.io/adk-docs/. Nếu gặp lỗi, hãy kiểm tra lại tài liệu chính thức.
