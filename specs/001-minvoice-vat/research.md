# Research: Xuất Hóa Đơn Điện Tử VAT qua MInvoice

**Branch**: `001-minvoice-vat` | **Date**: 2026-03-02

## MInvoice API Integration

**Decision**: Sử dụng MInvoice REST API (InvoiceApi78/Save) với Bearer token authentication.  
**Rationale**: Đây là API đang chạy ổn định trong codebase hiện tại (`trcf_minvoice`). Endpoint đã được verify với dữ liệu thực.  
**Alternatives considered**: Không xem xét thay đổi nhà cung cấp — MInvoice đã được ký hợp đồng.

| Thông tin | Giá trị |
|-----------|---------|
| Login endpoint | `https://{tax_code}.minvoice.app/api/Account/Login` |
| Save invoice endpoint | `https://{tax_code}.minvoice.app/api/InvoiceApi78/Save` |
| Get series endpoint | `https://{tax_code}.minvoice.app/api/Invoice68/GetTypeInvoiceSeries` |
| Auth method | Bearer Token (JWT, thời hạn không xác định — phát hiện qua HTTP 401) |
| Timeout | 30 giây per request |
| Success response | `{ "ok": true, "code": "00", "data": { "sobaomat": "..." } }` |

## Token Lifecycle Management

**Decision**: Token được lấy thủ công qua nút "Lấy Token" trong Settings. Khi batch phát hiện token hết hạn (HTTP 401), dừng batch ngay và hướng dẫn kế toán lấy lại token.  
**Rationale**: Auto-refresh phức tạp và có thể ẩn lỗi. Dừng sớm + hướng dẫn rõ ràng là UX tốt hơn cho F&B operation. (Quyết định từ clarify Q4)  
**Alternatives considered**: Auto-refresh 1 lần — bị loại bỏ do tăng complexity mà không được yêu cầu.

## Batch Processing Architecture

**Decision**: Sequential batch processing — xử lý từng đơn một, commit sau mỗi đơn, dừng nếu gặp token error.  
**Rationale**:
- Tránh duplicate invoice nếu commit transaction dở chừng
- OWL component cập nhật UI realtime sau mỗi đơn qua RPC call riêng (pattern: `action_rpc_process_line`)
- Auto-skip đơn đã có sobaomat (clarify Q1)
**Alternatives considered**: Parallel batch — bị loại vì MInvoice API có thể có rate limit và sequential dễ debug hơn.

## Public VAT Form Security

**Decision**: Public form (`/vat_info_form/<ref>`) không cần authentication. Bảo vệ bằng: (1) chặn form khi đơn đã có sobaomat (clarify Q3), (2) `csrf=False` có justification vì là public form.  
**Rationale**: Khách hàng F&B không có Odoo account. Mức độ nhạy cảm của thông tin VAT không yêu cầu strong auth. Rủi ro chính là sửa thông tin VAT sau khi đã phát hành — được giải quyết bằng form lock.  
**Alternatives considered**: OTP verification — bị loại bỏ vì tăng friction không cần thiết trong F&B context.

## VAT Type Handling

**Decision**: 3 loại khách (`vat_type`): `company` (doanh nghiệp), `individual` (cá nhân), `no_vat` (vãng lai).  
**Rationale**: Phản ánh đúng quy định hóa đơn điện tử VN. `no_vat` xuất hóa đơn ẩn danh (buyer = "khách không lấy hoá đơn").

| Loại | Trường bắt buộc |
|------|----------------|
| company | MST, tên công ty, địa chỉ |
| individual | Tên, CCCD hoặc hộ chiếu |
| no_vat | Không cần (ẩn danh) |

## VAT Rate

**Decision**: Mặc định 8% VAT (`ma_thue: 8`) cho tất cả sản phẩm.  
**Rationale**: Phù hợp với quy định hiện hành cho F&B tại VN (Nghị định 44/2023).  
**Alternatives considered**: Per-product tax rate — deferred cho roadmap tương lai nếu có sản phẩm miễn thuế.

## Odoo Model Approach

**Decision**: Dùng `_inherit` để mở rộng `pos.order` và `res.config.settings`. Wizard dùng `TransientModel` với OWL component.  
**Rationale**: Đây là Odoo 19 pattern chuẩn — không modify core tables, không break existing functionality. Module hiện tại đã có pattern này và chạy ổn.

## Time Limit for Issuing VAT

**Decision**: Không giới hạn thời gian trong ứng dụng.  
**Rationale**: Kế toán F&B thường xuất VAT theo batch cuối ngày/tuần. MInvoice đã có cơ chế kiểm soát phía API. Kế toán tự chịu trách nhiệm compliance. (Quyết định từ clarify Q2)
