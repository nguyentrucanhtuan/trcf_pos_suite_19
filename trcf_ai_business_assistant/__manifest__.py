{
    "name": "TRCF AI Business Assistant (Gemini)",
    "version": "1.0",
    "summary": "Trợ lý kinh doanh sử dụng Google Gemini để phân tích dữ liệu Odoo",
    "description": """
            Tích hợp Google Gemini vào Odoo để tạo Trợ lý Kinh Doanh thông minh.
            Hỗ trợ tự động phân tích lợi nhuận, chi phí và hiệu suất nhân viên.
    """,
    "author": "Tuấn Rang Cà Phê",
    "website": "https://coffeetree.vn",
    "category": "AI",
    "depends": ["base", "mail"],
    'external_dependencies': {
        'python': ['google-generativeai'],
    },
    "data": [],
    "license": "LGPL-3",
    "installable": True,
    'application': True,
}
