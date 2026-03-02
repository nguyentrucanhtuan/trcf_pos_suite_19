# Quickstart: Test Scenarios for MInvoice VAT

**Branch**: `001-minvoice-vat` | **Date**: 2026-03-02

## Prerequisites

1. Module `trcf_minvoice` installed in Odoo 19
2. Ít nhất 1 đơn POS ở trạng thái `paid` hoặc `done`
3. Credentials MInvoice (test account):
   - MST: `[từ MInvoice sandbox]`
   - Username / Password: `[từ MInvoice sandbox]`

---

## Scenario 1: Cấu Hình MInvoice trong Settings

```
1. Vào Settings → Accounting (hoặc tìm "MInvoice")
2. Điền Mã số thuế, Username, Password
3. Nhấn "Lấy Token" → Expected: thông báo "✅ Lấy token thành công"
4. Nhấn "Lấy Series" → Expected: ký hiệu hóa đơn tự động điền (e.g., "1C25MYY")
5. Điền Tên cửa hàng, Save
6. Kiểm tra: API Token hiển thị dạng "...LAST15CHARS"
```

---

## Scenario 2: Khách Tự Điền Thông Tin VAT (Doanh Nghiệp)

```
1. Lấy mã đơn hàng POS (e.g., "POS/0001-001")
2. Truy cập từ trình duyệt ẩn danh: http://localhost:8069/vat_info_form/POS/0001-001
3. Chọn loại "Doanh nghiệp"
4. Điền: MST = "0123456789", Tên công ty = "Công ty Test", Địa chỉ, Email
5. Submit → Expected: trang "Cảm ơn"
6. Kiểm tra backend: đơn POS/0001-001 có vat_type=company và thông tin đã lưu
```

---

## Scenario 3: Xuất VAT Đơn Lẻ từ Backend

```
1. Vào TRCF VAT → Hoá đơn chờ xuất VAT
2. Lọc "Hôm nay", tìm đơn đã điền thông tin VAT ở Scenario 2
3. Chọn đơn → Nhấn "Phát hành hoá đơn" (header button)
4. Wizard mở → nhấn nút bắt đầu
5. Dòng đơn chuyển: Chờ → Đang xử lý → Thành công
6. Expected: vat_code hiển thị (sobaomat), đơn đổi sang màu xanh trong danh sách
```

---

## Scenario 4: Xuất VAT Hàng Loạt (Batch)

```
1. Chuẩn bị 3 đơn POS đã thanh toán (chưa xuất VAT)
2. Vào TRCF VAT → Hoá đơn chờ xuất VAT
3. Chọn cả 3 đơn → Nhấn "Phát hành hoá đơn"
4. Wizard hiện 3 dòng trạng thái Chờ
5. Expected: từng dòng lần lượt chuyển Đang xử lý → Thành công
6. Expected: thống kê cuối: Total=3, Success=3, Failed=0, Skipped=0
```

---

## Scenario 5: Auto-Skip Đơn Đã Xuất VAT

```
1. Chọn 2 đơn: 1 đơn đã có sobaomat + 1 đơn chưa xuất
2. Nhấn "Phát hành hoá đơn"
3. Expected: wizard hiện 2 dòng — đơn đã có sobaomat status = Skipped ngay lập tức
4. Expected: thống kê: Total=2, Success=1, Skipped=1
```

---

## Scenario 6: Token Hết Hạn (Simulate)

```
1. Vào Settings → xóa/thay đổi API Token thành giá trị invalid
2. Chọn 3 đơn chưa xuất → nhấn "Phát hành hoá đơn"
3. Expected: dòng đầu tiên → Đang xử lý → Failed (HTTP 401)
4. Expected: wizard dừng ngay, hiển thị hướng dẫn "Token hết hạn, vào Settings → Lấy Token"
5. Expected: 2 đơn còn lại giữ trạng thái Chờ (không bị mark Failed)
```

---

## Scenario 7: Lock Form Sau Khi Xuất VAT

```
1. Dùng đơn đã xuất VAT thành công từ Scenario 3
2. Truy cập lại: http://localhost:8069/vat_info_form/POS/0001-001
3. Expected: form hiển thị nhưng bị khóa (read-only)
4. Expected: thông báo "Hóa đơn đã được phát hành, không thể chỉnh sửa thông tin"
```

---

## Error Cases để Test

| Tình huống | Action | Expected |
|-----------|--------|---------|
| Cấu hình thiếu Token | Nhấn "Phát hành hoá đơn" | Cảnh báo thiếu cấu hình, không mở wizard |
| Mã đơn không tồn tại | GET /vat_info_form/INVALID | Trang lỗi thân thiện |
| API MInvoice timeout | Mock timeout 30s | Dòng chuyển Failed + "Timeout Error" |
