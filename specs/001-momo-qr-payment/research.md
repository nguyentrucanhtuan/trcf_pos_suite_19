# Research: Tích Hợp Thanh Toán MoMo QR vào Odoo 19 POS

**Branch**: `001-momo-qr-payment` | **Date**: 2026-03-02

## MoMo API v3 Integration

**Decision**: Sử dụng MoMo Business API v3 (M4B) — endpoint `create` tạo payment request, `query` kiểm tra trạng thái.  
**Rationale**: Đây là API đang chạy ổn định trong codebase hiện tại. M4B cung cấp Partner Code, Access Key, Secret Key để ký HMAC-SHA256.  
**Alternatives considered**: MoMo QR tĩnh — không đảm bảo đúng số tiền, không có webhook confirmation.

| Thông tin | Giá trị |
|-----------|---------|
| Production endpoint | `https://payment.momo.vn/v2/gateway/api/create` |
| Sandbox endpoint | `https://test-payment.momo.vn/v2/gateway/api/create` |
| Query endpoint | `/v2/gateway/api/query` |
| Auth method | HMAC-SHA256 signature (raw string alphabetical order) |
| Request type | `payWithMethod` hoặc `captureWallet` |
| Response | `qrCodeUrl` (deep link để render QR), `resultCode=0` = success |

## QR Code Rendering — Local Library

**Decision**: Dùng thư viện JavaScript `qrcode` (npm `qrcode-svg` hoặc CDN-free `qrcode.js`) để render QR code từ deeplink URL trực tiếp trên browser — không cần server roundtrip, không phụ thuộc `quickchart.io`.  
**Rationale**: Giải quyết Q3 từ clarify — hoàn toàn offline-capable, không có single point of failure external. QR render client-side nhanh hơn HTTP call.  
**Alternatives considered**: `quickchart.io` (external, cần internet, single point of failure) → loại bỏ. Server-side Python `qrcode` library → phức tạp hơn cần thiết.

## Dual Confirmation: IPN + Polling

**Decision**: Song song 2 cơ chế: (1) MoMo webhook IPN → cập nhật transaction → bus notification → POS; (2) JS polling mỗi 3 giây → query status API → cập nhật nếu success.  
**Rationale**: IPN nhanh nhất nhưng phụ thuộc public URL. Polling là backup đảm bảo không mất giao dịch kể cả khi IPN bị chặn (localhost dev, firewall). Duplicate guard bằng `order.state !== 'draft'`.  
**Alternatives considered**: Chỉ dùng polling — trễ tối đa 3s, tệ hơn IPN. Chỉ dùng IPN — mất giao dịch nếu webhook bị block.

## IPN Security: Strict HMAC Validation

**Decision**: IPN phải qua HMAC-SHA256 validation. Nếu chữ ký không khớp → trả 204, ghi log, không cập nhật transaction. Polling tiếp tục làm backup recovery.  
**Rationale**: Giải quyết Q2 từ clarify — bảo mật quan trọng hơn khả năng xử lý IPN không có chữ ký. Polling đảm bảo giao dịch hợp lệ vẫn được confirm.  
**Signature raw string format (MoMo v3)**:
```
accessKey=...&amount=...&extraData=...&message=...&orderId=...&orderInfo=...
&orderType=...&partnerCode=...&payType=...&requestId=...&responseTime=...
&resultCode=...&transId=...
```

## Timeout UX: Nút "Tạo QR Mới"

**Decision**: Sau 5 phút (100 × 3s), polling dừng, POS hiển thị thông báo "QR đã hết hiệu lực" + nút "Tạo QR Mới". Thu ngân nhấn để tạo lại QR mới cho cùng đơn.  
**Rationale**: Giải quyết Q1 từ clarify — UX rõ ràng hơn là âm thầm để QR expired. Webhook IPN vẫn có thể đến sau timeout nếu khách đã quét trước.  
**Implementation**: OWL reactive state `momoState.isExpired = true` sau khi polling kết thúc mà chưa success. Template hiển thị banner expired + button trigger `createNewMomoPayment()`.

## Bus Notification Channel — Odoo 19 Pattern

**Decision**: Sử dụng `config.access_token` làm channel identifier. Notification name: `{access_token}-MOMO_PAYMENT_SUCCESS`.  
**Rationale**: Đây là pattern Odoo 19 POS chuẩn — mỗi POS config có unique access_token, tránh cross-terminal notification. Đúng với `getOnNotified()` API.  
**Implementation**: `bus.bus._sendone(channel, notification_name, payload)` từ Python transaction model.

## Transaction Record Pattern

**Decision**: Mỗi lần tạo QR → tạo 1 `trcf.momo.transaction` record ngay lập tức (không đợi payment). Liên kết với `pos_session_id` và `pos_config_id` để gửi bus đúng kênh.  
**Rationale**: Tránh race condition: nếu IPN đến trước JS tạo transaction, có thể bị "not found". Tạo sớm ngay sau khi API thành công đảm bảo IPN luôn match được record.

## Refund Policy

**Decision**: Hoàn tiền MoMo nằm ngoài phạm vi module này (Q4 từ clarify). Module chỉ xử lý payment một chiều.  
**Rationale**: MoMo Refund API phức tạp hơn, cần spec riêng. Odoo refund order flow cần được xem xét riêng.
