# Odoo 19 Best Practices (TRCF Wisdom)

Tài liệu này lưu trữ những "bí kíp" và kinh nghiệm thực chiến giúp viết code Odoo 19 tối ưu hơn.

## 1. Tối ưu Truy vấn
- Luôn ưu tiên dùng `_read_group` cho các báo cáo hoặc thống kê thay vì loop qua records.
- Sử dụng `filtered()` và `mapped()` của Odoo thay vì list comprehension của Python khi làm việc với Recordsets.

## 2. Trải nghiệm người dùng (UX)
- **Statusbar**: Luôn để các trạng thái quan trọng hiển thị trên statusbar để người dùng biết họ đang ở đâu.
- **Chatter**: Mọi model có quy trình nghiệp vụ (Order, Inventory...) bắt buộc phải có Chatter để lưu vết.

## 3. Cấu trúc Code
- **Compute Fields**: Nên luôn có `store=True` nếu field đó được dùng để lọc hoặc tìm kiếm.
- **Multi-company**: Luôn thêm field `company_id` và áp dụng security rule để hỗ trợ đa công ty.

*(Cập nhật thêm trong quá trình làm việc...)*
