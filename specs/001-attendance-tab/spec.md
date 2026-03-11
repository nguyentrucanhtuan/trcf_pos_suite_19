# Feature Specification: Trang /dang-ky-ca – Thêm Tab Bảng Giờ Công Tháng

**Feature Branch**: `001-attendance-tab`  
**Created**: 2026-03-05  
**Status**: Draft  
**Input**: User description: "cập nhật thêm chức năng trong link /dang-ky-ca, Chia ra 2 tab, 1 tab là đăng ký ca (chức năng vẫn giữ), 1 tab là bảng giờ công trong tháng cho nhân viên dễ thấy bao gồm các cột, Ngày, Giờ vào, giờ ra, thời gian làm việc, đi, về, tổng lương, Giống bảng dữ liệu https://coffeetreepos.io.vn/odoo/action-649 nhưng là cho nhân viên xem giờ công trong tháng."

---

## Clarifications

### Session 2026-03-05

- Q: Cột "Tổng lương" tính theo cách nào? → A: Tính tạm tính theo giờ công thực tế × đơn giá lương, hiển thị kèm nhãn "Tạm tính"; chỉ hiển thị lương chốt khi `hr.payslip` đã được duyệt.
- Q: Khi không có ca đăng ký tương ứng, cột Đi/Về hiển thị gì? → A: Hiển thị hàng bình thường, cột Đi/Về để "–" (không có dữ liệu ca tham chiếu để tính trễ/sớm).
- Q: Đơn giá lương để tính Tổng lương tạm tính lấy từ đâu? → A: Lấy từ field `trcf_hourly_salary_display` trên bản ghi chấm công (related từ `employee_id.trcf_hourly_salary`); tất cả tính toán đã có sẵn trong field `trcf_hourly_salary_sum` = `worked_hours × trcf_hourly_salary`.
- Q: Bảng hiển thị theo từng phiên chấm công hay gộp theo ngày? → A: Mỗi hàng = một phiên chấm công (một bản ghi `hr.attendance`); cùng ngày có thể có nhiều hàng nếu nhân viên có nhiều phiên.
- Q: Cột "Tổng lương" hiển thị lương phiên hay lũy kế cả tháng? → A: Mỗi hàng hiển thị lương của phiên đó (`trcf_hourly_salary_sum`); cuối bảng có hàng footer tổng lương cả tháng.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Nhân viên xem bảng giờ công tháng của cá nhân mình (Priority: P1)

Nhân viên truy cập trang `/dang-ky-ca`, thấy 2 tab: **"Đăng ký ca"** (chức năng cũ vẫn giữ) và **"Bảng giờ công"**. Khi chọn tab "Bảng giờ công", nhân viên thấy bảng liệt kê toàn bộ ngày trong tháng hiện tại kèm các thông tin: Ngày, Giờ vào, Giờ ra, Thời gian làm việc, Trễ/Về sớm (Đi/Về), và Tổng lương tính đến thời điểm hiện tại. Nhân viên chỉ thấy dữ liệu **của chính mình**, không thấy dữ liệu người khác.

**Why this priority**: Đây là chức năng cốt lõi mới được yêu cầu. Nhân viên cần tra cứu giờ công mà không phải liên hệ HR, giúp tăng tính minh bạch và tiết kiệm thời gian.

**Independent Test**: Đăng nhập bằng tài khoản nhân viên → vào `/dang-ky-ca` → chọn tab "Bảng giờ công" → xác nhận bảng hiển thị đúng dữ liệu của nhân viên đó trong tháng hiện tại.

**Acceptance Scenarios**:

1. **Given** nhân viên đã đăng nhập, **When** truy cập `/dang-ky-ca`, **Then** trang hiển thị 2 tab: "Đăng ký ca" và "Bảng giờ công".
2. **Given** nhân viên đang ở tab "Bảng giờ công", **When** trang tải xong, **Then** bảng hiển thị đúng tháng hiện tại với đầy đủ 6 cột: Ngày, Giờ vào, Giờ ra, Thời gian làm việc, Đi/Về (trễ/về sớm), Tổng lương.
3. **Given** nhân viên A đang xem bảng, **When** dữ liệu được tải, **Then** chỉ hiển thị bản ghi chấm công của nhân viên A, không có bản ghi của nhân viên khác.
4. **Given** ngày chưa có dữ liệu chấm công, **When** bảng hiển thị, **Then** ngày đó hiển thị với ô trống hoặc ghi chú "Chưa có dữ liệu" thay vì bỏ qua.

---

### User Story 2 – Nhân viên lọc bảng giờ công theo tháng khác (Priority: P2)

Nhân viên muốn xem lại giờ công của tháng trước để đối chiếu lương. Trên tab "Bảng giờ công", có bộ lọc chọn tháng/năm. Nhân viên chọn tháng khác và bảng cập nhật dữ liệu tương ứng.

**Why this priority**: Giúp nhân viên tự đối chiếu lịch sử giờ công mà không cần hỏi HR.

**Independent Test**: Vào tab "Bảng giờ công" → dùng bộ lọc chọn tháng trước → xác nhận bảng cập nhật đúng dữ liệu tháng được chọn.

**Acceptance Scenarios**:

1. **Given** nhân viên đang ở tab "Bảng giờ công", **When** chọn tháng/năm khác từ bộ lọc, **Then** bảng tải lại và hiển thị dữ liệu của tháng được chọn.
2. **Given** tháng được chọn không có dữ liệu nào, **When** bảng tải, **Then** hiển thị thông báo "Không có dữ liệu cho tháng này".

---

### User Story 3 – Tab Đăng ký ca vẫn hoạt động bình thường (Priority: P1)

Sau khi thêm tab mới, chức năng đăng ký ca (tab cũ) không bị ảnh hưởng. Nhân viên vẫn đăng ký ca thành công như trước.

**Why this priority**: Không được phép làm hỏng chức năng hiện có.

**Independent Test**: Vào `/dang-ky-ca` → chọn tab "Đăng ký ca" → thực hiện đăng ký ca như bình thường → xác nhận đăng ký thành công.

**Acceptance Scenarios**:

1. **Given** nhân viên ở tab "Đăng ký ca", **When** thực hiện đăng ký ca, **Then** hệ thống lưu thành công và hiển thị thông báo xác nhận như trước.
2. **Given** tab mặc định khi vào trang, **When** không có tham số URL, **Then** tab "Đăng ký ca" được hiển thị mặc định (giữ nguyên hành vi cũ).

---

### Edge Cases

- Nhân viên chưa có bản ghi chấm công trong tháng → bảng hiển thị rỗng với thông báo phù hợp.
- Tháng hiện tại chưa hết → các ngày trong tương lai hiển thị trống.
- Giờ vào có nhưng chưa có giờ ra (đang trong ca) → hiển thị giờ vào, cột giờ ra để trống hoặc ghi "Đang làm".
- Nhân viên chấm công nhưng không có ca đăng ký cho ngày đó → hiển thị hàng bình thường, cột Đi/Về hiển thị "–".
- Tổng lương chưa được chốt (tháng chưa kết thúc) → hiển thị tổng lương tạm tính với ghi chú rõ ràng.
- Nhân viên không có module giờ công được kích hoạt → ẩn tab "Bảng giờ công" hoặc hiển thị thông báo "Chức năng chưa được kích hoạt".

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Trang `/dang-ky-ca` PHẢI hiển thị 2 tab riêng biệt: "Đăng ký ca" và "Bảng giờ công".
- **FR-002**: Tab "Đăng ký ca" PHẢI giữ nguyên toàn bộ chức năng và giao diện hiện có, không thay đổi hành vi.
- **FR-003**: Tab "Bảng giờ công" PHẢI hiển thị bảng dữ liệu giờ công của nhân viên đang đăng nhập trong tháng hiện tại. **Mỗi hàng tương ứng với một phiên chấm công** (một bản ghi `hr.attendance`); cùng ngày có thể xuất hiện nhiều hàng nếu nhân viên có nhiều phiên.
- **FR-004**: Bảng giờ công PHẢI bao gồm đúng 6 cột: **Ngày**, **Giờ vào**, **Giờ ra**, **Thời gian làm việc**, **Đi/Về** (trễ giờ vào / về sớm), **Lương phiên**. Cuối bảng PHẢI có hàng footer hiển thị **tổng lương cả tháng** (tổng cộng của tất cả `trcf_hourly_salary_sum` trong tháng).
- **FR-005**: Hệ thống PHẢI lọc dữ liệu theo nhân viên đang đăng nhập — nhân viên không được xem dữ liệu của người khác.
- **FR-006**: Tab "Bảng giờ công" PHẢI cung cấp bộ lọc chọn tháng/năm để xem lịch sử các tháng trước.
- **FR-007**: Bảng PHẢI liệt kê toàn bộ bản ghi chấm công trong tháng được chọn, sắp xếp theo ngày tăng dần; các ngày không có phiên nào sẽ không xuất hiện hàng trống.
- **FR-008**: Cột "Thời gian làm việc" PHẢI tính từ giờ vào đến giờ ra (đơn vị: giờ và phút, ví dụ: 8h30m).
- **FR-009**: Cột "Đi/Về" PHẢI phản ánh thời gian trễ khi vào và về sớm so với ca đã đăng ký. Nếu ngày đó **không có ca đăng ký** tương ứng, cột Đi/Về hiển thị **"–"** thay vì để trống hoặc tính sai.
- **FR-010**: Cột **"Lương phiên"** của mỗi hàng PHẢI hiển thị giá trị từ field `trcf_hourly_salary_sum` (lương của riêng phiên đó), kèm nhãn **"Tạm tính"** rõ ràng ở header cột. Hàng footer cuối bảng PHẢI hiển thị tổng lương cả tháng. Nếu tháng đã có bảng lương (`hr.payslip`) được duyệt, ẩn nhãn "Tạm tính" và hiển thị tổng lương chính thức từ payslip.
- **FR-011**: Tab mặc định khi truy cập `/dang-ky-ca` PHẢI là tab "Đăng ký ca" (hành vi cũ).

### Key Entities *(include if feature involves data)*

- **Bản ghi chấm công (hr.attendance extended)**: Mô hình `hr.attendance` đã được mở rộng trong module `trcf_fnb_staff`. Chứa: nhân viên, ngày, giờ vào (`check_in`), giờ ra (`check_out`), thời gian làm việc (`worked_hours`), `check_in_status` (Đi), `check_out_status` (Về), `trcf_hourly_salary_sum` (tiền lương phiên).
- **Ca làm việc đã đăng ký (trcf.shift.registration)**: Ca nhân viên đăng ký, dùng để tính trễ/về sớm qua so sánh `shift_start_time` / `shift_end_time` với giờ thực tế.
- **Thông tin nhân viên (hr.employee)**: Chứa field `trcf_hourly_salary` — đơn giá lương theo giờ, dùng để tính `trcf_hourly_salary_sum`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Nhân viên tìm thấy và xem được bảng giờ công tháng trong vòng dưới 30 giây sau khi vào trang `/dang-ky-ca`.
- **SC-002**: Bảng giờ công hiển thị đúng 100% số ngày trong tháng được chọn (không thiếu ngày, không sai ngày).
- **SC-003**: 100% bản ghi chấm công của nhân viên hiển thị trên bảng khớp với dữ liệu hệ thống — không có bản ghi bị thiếu hoặc bị nhầm với người khác.
- **SC-004**: Chức năng đăng ký ca (tab cũ) hoạt động thành công trong 100% trường hợp thử nghiệm — không có regression.
- **SC-005**: Bộ lọc tháng/năm cập nhật bảng dữ liệu chính xác trong vòng dưới 3 giây.

---

## Assumptions

- Dữ liệu chấm công được lưu trong Odoo (model `hr.attendance` hoặc tương đương trong module hiện tại).
- Dữ liệu ca đã đăng ký được lưu trong module shift hiện có (dùng để tính cột Đi/Về).
- Tổng lương lấy từ bảng lương Odoo (model `hr.payslip` hoặc tương đương); nếu tháng chưa chốt thì hiển thị tổng tạm tính.
- Trang `/dang-ky-ca` là một controller Odoo tùy chỉnh (không phải portal Odoo gốc).
- Chỉ nhân viên đã xác thực mới truy cập được trang này.

---

## Out of Scope

- Không thêm chức năng xuất file Excel/PDF cho bảng giờ công trong phiên bản này.
- Không cho phép nhân viên chỉnh sửa dữ liệu chấm công từ trang này.
- Không hiển thị bảng giờ công cho quản lý xem dữ liệu nhiều nhân viên (đó là chức năng riêng của HR/Manager).
