# MOMO Payment Terminal for Odoo 19

## Cài đặt Module

1. Copy toàn bộ folder `momo_payment_terminal` vào thư mục addons của Odoo
2. Restart Odoo server
3. Vào Apps → Update Apps List
4. Tìm kiếm "MOMO Payment Terminal" và cài đặt

## Cấu hình Payment Method

1. Vào **Point of Sale → Configuration → Payment Methods**
2. Click **New** để tạo payment method mới
3. Điền thông tin:
   - **Name**: MOMO Payment
   - **Journal**: Chọn journal phù hợp (Bank hoặc Cash)
   - **Use a Payment Terminal**: Chọn **MOMO**
   
4. Trong phần **MOMO Configuration**:
   - **MOMO Merchant ID**: Nhập mã merchant của bạn
   - **MOMO Phone Number**: Số điện thoại nhận tiền MOMO
   - **MOMO QR Code Image**: Upload ảnh QR code của bạn

## Tạo QR Code

### Cách 1: Sử dụng script có sẵn
```bash
cd /path/to/momo_payment_terminal
python3 generate_qr.py
```

### Cách 2: Tạo QR code từ MOMO Business
1. Đăng nhập MOMO Business
2. Tạo QR code tĩnh cho merchant
3. Download và upload vào Odoo

### Cách 3: Sử dụng QR code online generator
Tạo QR với format:
```
2|99|[SĐT]|[TÊN]|[EMAIL]|0|0|[SỐ TIỀN]|[NỘI DUNG]|transfer|
```

## Gán cho POS

1. Vào **Point of Sale → Configuration → Point of Sale**
2. Chọn POS config của bạn
3. Trong tab **Payment Methods**, thêm "MOMO Payment" vào danh sách

## Sử dụng trong POS

1. Mở POS session
2. Tạo đơn hàng
3. Khi thanh toán, chọn **MOMO Payment**
4. Popup hiển thị:
   - QR code để khách quét
   - Số tiền cần thanh toán
   - Thông tin merchant
   - Đếm ngược 60 giây

5. Sau khi khách thanh toán:
   - Click **Xác nhận đã thanh toán** để hoàn tất
   - Hoặc **Hủy thanh toán** để chọn phương thức khác

## Tùy chỉnh

### Thay đổi thời gian timeout
Trong file `payment_momo.js`, dòng 88:
```javascript
countdown: 60, // Thay đổi số giây tại đây
```

### Thay đổi màu sắc MOMO
Trong file `payment_momo.css`, tìm color `#b0006d` và thay đổi theo ý muốn

### Tích hợp API thực tế
Để tích hợp với MOMO API thực:

1. Trong `payment_momo.js`, function `_showMomoPayment()`:
```javascript
// Thay vì simulate, gọi API thực
const response = await this.env.services.rpc({
    model: 'pos.payment',
    method: 'process_momo_payment',
    args: [line.amount, orderId],
});
```

2. Tạo backend method trong Python:
```python
@api.model
def process_momo_payment(self, amount, order_id):
    # Gọi MOMO API
    # Return status
    pass
```

## Lưu ý

- Module này hiện tại chỉ simulate payment
- Để tích hợp thực tế, cần:
  - MOMO Business account
  - API credentials
  - SSL certificate cho production
  - Implement webhook để nhận notification

## Support

Nếu cần hỗ trợ, vui lòng liên hệ:
- Email: support@yourcompany.com
- Documentation: https://your-docs.com
