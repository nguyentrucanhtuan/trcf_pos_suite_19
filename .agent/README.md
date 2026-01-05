# Hệ thống Hỗ trợ Phát triển Odoo 19 (Antigravity Agent)

Tài liệu này hướng dẫn cách sử dụng bộ công cụ hỗ trợ phát triển Odoo 19 Standard cho dự án Tuấn Rang Cà Phê (TRCF). Hệ thống này được thiết kế để áp dụng trí tuệ nhân tạo vào quy trình lập trình, đảm bảo code luôn sạch, chuẩn và nhất quán.

## 🏗 Cơ chế Hoạt động (How it works)

Hệ thống hoạt động dựa trên sự phối hợp của 4 tầng lớp:

1.  **Context (Tri thức)**: Lưu trữ các bản tham chiếu kỹ thuật về Odoo 19 (ORM, Views, OWL). Khi bạn yêu cầu code, Agent sẽ "đọc" các file này để biết cú pháp Odoo 19 đúng.
2.  **Skills (Kỹ năng)**: Chứa các quy chuẩn riêng của dự án TRCF (Prefix `trcf_`, ngôn ngữ Tiếng Việt, chuẩn bảo mật). Đây là bộ lọc để Agent không vi phạm quy tắc dự án.
3.  **Workflows (Quy trình)**: Các kịch bản tự động hóa (Slash commands) giúp thực hiện các tác vụ phức tạp bằng một lệnh duy nhất.
4.  **Templates (Mẫu)**: Các bộ khung file chuẩn để Agent sinh code nhanh và chính xác.

---

## 🔄 Cơ chế Tự học (The Learning Loop)

Để hệ thống ngày càng thông minh, Antigravity sẽ tự động thực hiện:

- **Cập nhật Lỗi**: Khi gặp một lỗi mới và fix xong, Agent sẽ tự viết vào `context_odoo19/troubleshooting.md`.
- **Ghi lại Kinh nghiệm**: Các mẹo code hay hoặc kiến trúc tối ưu sẽ được lưu vào `context_odoo19/best_practices.md`.
- **Tinh chỉnh Skill**: Nếu một quy tắc code không còn phù hợp, Agent sẽ kiến nghị bạn cập nhật `skills/odoo19_standard.md`.

---

## 🚀 Các lệnh Slash Commands (Workflows)

### 1. `/trcf_module_create`
Dùng khi bạn muốn khởi tạo một module mới từ đầu.
- **Cách dùng**: `/trcf_module_create [tên_module] "[mô_tả]"`
- **Ví dụ**: `/trcf_module_create coffee_management "Quản lý kho hạt cà phê và rang xay"`
- **Kết quả**: Agent sẽ tạo folder `trcf_coffee_management` với đầy đủ cấu hình Security, Model, View và Menu chuẩn Odoo 19.

### 2. `/trcf_module_optimize`
Dùng để "dọn dẹp" và nâng cấp code hiện có.
- **Cách dùng**: `/trcf_module_optimize [path_to_module]`
- **Ví dụ**: Hãy tối ưu module này `/trcf_module_optimize custom_addons/trcf_old_module`
- **Kết quả**: Agent sẽ tự động chuyển thẻ `<tree>` -> `<list>`, xóa `attrs`, cập nhật `@api.model_create_multi` và dịch toàn bộ nhãn sang Tiếng Việt.

### 3. `/trcf_create_owl_component`
Dùng để tạo nhanh các thành phần giao diện OWL.
- **Cách dùng**: `/trcf_create_owl_component [tên_component]`
- **Ví dụ**: `/trcf_create_owl_component pos_receipt_custom`
- **Kết quả**: Agent tạo file `.js` (ESM) và `.xml` (Template), đồng thời tự động đăng ký vào `__manifest__.py`.

### 4. `/trcf_create_adk_agent`
Dùng để tạo một AI Agent mới sử dụng Google ADK tích hợp vào Odoo Discuss.
- **Cách dùng**: `/trcf_create_adk_agent [tên_agent] "[mô_tả_nhiệm_vụ]"`
- **Ví dụ (Prompt mẫu)**: 
    - `@[/trcf_create_adk_agent] marketing_bot "Trợ lý viết nội dung quảng cáo facebook dựa trên thông tin sản phẩm và khách hàng mục tiêu"`
    - `@[/trcf_create_adk_agent] inventory_analyst "Trợ lý phân tích tồn kho, cảnh báo các mặt hàng sắp hết hàng"`
- **Kết quả**: Agent tạo cấu trúc thư mục chuẩn, đăng ký registry, cấu hình hook Discuss và **tự động chạy lệnh nâng cấp module** để áp dụng thay đổi ngay.

---

## 🧠 Mẹo dành cho Developer (Tips)

- **Kích hoạt "Bộ não"**: Khi bắt đầu một task mới, bạn có thể nhắc Agent: *"Hãy tham chiếu Skill odoo19_standard và các Context liên quan trước khi thực hiện"*.
- **Review Code**: Sau khi Agent viết code xong, hãy hỏi: *"Code này đã tuân thủ đúng Checklist Sạch Code trong Skill chưa?"* để Agent tự rà soát lỗi.
- **Cập nhật tri thức**: Nếu Odoo 19 có bản cập nhật mới, hãy dán link doc vào và yêu cầu Agent tự cập nhật thư mục `context_odoo19/`.

---
**Duy trì bởi**: Antigravity x Tuấn Rang Cà Phê
**Phiên bản**: 1.1 (Odoo 19 Standard - Enhanced)
