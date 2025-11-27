# TRCF Inventory Check Template

Module quản lý mẫu phiếu kiểm kho cho hệ thống Odoo.

## Tính năng

- **Tạo mẫu phiếu kiểm kho**: Định nghĩa sẵn danh sách sản phẩm cần kiểm cho từng kho/vị trí
- **Chọn đơn vị tính tùy chỉnh**: Mỗi sản phẩm có thể có đơn vị tính khác với đơn vị mặc định
- **Sắp xếp thứ tự**: Sắp xếp sản phẩm theo vị trí vật lý để kiểm kho thuận tiện
- **Tái sử dụng**: Sử dụng lại mẫu phiếu cho các lần kiểm kho sau

## Cài đặt

1. Copy module vào thư mục `addons`
2. Cập nhật danh sách module trong Odoo
3. Cài đặt module "TRCF Inventory Check Template"

## Sử dụng

### Tạo mẫu phiếu kiểm kho

1. Vào menu **TRCF INVENTORY TEMPLATE** > **Mẫu Phiếu Kiểm Kho**
2. Nhấn **Tạo mới**
3. Nhập thông tin:
   - **Tên phiếu kiểm**: Ví dụ "Phiếu kiểm kho chính", "Phiếu kiểm quầy"
   - **Kho/Vị trí**: Chọn kho cần kiểm
4. Thêm sản phẩm vào danh sách:
   - Chọn sản phẩm
   - Chọn đơn vị tính (có thể khác đơn vị mặc định)
   - Điều chỉnh thứ tự nếu cần
5. Lưu mẫu phiếu

### Tích hợp với module khác

Module này được thiết kế để tích hợp với các module kiểm kho khác. Các module khác có thể:

- Load danh sách template: `request.env['trcf.inventory.check.template'].search([])`
- Lấy chi tiết sản phẩm từ template: `template.line_ids`

## Cấu trúc dữ liệu

### Model: `trcf.inventory.check.template`
- `name`: Tên phiếu kiểm
- `location_id`: Kho/vị trí
- `line_ids`: Danh sách sản phẩm
- `active`: Trạng thái hoạt động
- `note`: Ghi chú

### Model: `trcf.inventory.check.template.line`
- `template_id`: Phiếu kiểm
- `product_id`: Sản phẩm
- `uom_id`: Đơn vị tính
- `sequence`: Thứ tự hiển thị

## Tác giả

Tuấn Rang Cà Phê

## Giấy phép

LGPL-3
