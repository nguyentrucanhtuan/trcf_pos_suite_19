# Skill: Phát triển Odoo 19 Standard Module (TRCF Style)

Kỹ năng này hướng dẫn Antigravity cách viết code chuẩn Odoo 19 cho hệ thống của Tuấn Rang Cà Phê.

## 🎯 Mục tiêu
- Tạo ra code sạch, dễ bảo trì, tuân thủ đúng kiến trúc Odoo 19.
- Luôn sử dụng phong cách đặc trưng của dự án (TRCF).

## 🐍 Python Style
- **Model Name**: Luôn bắt đầu bằng `trcf.`. Ví dụ: `trcf.inventory.check`.
- **Field Conventions**:
    - `name`: Luôn có `required=True` và `index=True`.
    - `active`: Luôn có để hỗ trợ Archive.
    - `state`: Luôn dùng Selection với các giá trị: `draft`, `confirmed`, `done`, `cancelled`.
    - `tracking=True`: Sử dụng cho các trường quan trọng để lưu log vào Chatter.
- **Methods**:
    - Sử dụng `@api.model_create_multi` cho hàm `create`.
    - Các hàm xử lý trạng thái bắt đầu bằng `action_` (ví dụ: `action_confirm`).
    - Luôn có Docstring bằng tiếng Việt mô tả ngắn gọn mục đích.

## 📄 XML / UI Style
- **Odoo 19 List View**: 
    - Tuyệt đối không dùng thẻ `<tree>`, phải dùng `<list>`.
    - Thêm `decoration-info`, `decoration-success` dựa trên `state`.
- **Form View**:
    - Cấu trúc: `<header>` (chứa buttons & statusbar) -> `<sheet>` -> `<div class="oe_title">` -> `<group>`.
    - Luôn tích hợp Chatter (`oe_chatter`) ở cuối Form.
- **Search View**: Luôn có các bộ lọc mặc định và Group By cho `state` và `date`.

## 📁 File Structure
- Luôn tuân thủ template trong `.agent/templates/odoo19_standard/`.
- Tách biệt logic theo folder: `models/`, `views/`, `security/`, `static/`.

## ⚠️ Check & Fix
- Khi gặp lỗi, hãy đối chiếu với `context_odoo19/troubleshooting.md`.
- Tuyệt đối không dùng `attrs` (đã bị bỏ trong Odoo 19), hãy dùng trực tiếp `invisible`, `readonly`, `required` với điều kiện trực tiếp trong XML.

## 💡 Tư duy Logic
- Hạn chế viết logic nặng trong Controller, hãy đưa vào Model (`models.py`) để tái sử dụng.
- Luôn kiểm tra quyền truy cập (`ir.model.access.csv`) sau khi tạo model mới.
