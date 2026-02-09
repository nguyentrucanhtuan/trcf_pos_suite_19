# Tài liệu tham khảo về ADK Tools

Công cụ (Tools) giúp Agent tương tác được với Odoo và các hệ thống bên ngoài.

## 1. Công cụ có sẵn (Pre-built Tools)
ADK cung cấp một số công cụ tích hợp:
- **Google Search**: Thông qua Gemini API.
- **Code Execution**: Môi trường Python nội bộ để giải quyết toán học/logic.
- **Vertex AI RAG**: Tích hợp với cơ sở dữ liệu Vector.

## 2. Function Tools (Quan trọng nhất với Odoo)
Các hàm công cụ PHẢI sử dụng **Python Type Hinting** và **Docstrings**.
```python
def get_stock_qty(product_id: int) -> float:
    """Lấy số lượng tồn kho khả dụng cho một ID sản phẩm cụ thể."""
    # Logic truy vấn Odoo ORM (dùng env truyền từ class cha)
    return 100.0
```

## 3. Quy tắc chuẩn cho Tools
- **Nomenclature (Đặt tên)**: Tên hàm rõ ràng, mang tính mô tả hành động.
- **Typing**: Luôn khai báo kiểu dữ liệu cho tham số và giá trị trả về.
- **Docstrings**: LLM dựa vào đây để hiểu *cách dùng* và *lý do* dùng công cụ.
- **Granularity (Độ chi tiết)**: Mỗi công cụ chỉ nên làm một việc duy nhất.
- **Error Handling**: Nên trả về thông báo lỗi thân thiện thay vì làm crash chương trình.

## 4. MCP Tools
ADK hỗ trợ **Model Context Protocol (MCP)**, cho phép kết nối với các server MCP bên ngoài như database, API hoặc file cục bộ.
