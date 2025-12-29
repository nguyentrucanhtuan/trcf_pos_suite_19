# Skill: Phát triển Odoo 19 Standard Module (TRCF Standard)

Kỹ năng này định hình cách Antigravity viết code cho dự án Tuấn Rang Cà Phê (TRCF), áp dụng các tiêu chuẩn mới nhất của Odoo 19.

## 🎯 Tư duy Thiết kế (Mindset)
- **Chuẩn Odoo 19**: Tuyệt đối không dùng code legacy. Ưu tiên `<list>`, reactive OWL, và Python expression modifiers.
- **Tính đóng gói**: Một module phải "chạy được ngay" sau khi cài đặt (đầy đủ Data, Security, Action, Menu).
- **Ngôn ngữ**: Toàn bộ nhãn hiển thị (string), thông báo lỗi và Docstring phải bằng **tiếng Việt**.

## 🐍 Quy tắc Python (Backend)
- **Model Definition**: 
    - Prefix: `trcf.`.
    - Phải có `_description`.
    - Trình tự: Attributes (`_name`, `_inherit`...) -> Fields -> Constrains -> Compute methods -> CRUD overrides -> Action methods.
- **Fields Reference**:
    - `name`: Luôn là `required=True`, `index=True` và `tracking=True`.
    - `state`: Luôn là `Selection` với widget `statusbar` trong View.
    - `active`: Thêm vào để hỗ trợ Archive nếu cần.
    - `Many2one`: Luôn cân nhắc `ondelete='restrict'` hoặc `'cascade'`.
- **ORM Style**: 
    - Sử dụng `self.env` để truy cập `user`, `company`, `context`. Không dùng `self._uid` hay `self._context`.
    - Overrides: Luôn dùng `@api.model_create_multi` cho `create`.
    - Method naming: Logic nghiệp vụ bắt đầu bằng `action_`, logic nội bộ hoặc API riêng dùng `@api.private`.
- **Error Handling**: Sử dụng `odoo.exceptions.ValidationError` hoặc `UserError` với nội dung tiếng Việt rõ ràng.

## 📄 Quy tắc XML / UI Style (Frontend)
- **Views**:
    - List View: Dùng thẻ `<list>`, không dùng `<tree>`. Thêm các thuộc tính trang trí `decoration-X`.
    - Form View: Cấu trúc bắt buộc Header -> Sheet (Title -> Group -> Notebook) -> Chatter.
    - Modifiers: Dùng trực tiếp `invisible`, `readonly`, `required` với logic Python (VD: `invisible="state == 'done'"`).
- **Control Panel**: Luôn định nghĩa Search View với đầy đủ bộ lọc hữu ích cho người dùng TRCF.
- **Menu Hierarchy**: Tuân thủ cấu trúc Menu của dự án, tránh tạo Menu rác ở Root.

## 📁 File Structure & Manifest
- **__manifest__.py**: 
    - `name`: Bắt đầu bằng `trcf_`.
    - `license`: Bắt buộc là `LGPL-3`.
    - `depends`: Luôn khai báo đủ các module phụ thuộc (VD: `base`, `mail`, `product`).
    - `data`: Liệt kê theo thứ tự: Security -> Data -> Views -> Reports.
- **Security**: File `ir.model.access.csv` phải đầy đủ quyền cho `base.group_user`.

## ⚙️ OWL & Assets
- Sử dụng **ESM (import/export)**.
- Đăng ký assets trong `__manifest__.py` dưới key `assets`.
- Sử dụng `setup()` và các hooks (`useState`, `onWillStart`) thay cho constructor cũ.

## ⚠️ Checklist "Sạch Code"
1. Đã xóa code thừa/comment trống chưa?
2. Docstring đã mô tả bằng tiếng Việt chưa?
3. Các field số tiền đã dùng `Monetary` kèm field tiền tệ chưa?
4. Đã có file `__init__.py` ở tất cả các folder con (`models`, `controllers`...) chưa?
