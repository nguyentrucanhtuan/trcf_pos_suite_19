{
    "name": "TRCF AI Business Assistant",
    "version": "2.0",
    "summary": "Multi-Agent AI Assistant với Trợ lý Sáng tạo Thức uống và Trợ lý Kinh doanh",
    "description": """
        Tích hợp Google Gemini vào Odoo với kiến trúc Multi-Agent.
        
        AGENTS:
        - Trợ lý Sáng tạo Thức uống: Tìm trend, tra công thức, gợi ý món mới
        - Trợ lý Kinh doanh: Phân tích doanh thu, đơn hàng
        
        TÍNH NĂNG:
        - Auto-routing tin nhắn đến agent phù hợp
        - Quy tắc pha chế configurable trong Settings
        - Hỗ trợ Cython compilation cho business logic
    """,
    "author": "Tuấn Rang Cà Phê",
    "website": "https://coffeetree.vn",
    "category": "AI",
    "depends": ["base", "mail", "point_of_sale", "mrp", "product"],
    "external_dependencies": {
        "python": ["google-adk", "google-genai"],
    },
    "data": [
        "data/bot_data.xml",
        "views/res_config_settings_views.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": True,
}
