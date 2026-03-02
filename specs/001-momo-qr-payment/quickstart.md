# Quickstart: Test Scenarios for MoMo QR Payment

**Branch**: `001-momo-qr-payment` | **Date**: 2026-03-02

## Prerequisites

1. Module `trcf_payment_momo` installed in Odoo 19
2. Tài khoản MoMo Business (M4B) với Partner Code, Access Key, Secret Key
3. MoMo sandbox account để test: `https://test-payment.momo.vn`
4. Odoo server có public URL (hoặc ngrok tunnel cho local dev để test IPN)

---

## Scenario 1: Cấu Hình MoMo Payment Method

```
1. Vào POS → Settings → Payment Methods → Tạo mới
2. Chọn "Use Payment Terminal" = "TRCF MOMO QR"
3. Bật "Chế độ Test" (sandbox)
4. Nhập: Partner Code, Access Key, Secret Key từ M4B sandbox
5. (Tuỳ chọn) Upload ảnh QR tĩnh làm backup
6. Save → Gán vào POS config
Expected: Payment Method được lưu, Secret Key hiển thị dạng ****
```

---

## Scenario 2: Thanh Toán MoMo Thành Công (Happy Path - IPN)

```
1. Mở POS → Thêm sản phẩm 50,000đ → Vào màn hình Payment
2. Chọn "MoMo" làm phương thức thanh toán
Expected: Loading spinner xuất hiện → QR động hiển thị trong vòng 5 giây
3. Dùng app MoMo sandbox quét QR → Xác nhận thanh toán
Expected (trong vòng 10 giây):
  - MoMo gửi IPN về /momo/ipn
  - Signature được verify thành công
  - Transaction cập nhật status=success
  - Bus notification gửi đến POS
  - Màn hình POS hiển thị dấu tích xanh
  - Đơn hàng tự động validate, in biên lai
```

---

## Scenario 3: Thanh Toán MoMo Thành Công (Polling Recover)

```
Simulate: Chặn /momo/ipn (e.g. tắt webhook trong MoMo sandbox hoặc test local)
1. Thực hiện giống Scenario 2, khách quét QR và thanh toán
Expected (trong vòng 3-6 giây):
  - IPN không đến (blocked)
  - JS polling gọi /pos/momo/check_payment_status sau 3s
  - API trả về result_code=0
  - Transaction cập nhật success
  - POS nhận tín hiệu qua polling result → auto validate
```

---

## Scenario 4: IPN Chữ Ký Không Hợp Lệ (Security Test)

```
Simulate: Gửi POST request giả mạo đến /momo/ipn với signature sai
  curl -X POST http://localhost:8069/momo/ipn \
    -H "Content-Type: application/json" \
    -d '{"orderId":"fake-order","resultCode":0,"signature":"invalid"}'
Expected:
  - Server trả về 204 No Content (không process)
  - Log warning: "MoMo IPN: Signature mismatch for order fake-order"
  - Transaction KHÔNG được cập nhật
  - Polling tiếp tục chạy bình thường (nếu có giao dịch thật)
```

---

## Scenario 5: Fallback QR Tĩnh (API Thất Bại)

```
1. Xóa Partner Code trong Payment Method config → Save
2. Mở POS → Chọn MoMo
Expected:
  - Không có spinner, không có crash
  - Hiển thị QR tĩnh đã upload (hoặc placeholder SVG mặc định)
  - Không có error dialog
3. Thu ngân nhận tiền thủ công → xác nhận payment line
Expected: Đơn hàng validate thành công
```

---

## Scenario 6: Timeout 5 Phút → Tạo QR Mới

```
1. Mở POS → Chọn MoMo → QR hiển thị
2. Chờ 5 phút không thanh toán (hoặc mock: giảm maxPolls xuống 2 để test nhanh)
Expected:
  - Polling dừng sau 100 lần (5 phút)
  - Banner hiển thị: "QR đã hết hiệu lực sau 5 phút"
  - Nút "Tạo QR Mới" xuất hiện
3. Nhấn "Tạo QR Mới"
Expected: API tạo QR mới, QR mới hiển thị, polling bắt đầu lại
```

---

## Scenario 7: Không Duplicate Validate

```
1. Mở POS → Chọn MoMo → Khách thanh toán
2. Cả IPN và polling đều báo success cùng lúc
Expected:
  - POS nhận notification/polling success
  - Đơn hàng validate 1 lần duy nhất
  - Không có lỗi "Order already paid" hay validate kép
  - Guard: kiểm tra order.state === 'draft' trước khi validateOrder()
```

---

## Error Cases

| Tình huống | Action | Expected |
|-----------|--------|---------|
| Internet cut trong khi tạo QR | Chọn MoMo → API fail | Fallback QR tĩnh hoặc placeholder |
| MoMo API 5xx error | Chọn MoMo | Error message, fallback QR |
| momo_order_id trùng (nếu xảy ra) | Tạo 2x QR liên tục | suffix uuid đảm bảo unique |
| Đơn POS có ký tự đặc biệt (e.g. "Đặc biệt") | Chọn MoMo | orderId được sanitize, API call thành công |
