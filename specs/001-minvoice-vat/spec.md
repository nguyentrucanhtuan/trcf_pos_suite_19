# Feature Specification: Xuất Hóa Đơn Điện Tử VAT qua MInvoice

**Feature Branch**: `001-minvoice-vat`
**Created**: 2026-03-02
**Status**: Draft
**Input**: User description: "Module xuất hóa đơn điện tử VAT từ Odoo 19 POS tích hợp nền tảng MInvoice cho chuỗi F&B tại Việt Nam."

---

## Clarifications

### Session 2026-03-02

- Q: Nếu kế toán chọn đơn đã có sobaomat và nhấn "Phát hành hoá đơn", hệ thống làm gì? → A: Tự động skip trong batch — chỉ xuất các đơn chưa có sobaomat, không cần lọc thủ công; số lượng đơn bị bỏ qua hiển thị trong thống kê wizard.
- Q: Sau khi đơn POS hoàn tất, kế toán có bao nhiêu thời gian để xuất hóa đơn VAT? → A: Không giới hạn trong ứng dụng — kế toán tự chịu trách nhiệm tuân thủ quy định thuế; hệ thống không chặn theo thời gian.
- Q: Trang điền VAT công khai cần xác minh thêm gì để tránh lạm dụng? → A: Chặn form sau khi đơn đã có sobaomat — không cho phép sửa thông tin VAT sau khi hóa đơn đã được phát hành.
- Q: Khi token MInvoice hết hạn giữa batch, hệ thống nên làm gì? → A: Dừng batch ngay — hiển thị lỗi rõ ràng "Token hết hạn, vui lòng vào Settings để lấy token mới"; các đơn đã thành công trước đó được giữ nguyên.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Kế Toán Xuất VAT Hàng Loạt (Priority: P1)

Kế toán vào menu **TRCF VAT > Hoá đơn chờ xuất VAT**, lọc danh sách theo ngày (hôm nay, 7 ngày, 30 ngày) hoặc trạng thái (chưa xuất / đã xuất). Chọn một hoặc nhiều đơn POS đã thanh toán rồi nhấn **"Phát hành hoá đơn"**. Hệ thống mở wizard tiến trình và gửi từng đơn lên dịch vụ hóa đơn điện tử. Kế toán thấy ngay kết quả thành công hoặc thông báo lỗi cho từng đơn — mà không cần tải lại trang.

**Why this priority**: Đây là quy trình lõi — không có tính năng này, toàn bộ module không có giá trị. Xuất hàng loạt tiết kiệm đáng kể thời gian so với xuất từng đơn.

**Independent Test**: Chọn 3 đơn POS đã thanh toán → nhấn "Phát hành hoá đơn" → wizard hiện, 3 dòng chuyển trạng thái lần lượt → khi xong, 3 đơn đều có mã hóa đơn và hiển thị màu xanh trong danh sách.

**Acceptance Scenarios**:

1. **Given** có 5 đơn POS đã thanh toán chưa xuất VAT, **When** kế toán chọn tất cả và nhấn "Phát hành hoá đơn", **Then** wizard mở ra với 5 dòng, hệ thống gửi lần lượt, mỗi dòng cập nhật trạng thái (Đang xử lý → Thành công / Thất bại) và sau khi xong, 5 đơn đã có mã bảo mật hóa đơn (sobaomat).
2. **Given** cấu hình MInvoice chưa đầy đủ (thiếu API Token), **When** kế toán nhấn "Phát hành hoá đơn", **Then** hệ thống hiện cảnh báo rõ ràng yêu cầu hoàn thiện cấu hình, không mở wizard.
3. **Given** dịch vụ hóa đơn điện tử trả lỗi cho một đơn, **When** wizard đang xử lý, **Then** dòng đó hiển thị thông báo lỗi cụ thể, các đơn còn lại vẫn tiếp tục xử lý bình thường.

---

### User Story 2 - Nhập Thông Tin Khách Hàng VAT (Priority: P2)

Sau khi đơn POS hoàn tất, thu ngân cung cấp cho khách đường link tự điền thông tin VAT (dạng `/vat_info_form/<mã_đơn>`). Khách truy cập link từ điện thoại hoặc máy tính — không cần tài khoản Odoo — và điền thông tin theo loại: **Doanh nghiệp** (MST, tên công ty, địa chỉ, email, tài khoản ngân hàng), **Cá nhân** (tên, CCCD/hộ chiếu, địa chỉ, email), hoặc **Vãng lai** (không cần thông tin). Thu ngân cũng có thể nhập trực tiếp trong backend.

**Why this priority**: Thông tin VAT chính xác là điều kiện tiên quyết để phát hành hóa đơn hợp lệ. Việc cho khách tự điền giảm sai sót và tiết kiệm thời gian cho thu ngân.

**Independent Test**: Truy cập `/vat_info_form/POS001` từ trình duyệt ẩn danh → trang hiện form → chọn loại "Doanh nghiệp" → điền MST và thông tin → submit → trang xác nhận → vào backend kiểm tra đơn POS001 đã lưu đúng thông tin.

**Acceptance Scenarios**:

1. **Given** một đường link `/vat_info_form/POS001`, **When** khách hàng truy cập và chọn loại "Doanh nghiệp", **Then** form hiển thị các trường: MST, tên công ty, địa chỉ, email, số tài khoản ngân hàng; sau khi submit thông tin được lưu vào đơn hàng POS001.
2. **Given** khách chọn loại "Cá nhân", **When** submit form, **Then** lưu: tên, CCCD hoặc hộ chiếu, địa chỉ, email vào đơn hàng.
3. **Given** khách truy cập link với mã đơn không tồn tại, **When** trang load, **Then** hiển thị thông báo lỗi thân thiện thay vì trang trắng hoặc lỗi hệ thống.
4. **Given** khách chọn "Không lấy hóa đơn", **When** submit form hoặc kế toán xuất VAT, **Then** hóa đơn được phát hành ở dạng ẩn danh (không khai thông tin người mua cụ thể).

---

### User Story 3 - Admin Cấu Hình Kết Nối MInvoice (Priority: P3)

Admin vào **Settings** và điền thông tin để kết nối với nền tảng hóa đơn điện tử: Mã số thuế, Username, Password. Nhấn nút **"Lấy Token"** để hệ thống tự động đăng nhập và lưu API Token. Sau đó nhấn **"Lấy Series"** để tự động lấy ký hiệu hóa đơn từ hệ thống. Admin cũng điền tên cửa hàng/công ty. API Token hiển thị che bớt để bảo mật.

**Why this priority**: Cấu hình là điều kiện cần, nhưng chỉ làm một lần nên có thể thực hiện sau khi các tính năng chính đã sẵn sàng.

**Independent Test**: Vào Settings → điền MST, Username, Password → nhấn "Lấy Token" → thông báo thành công → nhấn "Lấy Series" → ký hiệu hóa đơn tự động điền vào trường → lưu Settings → vào màn hình xuất VAT, hệ thống không còn cảnh báo thiếu cấu hình.

**Acceptance Scenarios**:

1. **Given** admin điền đúng MST, Username, Password, **When** nhấn "Lấy Token", **Then** hệ thống tự động xác thực với dịch vụ hóa đơn, lưu token và thông báo thành công.
2. **Given** token đã được lấy, **When** admin nhấn "Lấy Series", **Then** ký hiệu hóa đơn được tự động lấy và điền vào trường cấu hình.
3. **Given** admin điền sai Password, **When** nhấn "Lấy Token", **Then** hệ thống hiện thông báo lỗi mô tả nguyên nhân (sai thông tin đăng nhập).
4. **Given** token đã được lưu, **When** admin xem trang Settings, **Then** trường API Token chỉ hiển thị phần cuối của chuỗi (che bảo mật), không hiển thị toàn bộ giá trị.

---

### Edge Cases

- Đơn đã có sobaomat sẽ **tự động bị bỏ qua (skip)** khi chạy batch — wizard chỉ xử lý các đơn chưa có sobaomat. Số đơn bị bỏ qua hiển thị trong thống kê cuối wizard.
- API MInvoice timeout sau 30 giây → đơn hàng không bị trạng thái "treo" mãi, phải chuyển sang Thất bại với thông báo timeout.
- Token hết hạn giữa chừng khi đang xuất hàng loạt → **batch dừng ngay lập tức**, wizard hiển thị lỗi "Token hết hạn, vui lòng vào Settings để lấy token mới". Các đơn đã thành công trước thời điểm token hết hạn được giữ nguyên kết quả.
- Khách truy cập link VAT sau khi đơn **đã được xuất VAT** (đã có sobaomat) → form bị **khóa hoàn toàn**, hiển thị thông báo "Hóa đơn đã được phát hành, không thể chỉnh sửa thông tin."
- Đơn POS bị hủy (state = cancel) → không cho phép xuất VAT.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI hiển thị danh sách đơn POS đã thanh toán kèm trạng thái xuất VAT (đã xuất / chưa xuất) tại menu TRCF VAT.
- **FR-002**: Hệ thống PHẢI hỗ trợ lọc danh sách theo: hôm nay, 7 ngày qua, 30 ngày qua, chưa xuất VAT, đã xuất VAT.
- **FR-003**: Người dùng PHẢI có thể chọn nhiều đơn và phát hành hóa đơn VAT cùng lúc qua wizard tiến trình. Hệ thống PHẢI tự động bỏ qua (skip) các đơn đã có sobaomat mà không cần người dùng lọc thủ công; số đơn bị bỏ qua PHẢI hiển thị trong thống kê cuối wizard.
- **FR-004**: Hệ thống PHẢI hiển thị trạng thái xử lý từng đơn theo thời gian thực trong wizard (Đang xử lý → Thành công / Thất bại).
- **FR-005**: Hệ thống PHẢI lưu mã bảo mật hóa đơn (sobaomat) vào đơn hàng sau khi phát hành thành công.
- **FR-006**: Đơn đã xuất VAT PHẢI được hiển thị màu xanh trong danh sách để phân biệt trực quan.
- **FR-007**: Hệ thống PHẢI hiển thị cảnh báo cụ thể khi cấu hình MInvoice chưa đầy đủ (thiếu MST, series hoặc token), TRƯỚC khi mở wizard.
- **FR-008**: Hệ thống PHẢI cung cấp trang web công khai (không yêu cầu đăng nhập) để khách hàng tự điền thông tin VAT theo mã đơn.
- **FR-009**: Trang điền thông tin VAT PHẢI hỗ trợ 3 loại khách: Doanh nghiệp, Cá nhân, Vãng lai — với các trường thông tin tương ứng cho từng loại.
- **FR-010**: Hệ thống PHẢI cho phép admin lấy API Token tự động từ trang Settings bằng thông tin đăng nhập MInvoice.
- **FR-011**: Hệ thống PHẢI cho phép admin lấy ký hiệu hóa đơn (invoice series) tự động từ dịch vụ hóa đơn điện tử.
- **FR-012**: API Token trong Settings PHẢI được hiển thị che bớt (chỉ hiện phần cuối) để bảo mật.
- **FR-013**: Khi API dịch vụ hóa đơn trả lỗi, hệ thống PHẢI ghi nhận thông báo lỗi cụ thể vào từng dòng wizard thay vì dừng toàn bộ tiến trình.
- **FR-014**: Trang điền thông tin VAT công khai PHẢI bị khóa (read-only) và hiển thị thông báo "Hóa đơn đã được phát hành, không thể chỉnh sửa thông tin" khi đơn hàng đã có sobaomat.
- **FR-015**: Khi phát hiện token MInvoice hết hạn trong quá trình xuất hàng loạt, hệ thống PHẢI dừng batch ngay lập tức và hiển thị hướng dẫn lấy lại token trong Settings; các đơn đã phát hành thành công trước đó KHÔNG bị ảnh hưởng.

### Key Entities *(include if feature involves data)*

- **Đơn hàng POS (POS Order)**: Đơn bán hàng từ quầy thu ngân. Được bổ sung các trường: loại khách VAT, thông tin người mua (tên, MST/CCCD/hộ chiếu, địa chỉ, email, ngân hàng), mã bảo mật hóa đơn (sobaomat), trạng thái đã xuất VAT.
- **Hóa đơn VAT**: Hóa đơn điện tử do dịch vụ MInvoice phát hành. Được liên kết với đơn POS qua sobaomat. Chứa thông tin người bán (tên cửa hàng, MST, ký hiệu hóa đơn) và thông tin người mua.
- **Cấu hình hệ thống**: Lưu thông tin kết nối với dịch vụ hóa đơn: MST, API Token, ký hiệu hóa đơn, tên cửa hàng. Được quản lý bởi admin trong phần Settings.
- **Tiến trình xuất wizard**: Phiên làm việc tạm thời khi xuất hàng loạt. Chứa danh sách các đơn cần xuất, trạng thái từng dòng (Chờ / Đang xử lý / Thành công / Thất bại), thống kê tổng hợp.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Kế toán có thể phát hành hóa đơn VAT cho 10 đơn hàng trong vòng dưới 5 phút.
- **SC-002**: Tỷ lệ phát hành hóa đơn thành công đạt ≥ 95% trong điều kiện kết nối mạng ổn định.
- **SC-003**: Khách hàng có thể tự điền thông tin VAT qua đường link và hoàn tất trong vòng dưới 2 phút.
- **SC-004**: Kết quả của từng đơn trong wizard hiển thị trong vòng dưới 10 giây kể từ khi bắt đầu xử lý đơn đó.
- **SC-005**: Admin có thể hoàn tất cấu hình kết nối MInvoice (lấy token, lấy series) trong vòng dưới 3 phút.
- **SC-006**: Thông báo lỗi phải đủ mô tả để kế toán tự xử lý được ít nhất 80% các trường hợp lỗi thường gặp mà không cần liên hệ kỹ thuật.

---

## Assumptions

- Dịch vụ hóa đơn điện tử MInvoice đã có tài khoản M4B và các thông tin đăng nhập hợp lệ.
- Tất cả sản phẩm trong đơn POS áp dụng thuế VAT 8% (mặc định theo quy định hiện hành; có thể điều chỉnh nếu có sản phẩm miễn thuế).
- Đồng tiền mặc định là VND, tỷ giá 1.
- Không có giới hạn thời gian trong ứng dụng để xuất hóa đơn VAT sau khi đơn POS hoàn tất — kế toán tự chịu trách nhiệm tuân thủ quy định thuế hiện hành.
- Phiên bản MInvoice API đang sử dụng là InvoiceApi78 (Save endpoint).
