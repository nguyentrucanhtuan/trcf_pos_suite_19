# Feature Specification: Tích Hợp Thanh Toán MoMo QR vào Odoo 19 POS

**Feature Branch**: `001-momo-qr-payment`
**Created**: 2026-03-02
**Status**: Draft
**Input**: User description: "Tích hợp thanh toán MoMo QR vào Odoo 19 POS cho chuỗi F&B tại Việt Nam."

---

## Clarifications

### Session 2026-03-02

- Q: Sau 5 phút polling hết thời gian mà khách chưa thanh toán, POS làm gì? → A: Hiển thị thông báo "QR đã hết hiệu lực sau 5 phút" + nút "Tạo QR Mới" để thu ngân tạo lại QR mới cho cùng đơn hàng.
- Q: IPN đến nhưng chữ ký HMAC-SHA256 không khớp, hệ thống xử lý như thế nào? → A: Từ chối xử lý, trả về 204 No Content (không để MoMo retry), ghi log warning; polling làm backup để recover giao dịch nếu cần.
- Q: Khi `quickchart.io` không phản hồi, QR hiển thị thế nào? → A: Bỏ hoàn toàn phụ thuộc vào `quickchart.io` — render QR bằng thư viện local (không cần internet); đảm bảo QR hoạt động dù offline.
- Q: Tính năng hoàn tiền MoMo có thuộc phạm vi module này không? → A: Ngoài phạm vi — module chỉ xử lý luồng nhận tiền; hoàn tiền (bao gồm MoMo Refund API) sẽ là spec riêng biệt.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Thu Ngân Nhận Thanh Toán MoMo QR (Priority: P1)

Thu ngân chọn "MoMo" tại màn hình thanh toán POS. Hệ thống ngay lập tức gọi MoMo API để tạo mã QR động với đúng số tiền đơn hàng và hiển thị trên màn hình. Khách quét QR bằng app MoMo và xác nhận thanh toán. MoMo gửi thông báo về server Odoo, hệ thống tự động đánh dấu thanh toán thành công, màn hình POS hiển thị dấu tích xanh và tự động in biên lai — thu ngân không cần thao tác gì thêm.

**Why this priority**: Đây là tính năng cốt lõi — toàn bộ giá trị của module nằm ở việc thanh toán hoàn tất tự động. Mọi thứ khác là hỗ trợ cho luồng này.

**Independent Test**: Tạo đơn POS 100,000đ → chọn MoMo → QR hiển thị → dùng sandbox MoMo quét và thanh toán → trong vòng 10 giây, POS tự động validate đơn và in biên lai mà không cần thu ngân nhấn nút.

**Acceptance Scenarios**:

1. **Given** đơn POS 50,000đ, **When** thu ngân chọn "MoMo" làm phương thức thanh toán, **Then** hệ thống gọi MoMo API trong nền, màn hình hiển thị QR loading spinner rồi QR động đúng số tiền trong vòng 5 giây.
2. **Given** QR đang hiển thị, **When** khách quét và thanh toán thành công bằng app MoMo, **Then** trong vòng 10 giây POS nhận thông báo (qua webhook IPN hoặc polling), dòng thanh toán chuyển trạng thái "Done", hiển thị dấu tích xanh, đơn hàng tự động validate.
3. **Given** QR đang hiển thị, **When** thu ngân nhấn xóa dòng thanh toán MoMo, **Then** QR biến mất, polling dừng, đơn hàng quay về trạng thái chưa thanh toán.
4. **Given** MoMo API trả về kết quả thành công qua cả IPN lẫn polling, **When** hệ thống nhận được cả 2, **Then** đơn hàng chỉ được validate 1 lần, không bị duplicate.

---

### User Story 2 - Fallback QR Tĩnh Khi API Không Khả Dụng (Priority: P2)

Khi API MoMo chưa được cấu hình (thiếu credentials) hoặc có lỗi kết nối, thu ngân vẫn có thể nhận thanh toán MoMo bằng QR tĩnh đã upload sẵn. Thu ngân yêu cầu khách quét QR tĩnh và nhập đúng số tiền. Sau khi khách thanh toán, thu ngân xác nhận thủ công bằng cách chuyển trạng thái dòng thanh toán.

**Why this priority**: Đảm bảo liên tục hoạt động khi API gặp sự cố — không để chuỗi F&B mất giao dịch.

**Independent Test**: Để trống Partner Code → chọn MoMo → Expected: QR tĩnh (hoặc placeholder svg) hiển thị thay vì loading, không có lỗi crash.

**Acceptance Scenarios**:

1. **Given** chưa cấu hình credentials MoMo, **When** thu ngân chọn "MoMo", **Then** hệ thống hiển thị QR tĩnh đã upload (hoặc placeholder default nếu chưa upload), không hiển thị lỗi crash.
2. **Given** admin đã upload ảnh QR tĩnh trong Payment Method config, **When** API MoMo thất bại, **Then** hệ thống tự động fallback về QR tĩnh đó.
3. **Given** QR tĩnh đang hiển thị, **When** khách đã thanh toán theo QR tĩnh, **Then** thu ngân có thể xác nhận thanh toán thủ công để hoàn tất đơn.

---

### User Story 3 - Admin Cấu Hình MoMo Payment Method (Priority: P3)

Admin tạo phương thức thanh toán loại "TRCF MOMO QR" trong POS Settings, nhập Partner Code, Access Key, Secret Key từ tài khoản MoMo Business (M4B). Bật/tắt "Chế độ Test" để dùng sandbox MoMo trước khi đưa vào production. Upload ảnh QR tĩnh làm backup. Hệ thống kiểm tra rằng `web.base.url` có thể reach từ internet để MoMo IPN hoạt động.

**Why this priority**: Làm một lần duy nhất khi setup. Quan trọng nhưng không phải tính năng hàng ngày.

**Independent Test**: Vào POS → Payment Methods → Tạo method "MoMo" → chọn terminal "TRCF MOMO QR" → nhập 3 credentials → bật Test Mode → Save → vào POS, tạo đơn, chọn MoMo → API gọi thành công đến sandbox.

**Acceptance Scenarios**:

1. **Given** admin chọn terminal "TRCF MOMO QR", **When** form lưu lại, **Then** các fields cấu hình MoMo API (Partner Code, Access Key, Secret Key) và QR tĩnh backup hiển thị; Secret Key được ẩn dạng password.
2. **Given** admin bật "Chế độ Test", **When** POS gọi API tạo QR, **Then** request đến MoMo sandbox endpoint thay vì production.
3. **Given** thiếu một trong 3 credentials (Partner Code / Access Key / Secret Key), **When** thu ngân chọn MoMo trong POS, **Then** hệ thống thông báo lỗi rõ ràng và fallback về QR tĩnh.

---

### Edge Cases

- QR timeout sau 5 phút (100 lần polling × 3 giây) → polling dừng tự động, màn hình hiển thị thông báo **"QR đã hết hiệu lực sau 5 phút"** kèm nút **"Tạo QR Mới"**; thu ngân nhấn nút để tạo lại QR mới. Webhook IPN vẫn có thể đến sau (nếu khách đã quét trước lúc timeout).
- MoMo IPN đến nhưng chữ ký HMAC-SHA256 không khớp → **từ chối xử lý**, trả về 204 No Content (không retry), ghi log warning; polling tiếp tục chạy và sẽ recover giao dịch nếu đó là IPN hợp lệ bị sai format.
- MoMo IPN đến trước khi transaction record được tạo (race condition) → IPN ghi log "not found", polling sẽ recover sau.
- Cùng lúc IPN và polling đều báo success → đơn hàng chỉ validate 1 lần (guard kiểm tra `state !== 'draft'`).
- Thu ngân thoát màn hình payment rồi quay lại → polling đã bị cleanup, QR không còn hiệu lực.
- Số tiền đơn hàng tính sai do Odoo 19 reactive proxy → dùng 4 fallback methods theo thứ tự: `getTotalDue()` → `taxTotals.order_total` → `amount_total` → tính từng order line.
- Mã đơn POS chứa ký tự đặc biệt (dấu /, khoảng trắng) → sanitize bằng regex trước khi gửi lên MoMo (chỉ nhận `[0-9a-zA-Z-_.:]+`).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Khi thu ngân chọn "MoMo" trong POS, hệ thống PHẢI gọi MoMo API và trả về mã QR động trong vòng dưới 5 giây.
- **FR-002**: Mã QR PHẢI được tính toán đúng số tiền cần thanh toán (không thể sai lệch dù 1đ).
- **FR-003**: Hệ thống PHẢI lắng nghe webhook IPN từ MoMo để nhận xác nhận thanh toán realtime.
- **FR-004**: Hệ thống PHẢI polling kiểm tra trạng thái thanh toán mỗi 3 giây song song với webhook, tối đa 5 phút.
- **FR-005**: Khi thanh toán thành công (qua IPN hoặc polling), POS PHẢI tự động validate đơn hàng và in biên lai mà không cần thu ngân thao tác thêm.
- **FR-006**: Polling PHẢI dừng tự động khi: thanh toán thành công, thanh toán thất bại, hoặc thu ngân xóa dòng thanh toán MoMo.
- **FR-007**: IPN webhook PHẢI được xác thực bằng chữ ký HMAC-SHA256 theo đúng MoMo API v3 spec.
- **FR-008**: Webhook PHẢI luôn trả về 204 No Content kể cả khi có lỗi, để tránh MoMo retry vô hạn.
- **FR-009**: Nếu API MoMo thất bại hoặc chưa cấu hình, hệ thống PHẢI fallback hiển thị QR tĩnh đã upload.
- **FR-010**: Nếu chưa upload QR tĩnh, hệ thống PHẢI hiển thị placeholder SVG mặc định (không crash).
- **FR-011**: Đơn hàng KHÔNG ĐƯỢC validate quá 1 lần kể cả khi nhận được cả IPN lẫn polling success.
- **FR-012**: Mỗi giao dịch MoMo PHẢI được lưu trữ kèm trạng thái (Pending/Success/Failed/Expired), mã đơn POS, mã giao dịch MoMo, số tiền, thời gian thanh toán.
- **FR-013**: Admin PHẢI có thể cấu hình credentials M4B (Partner Code, Access Key, Secret Key) trực tiếp trong POS Payment Method form; Secret Key hiển thị dạng password field.
- **FR-014**: Credentials PHẢI được lưu an toàn gắn với Payment Method record, không hard-code.
- **FR-015**: Admin PHẢI có thể bật/tắt "Chế độ Test" để chuyển giữa sandbox và production MoMo.
- **FR-016**: Khi polling hết thời gian 5 phút mà chưa nhận xác nhận, POS PHẢI hiển thị thông báo "QR đã hết hiệu lực" và nút "Tạo QR Mới" để thu ngân có thể tạo lại QR cho cùng đơn hàng.
- **FR-017**: IPN webhook PHẢI từ chối xử lý giao dịch nếu chữ ký HMAC-SHA256 không khớp; phải trả về 204 No Content và ghi log warning. Polling là cơ chế recover dự phòng.
- **FR-018**: Mã QR PHẢI được render bằng thư viện local (không phụ thuộc external service `quickchart.io`); hệ thống phải tạo được ảnh QR ngay cả khi không có kết nối internet.

### Key Entities

- **Phương thức thanh toán MoMo (pos.payment.method extend)**: Lưu credentials (Partner Code, Access Key, Secret Key), chế độ test, ảnh QR tĩnh backup.
- **Giao dịch MoMo (trcf.momo.transaction)**: Bản ghi mỗi lần tạo QR. Trạng thái: Pending → Success/Failed/Expired. Liên kết với POS session, POS config để gửi bus notification đúng kênh.
- **QR Code hiển thị (frontend state)**: Trạng thái reactive chỉ tồn tại trong POS session: Loading → QR động → Success checkmark (hoặc QR tĩnh nếu fallback).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Mã QR động xuất hiện trên màn hình POS trong vòng dưới 5 giây sau khi thu ngân chọn MoMo.
- **SC-002**: Đơn hàng được tự động validate trong vòng dưới 10 giây sau khi khách thanh toán thành công.
- **SC-003**: Tỷ lệ giao dịch MoMo không bị duplicate (validate 2 lần) đạt 100%.
- **SC-004**: Hệ thống hoạt động ổn định khi API MoMo không khả dụng — thu ngân luôn thấy QR (tĩnh hoặc động) để tiếp tục nhận tiền.
- **SC-005**: 100% IPN request có chữ ký hợp lệ được xử lý; IPN sai chữ ký bị từ chối và ghi log — không có request trái phép nào được xử lý.
- **SC-006**: Admin có thể hoàn tất cấu hình MoMo Payment Method trong vòng dưới 5 phút.

---

## Assumptions

- Chuỗi F&B có tài khoản MoMo Business (M4B) hợp lệ với Partner Code, Access Key, Secret Key.
- Server Odoo có địa chỉ public URL (`web.base.url`) mà MoMo có thể gọi IPN về — nếu dùng localhost cần ngrok hoặc tương tự để test IPN.
- Tiền tệ là VND (nguyên, không thập phân). MoMo không hỗ trợ thanh toán dưới 1,000đ.
- Mỗi POS config chỉ có 1 phương thức thanh toán MoMo (search lấy limit=1).
- MoMo sandbox (`test_mode=True`) dùng để phát triển và kiểm thử; production chỉ bật sau khi đã verify với MoMo.
- QR code được render bằng **thư viện JavaScript local**, không phụ thuộc `quickchart.io` hay bất kỳ external service nào. Hệ thống hoạt động ngay cả khi không có internet (ngoại trừ API call đến MoMo).

## Out-of-Scope

- **Hoàn tiền (Refund)**: Module chỉ xử lý luồng thanh toán một chiều (nhận tiền). Hoàn tiền MoMo (bao gồm MoMo Refund API) nằm ngoài phạm vi và sẽ là spec riêng biệt.
- **Báo cáo giao dịch MoMo**: Thống kê, export, reconciliation tự động.
- **Đa cửa hàng song song**: Module hỗ trợ 1 payment method MoMo per POS config; multi-store với nhiều MoMo account riêng là use case nâng cấp.
