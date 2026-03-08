# Feature Specification: Tab Chấm Công Geolocation – Tích hợp /dang-ky-ca

**Feature Branch**: `002-geo-attendance`  
**Created**: 2026-03-07  
**Updated**: 2026-03-08 (bổ sung bảo mật: fake GPS, fake time, xác minh Public IP WiFi)  
**Status**: Draft  
**Input**: User description: "Dùng GEO LOCATION JS để làm ứng dụng chấm công, tích hợp với tab /dang-ky-ca trong module trcf_zkteco_attendance_sync"

---

## Clarifications

### Session 2026-03-08

- Q: Khi nhân viên nhấn Check-out, hệ thống có kiểm tra GPS và IP không? → A: Check-out bắt buộc GPS hợp lệ (phải trong geofence) VÀ kiểm tra IP như check-in.
- Q: Có cần lưu trường `ip_match` vào bản ghi chấm công không? → A: Không — kết quả khớp IP suy ra từ `ip_suspicious = False` khi cơ sở đã cấu hình danh sách IP.
- Q: Khi đọc IP từ header `X-Forwarded-For`, hệ thống dùng hop nào để tránh bị giả mạo? → A: Dùng IP được găn bởi reverse proxy đáng tin (rightmost trusted hop / `REMOTE_ADDR` từ nginx) — không tin vào giá trị client tự gửi.
- Q: Tab Chấm Công cập nhật vị trí GPS như thế nào? → A: Lấy lần đầu khi mở tab, sau đó tự động refresh mỗi 5 giây.
- Q: Mỗi bản ghi `hr.attendance` khi tạo có lưu cơ sở nào nhân viên đang check-in không? → A: Có — lưu `geo_location_id` (FK đến `trcf.geo.location`) vào bản ghi chấm công.

### Assumptions

- Nhân viên đã đăng nhập vào hệ thống Odoo qua browser (auth='user') trên thiết bị di động hoặc desktop.
- Mỗi cơ sở/chi nhánh có một tọa độ GPS trung tâm (latitude, longitude) và bán kính được phép chấm công (radius, tính bằng mét) được cấu hình sẵn trong hệ thống.
- Hệ thống sẽ thêm một **tab "Chấm Công"** (tab thứ ba) vào trang `/dang-ky-ca`, bên cạnh tab "Đăng ký ca" (tab 1) và tab "Bảng giờ công" (tab 2 - đã triển khai trong `001-attendance-tab`).
- Chấm công Geolocation cạnh tranh / bổ sung với chấm công ZKTeco — không thay thế.
- Múi giờ: giờ địa phương `Asia/Ho_Chi_Minh` (UTC+7).
- Nhân viên chỉ có thể Check-in một lần và Check-out một lần mỗi ca (ví dụ: không có nhiều phiên cùng giờ trong cùng ngày trừ khi ca khác nhau).

### Bảo mật: Fake GPS và Fake Thời gian

**Fake thời gian (đổi giờ điện thoại)**: Không ảnh hưởng hệ thống. Timestamp `check_in` / `check_out` được ghi bằng **giờ server** (UTC), không dùng bất kỳ giá trị thời gian nào từ phía client. Nhân viên không thể thay đổi giờ server bằng cách chỉnh đồng hồ điện thoại.

**Fake GPS (GPS Spoofing)**: Không thể chặn 100% qua web browser, nhưng hệ thống áp dụng 4 lớp phát hiện:

| Lớp | Tín hiệu | Cách xử lý |
|-----|---------|------------|
| 1 – Accuracy | App giả GPS thường trả `accuracy = 0m hoặc < 2m` (bất thường) | Log + flag nếu accuracy < 5m |
| 2 – Velocity | Di chuyển > 500 km/giờ giữa 2 lần check (bất khả thi) | Tự động flag, HR review |
| 3 – Pattern | Liên tục check-in đúng bán kính mà không bao giờ lệch | Ghi nhận để HR phân tích |
| 4 – Public IP | Public IP của thiết bị không khớp IP WiFi văn phòng đã đăng ký | Cảnh báo hoặc từ chối tùy cấu hình |

Hệ thống **không từ chối hoàn toàn** dựa trên các tín hiệu này (trừ khi admin bật chế độ bắt buộc IP), mà **ghi nhận cờ cảnh báo** để HR xem xét.

**Xác minh Public IP WiFi**: Khi nhân viên check-in, hệ thống server tự tra cứu public IP của request (từ HTTP header) và so sánh với danh sách public IP được phép cho cơ sở tương ứng. Không yêu cầu nhân viên làm thêm bước nào — hoàn toàn tự động phía server. Admin có thể chọn chế độ: (a) **Cảnh báo** — ghi nhận IP không khớp nhưng vẫn cho check-in; (b) **Bắt buộc** — từ chối check-in nếu IP không thuộc danh sách.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 – Nhân viên Check-in bằng Geolocation (Priority: P1)

Nhân viên đến nơi làm việc, mở trình duyệt truy cập `/dang-ky-ca`, chọn tab **"Chấm Công"**. Trình duyệt yêu cầu quyền truy cập vị trí GPS. Sau khi nhân viên cho phép, hệ thống kiểm tra xem vị trí hiện tại có nằm trong bán kính được phép của cơ sở hay không. Nếu hợp lệ, nhân viên nhấn nút **"Check-in"** và hệ thống ghi nhận giờ vào, lưu vào model `hr.attendance`.

**Why this priority**: Đây là chức năng cốt lõi của tính năng — không có check-in thì không có chấm công Geolocation.

**Independent Test**: Đăng nhập bằng tài khoản nhân viên → vào `/dang-ky-ca` → chọn tab "Chấm Công" → cho phép GPS → xác nhận vị trí hợp lệ → nhấn Check-in → kiểm tra bản ghi `hr.attendance` được tạo với `check_in` đúng giờ.

**Acceptance Scenarios**:

1. **Given** nhân viên đã đăng nhập và ở trong phạm vi GPS cho phép, **When** mở tab "Chấm Công", **Then** hiển thị vị trí hiện tại trên bản đồ, trạng thái "Hợp lệ ✓", và nút "Check-in" có thể nhấn được.
2. **Given** nhân viên nhấn nút "Check-in" khi vị trí hợp lệ, **When** trang xử lý xong, **Then** hệ thống tạo bản ghi `hr.attendance` với `check_in = NOW()` (UTC), hiển thị thông báo thành công và thay nút bằng "Check-out".
3. **Given** nhân viên đã Check-in, **When** quay lại tab "Chấm Công", **Then** hiển thị trạng thái "Đang trong ca", giờ check-in, và nút "Check-out".
4. **Given** nhân viên nằm ngoài bán kính GPS cho phép, **When** mở tab "Chấm Công", **Then** nút "Check-in" bị ẩn hoặc vô hiệu, hiển thị cảnh báo dạng "Bạn cách cơ sở X mét — ngoài vùng cho phép".

---

### User Story 2 – Nhân viên Check-out bằng Geolocation (Priority: P1)

Nhân viên kết thúc ca làm việc, truy cập tab "Chấm Công". Hệ thống kiểm tra vị trí GPS **và public IP** (cùng quy tắc như check-in), nếu hợp lệ thì hiển thị nút "Check-out". Nhân viên nhấn "Check-out", hệ thống cập nhật `check_out` vào bản ghi `hr.attendance` tương ứng, tính `worked_hours` và các field liên quan.

**Why this priority**: Hoàn tất một phiên chấm công — không có check-out thì không tính được giờ công và lương.

**Independent Test**: Sau khi Check-in thành công → trở lại tab "Chấm Công" → nhấn "Check-out" khi vị trí hợp lệ và IP hợp lệ → kiểm tra `check_out` được cập nhật vào đúng bản ghi `hr.attendance`, `worked_hours` được tính.

**Acceptance Scenarios**:

1. **Given** nhân viên đã Check-in và đang trong ca, **When** nhấn "Check-out" ở vị trí GPS hợp lệ và IP hợp lệ, **Then** hệ thống cập nhật `check_out = NOW()` vào bản ghi `hr.attendance` đang mở, hiển thị thông báo thành công, hiển thị tổng thời gian làm việc của phiên vừa xong.
2. **Given** nhân viên đã Check-in nhưng đang ở ngoài geofence, **When** vào tab "Chấm Công", **Then** nút "Check-out" bị ẩn hoặc vô hiệu hóa kèm thông báo "Bạn cách cơ sở X mét — ngoài vùng cho phép".
3. **Given** nhân viên đã Check-in, ở trong geofence nhưng IP không khớp và chế độ "Bắt buộc", **When** nhấn "Check-out", **Then** check-out bị từ chối với thông báo "Thiết bị không kết nối đúng mạng WiFi văn phòng".
4. **Given** nhân viên chưa Check-in hôm nay, **When** vào tab "Chấm Công", **Then** chỉ hiển thị nút "Check-in", không hiển thị "Check-out".
5. **Given** nhân viên đã Check-out xong ca hôm nay, **When** vào lại tab "Chấm Công", **Then** hiển thị thông báo "Bạn đã hoàn thành ca hôm nay" kèm tóm tắt giờ công phiên vừa xong.

---

### User Story 3 – Cấu hình GPS Geofence cho cơ sở (Priority: P2)

Quản trị viên hoặc HR Manager cấu hình vùng chấm công cho mỗi cơ sở/chi nhánh thông qua **giao diện bản đồ tương tác** trong phần quản lý Odoo backend. Quản trị viên **click lên bản đồ để đặt điểm tâm** (lat/lon tự điền), sau đó **kéo vòng tròn để chỉnh bán kính** (radius cập nhật theo thời gian thực bằng mét). Ngoài ra có nút **"Dùng vị trí hiện tại"** để nhanh chóng đặt tâm tại vị trí của thiết bị admin.

**Why this priority**: Không có cấu hình Geofence thì hệ thống không biết "nơi làm việc" là ở đâu. UX bản đồ giúp admin không cần biết tọa độ GPS là số bao nhiêu — chỉ cần nhìn và kéo.

**Independent Test**: Vào Odoo backend → TRCF → Cấu hình Geofence → tạo mới cơ sở → click trên bản đồ đặt tâm → kéo vòng chỉnh bán kính 100m → lưu → nhân viên check-in trong vùng đó thành công.

**Acceptance Scenarios**:

1. **Given** quản trị viên mở form tạo cơ sở mới, **When** trang tải, **Then** hiển thị bản đồ tương tác với con trỏ chờ nhấn chọn vị trí; các field latitude, longitude, radius vẫn có thể nhập tay song song.
2. **Given** quản trị viên click một điểm trên bản đồ, **When** click xong, **Then** đặt ghim tâm tại điểm đó, hiển thị vòng tròn bán kính mặc định (100m), và tự động điền giá trị latitude/longitude vào field.
3. **Given** quản trị viên kéo rìa vòng tròn trên bản đồ, **When** kéo, **Then** vòng tròn thay đổi kích thước theo thời gian thực và field radius cập nhật số mét tương ứng.
4. **Given** quản trị viên nhấn nút "Dùng vị trí hiện tại", **When** browser xác định được GPS, **Then** bản đồ di chuyển đến vị trí đó, đặt tâm và điền lat/lon tự động.
5. **Given** cấu hình GPS chưa được thiết lập, **When** nhân viên vào tab "Chấm Công", **Then** hiển thị thông báo "Cơ sở chưa được cấu hình vị trí GPS — vui lòng liên hệ quản trị" thay vì cho check-in.
6. **Given** có nhiều cơ sở/chi nhánh, **When** nhân viên check-in, **Then** hệ thống so khớp GPS với tất cả cơ sở đã cấu hình, chấp nhận nếu nằm trong bán kính của ít nhất một cơ sở.
7. **Given** quản trị viên nhập danh sách public IP cho cơ sở (ví dụ: `203.113.x.x, 14.178.y.y`), **When** lưu cấu hình, **Then** hệ thống lưu danh sách IP và áp dụng cho các lần check-in tiếp theo tại cơ sở đó.
8. **Given** quản trị viên chọn chế độ kiểm tra IP là "Bắt buộc", **When** nhân viên check-in từ IP không thuộc danh sách, **Then** check-in bị từ chối với thông báo rõ ràng.
9. **Given** quản trị viên chọn chế độ kiểm tra IP là "Cảnh báo", **When** nhân viên check-in từ IP không thuộc danh sách, **Then** check-in vẫn thành công nhưng bản ghi được flag `ip_suspicious = True`.

---

### User Story 3b – Xác minh Public IP WiFi khi chấm công (Priority: P2)

Khi nhân viên thực hiện check-in hoặc check-out, server tự động kiểm tra public IP của request HTTP. Nếu cơ sở đã cấu hình danh sách IP được phép, hệ thống so sánh IP của thiết bị với danh sách đó. Toàn bộ quá trình này diễn ra ngầm, không yêu cầu thao tác thêm từ nhân viên. Kết quả kiểm tra được lưu cùng bản ghi chấm công.

**Why this priority**: Public IP của mạng WiFi văn phòng thường cố định — đây là lớp xác minh thứ hai bên cạnh GPS, giúp phát hiện nhân viên check-in từ xa (dùng GPS spoofing hoặc VPN) trong khi không thực sự có mặt tại văn phòng.

**Independent Test**: Cấu hình cơ sở với IP cụ thể → check-in từ IP khác → kiểm tra cờ `ip_suspicious = True` hoặc bị từ chối tùy chế độ → check-in từ IP đúng → kiểm tra `ip_suspicious = False`, check-in thành công.

**Acceptance Scenarios**:

1. **Given** cơ sở chưa cấu hình public IP nào, **When** nhân viên check-in, **Then** kiểm tra IP bị bỏ qua, check-in diễn ra bình thường chỉ dựa vào GPS.
2. **Given** cơ sở có danh sách IP và chế độ "Cảnh báo", **When** nhân viên check-in từ IP hợp lệ, **Then** `ip_suspicious = False`, không có flag.
3. **Given** cơ sở có danh sách IP và chế độ "Cảnh báo", **When** nhân viên check-in từ IP không hợp lệ, **Then** check-in thành công nhưng `ip_suspicious = True`, lưu kèm IP thực tế của request.
4. **Given** cơ sở có danh sách IP và chế độ "Bắt buộc", **When** nhân viên check-in từ IP không hợp lệ, **Then** check-in bị từ chối, hiển thị thông báo "Thiết bị không kết nối đúng mạng WiFi văn phòng".
5. **Given** cơ sở có danh sách IP và chế độ "Bắt buộc", **When** nhân viên check-in từ IP hợp lệ, **Then** check-in thành công, `ip_suspicious = False`.
6. **Given** nhân viên dùng VPN hoặc proxy khiến IP thay đổi, **When** check-in trong chế độ "Bắt buộc", **Then** check-in bị từ chối nếu IP VPN không có trong danh sách được phép.

---

### User Story 4 – Tab Đăng ký ca và Bảng giờ công vẫn hoạt động bình thường (Priority: P1)

Sau khi thêm tab "Chấm Công", hai tab còn lại ("Đăng ký ca" và "Bảng giờ công") không bị ảnh hưởng.

**Why this priority**: Không được phép tạo regression trên chức năng hiện có.

**Independent Test**: Vào `/dang-ky-ca` → kiểm tra 3 tab hiện diện → thao tác đăng ký ca bình thường → xem bảng giờ công bình thường.

**Acceptance Scenarios**:

1. **Given** nhân viên vào `/dang-ky-ca`, **When** trang tải, **Then** hiển thị 3 tab: "Đăng ký ca" (tab 1, mặc định), "Bảng giờ công" (tab 2), "Chấm Công" (tab 3).
2. **Given** nhân viên ở tab "Đăng ký ca", **When** thực hiện đăng ký, **Then** chức năng hoạt động bình thường y như trước.
3. **Given** nhân viên ở tab "Bảng giờ công", **When** xem bảng, **Then** bảng giờ công hiển thị đầy đủ bao gồm cả bản ghi chấm công từ Geolocation.

---

### Edge Cases

- Trình duyệt không hỗ trợ Geolocation API → hiển thị thông báo "Trình duyệt của bạn không hỗ trợ định vị GPS. Vui lòng dùng trình duyệt khác".
- Nhân viên từ chối cấp quyền GPS → hiển thị hướng dẫn bật lại quyền, nút Check-in không hoạt động.
- GPS trả về vị trí không chính xác (accuracy > 100m) → hiển thị cảnh báo "Tín hiệu GPS yếu, độ chính xác thấp" nhưng vẫn cho phép check-in nếu nằm trong bán kính (để tránh chặn nhân viên hợp lệ); lưu accuracy vào log.
- **Nhân viên fake GPS**: Hệ thống lưu giá trị `accuracy` (mét) từ browser. Nếu accuracy < 5m (bất thường với môi trường thực tế) → lưu cờ `geo_suspicious = True` vào bản ghi, không từ chối.
- **Nhân viên đổi giờ điện thoại**: Không ảnh hưởng — timestamp lưu là giờ server, không phải giờ thiết bị.
- **Velocity check**: Nếu tốc độ di chuyển giữa check-out lần trước và check-in lần này > 500 km/h (bất khả thi) → hệ thống tự động đặt cờ `geo_suspicious = True`. HR có thể xem danh sách bản ghi bị flag.
- **Public IP không khớp**: Nếu cơ sở đã cấu hình danh sách IP và chế độ là "Cảnh báo" → lưu `ip_suspicious = True` và IP thực tế, vẫn ghi nhận check-in. Nếu chế độ là "Bắt buộc" → từ chối check-in.
- **Cơ sở chưa cấu hình IP**: Bỏ qua kiểm tra IP, không ảnh hưởng luồng chấm công.
- **IP động (DHCP WAN thay đổi)**: Admin cần cập nhật danh sách IP trong cấu hình cơ sở khi ISP thay đổi IP. Hệ thống ghi nhận IP thực tế của mỗi lần check-in để admin tra soát.
- Nhân viên check-in ngoài giờ ca đã đăng ký (ví dụ: check-in lúc 6h trong khi ca bắt đầu 8h) → vẫn ghi nhận bản ghi chấm công bình thường, `check_in_status` sẽ được tính tự động bởi compute field như hiện tại.
- Mất kết nối mạng sau khi GPS xác định vị trí → thử gửi check-in 3 lần rồi thông báo lỗi, không mất dữ liệu đã xác định.
- Nhân viên check-in từ điện thoại nhưng check-out từ máy tính → hệ thống chấp nhận vì check phía server, không phụ thuộc thiết bị.
- Hai phiên check-in cùng ngày chưa có check-out (bản ghi mở) → hệ thống cảnh báo "Bạn đang có phiên chưa kết thúc" và gợi ý checkout phiên cũ trước.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Trang `/dang-ky-ca` PHẢI hiển thị 3 tab: "Đăng ký ca" (tab 1, mặc định), "Bảng giờ công" (tab 2), "Chấm Công" (tab 3). Tab 1 và Tab 2 giữ nguyên chức năng hiện có.
- **FR-002**: Tab "Chấm Công" PHẢI sử dụng Browser Geolocation API (`navigator.geolocation.getCurrentPosition`) để lấy vị trí GPS khi mở tab, sau đó tự động refresh mỗi **5 giây** bằng `setInterval`. Yêu cầu quyền vị trí khi mở tab lần đầu.
- **FR-003**: Hệ thống PHẢI tính khoảng cách giữa vị trí GPS của nhân viên và tọa độ GPS của cơ sở (dùng công thức Haversine hoặc tương đương), so sánh với bán kính cấu hình (meter) để xác định hợp lệ.
- **FR-004**: Tab "Chấm Công" PHẢI hiển thị trạng thái vị trí theo thời gian thực (cập nhật mỗi 5 giây): khoảng cách tới cơ sở gần nhất, trạng thái hợp lệ/không hợp lệ, và hướng dẫn khi nằm ngoài vùng. Nút Check-in/Check-out tự động bật/tắt theo trạng thái GPS mới nhất.
- **FR-005**: Nút "Check-in" PHẢI chỉ có thể nhấn được khi xác định được vị trí GPS hợp lệ (nằm trong bán kính cấu hình). Khi ngoài vùng, nút ẩn hoặc bị vô hiệu hóa kèm thông báo rõ lý do.
- **FR-006**: Khi nhân viên nhấn "Check-in" thành công, hệ thống PHẢI tạo bản ghi `hr.attendance` mới với `employee_id` = nhân viên hiện tại, `check_in` = giờ hiện tại (UTC), và lưu tọa độ GPS check-in (latitude, longitude) vào bản ghi.
- **FR-007**: Nút "Check-out" PHẢI hiển thị thay nút "Check-in" khi nhân viên đã có bản ghi `hr.attendance` trong ngày chưa có `check_out`. Check-out PHẢI áp dụng cùng quy tắc xác thực như check-in: (a) vị trí GPS phải nằm trong bán kính geofence, (b) public IP phải vượt qua kiểm tra IP theo chế độ cấu hình của cơ sở. Khi hợp lệ, hệ thống PHẢI cập nhật `check_out` và lưu tọa độ GPS + IP của request check-out vào bản ghi.
- **FR-008**: Hệ thống PHẢI lưu tọa độ GPS (latitude, longitude) và **độ chính xác GPS (accuracy, tính bằng mét)** cho cả check-in và check-out vào bản ghi chấm công.
- **FR-009**: Cấu hình Geofence PHẢI được quản lý qua giao diện **bản đồ tương tác** trong Odoo backend, bao gồm: (a) click trên bản đồ để đặt điểm tâm (lat/lon tự điền), (b) kéo rìa vòng tròn để chỉnh bán kính (radius cập nhật tức thời bằng mét), (c) nút "Dùng vị trí hiện tại" để lấy GPS từ thiết bị admin. Field lat/lon/radius vẫn cho phép nhập tay. Hỗ trợ nhiều cơ sở.
- **FR-010**: Khi trình duyệt không hỗ trợ GPS hoặc nhân viên từ chối cấp quyền, hệ thống PHẢI hiển thị thông báo thân thiện và không cho check-in bằng Geolocation.
- **FR-011**: Tab "Bảng giờ công" PHẢI hiển thị cả bản ghi chấm công từ ZKTeco lẫn từ Geolocation trong cùng bảng (source được phân biệt bằng cột hoặc icon nếu cần).
- **FR-012**: Hệ thống PHẢI ngăn check-in khi nhân viên đã có bản ghi `hr.attendance` đang mở (chưa checkout) trong ngày — thay vào đó hiển thị trạng thái đang trong ca và nút "Check-out".
- **FR-013**: Timestamp `check_in` và `check_out` PHẢI được ghi bằng **giờ server** tại thời điểm request đến. Hệ thống KHÔNG ĐƯỢC dùng bất kỳ giá trị thời gian nào do client (trình duyệt/điện thoại) gửi lên. Nhân viên đổi giờ thiết bị không ảnh hưởng được timestamp.
- **FR-014**: Hệ thống PHẢI tự động đánh dấu `geo_suspicious = True` vào bản ghi chấm công khi phát hiện bất kỳ dấu hiệu bất thường nào: (a) accuracy GPS < 5m, hoặc (b) tốc độ di chuyển giữa lần checkout trước và check-in hiện tại > 500 km/h. Bản ghi vẫn được lưu bình thường.
- **FR-015**: HR Manager PHẢI có thể xem danh sách các bản ghi chấm công Geo bị đánh dấu `geo_suspicious = True` hoặc `ip_suspicious = True` để xem xét và quyết định xử lý thủ công.
- **FR-016**: Hệ thống PHẢI hiển thị badge/icon cảnh báo bên cạnh bản ghi bị flag trong bảng giờ công, người dùng hover/click vào sẽ thấy lý do flag (accuracy thấp / velocity bất thường / IP không khớp).
- **FR-017**: Tại thời điểm server xử lý check-in/check-out, hệ thống PHẢI tự động trích xuất public IP của request HTTP bằng cách ưu tiên lấy **`REMOTE_ADDR` do reverse proxy (nginx) gắn vào** (đây là rightmost trusted hop, không thể bị client giả mạo). Nếu Odoo được cấu hình `proxy_mode = True`, dùng `request.environ.get('HTTP_X_FORWARDED_FOR')` nhưng chỉ lấy **phần tử được xác nhận bởi nginx** (last hop thường đủ tin cậy). Không bao giờ tin vào `X-Forwarded-For` do client tự đặt mà không qua proxy xác nhận.
- **FR-018**: Mỗi cơ sở trong `trcf.geo.location` PHẢI cho phép cấu hình: (a) **Danh sách public IP được phép** (có thể trống — bỏ qua kiểm tra), (b) **Chế độ kiểm tra IP**: "Cảnh báo" (flag `ip_suspicious` nhưng cho check-in) hoặc "Bắt buộc" (từ chối check-in nếu IP không hợp lệ).
- **FR-019**: Khi cơ sở có danh sách IP và request đến từ IP không thuộc danh sách: trong chế độ "Cảnh báo" → check-in thành công, `ip_suspicious = True`; trong chế độ "Bắt buộc" → check-in bị từ chối với thông báo "Thiết bị không kết nối đúng mạng WiFi văn phòng".
- **FR-020**: Khi cơ sở chưa cấu hình danh sách IP (trống), hệ thống PHẢI bỏ qua kiểm tra IP hoàn toàn — không flag, không từ chối.
- **FR-021**: Khi tạo bản ghi check-in, hệ thống PHẢI xác định cơ sở khớp GPS (cơ sở mà vị trí nhân viên nằm trong bán kính) và lưu vào field `geo_location_id`. Nếu nhiều cơ sở cùng khớp, chọn cơ sở có tâm gần nhân viên nhất. Kiểm tra IP sử dụng `allowed_ips` và `ip_check_mode` của cơ sở này.

### Key Entities

- **Bản ghi chấm công Geo (hr.attendance extended)**: Kế thừa `hr.attendance`, bổ sung các field:
  - `geo_check_in_lat`, `geo_check_in_lon` (Float): tọa độ check-in
  - `geo_check_out_lat`, `geo_check_out_lon` (Float): tọa độ check-out
  - `geo_check_in_accuracy`, `geo_check_out_accuracy` (Float, mét): độ chính xác GPS
  - `attendance_source` (Selection: 'zkteco', 'geo', 'manual'): nguồn chấm công
  - `geo_suspicious` (Boolean, default False): cờ cảnh báo bất thường GPS
  - `geo_suspicious_reason` (Char): lý do flag GPS ('low_accuracy', 'impossible_velocity', hoặc kết hợp)
  - `request_ip` (Char): public IP của request check-in/check-out
  - `ip_suspicious` (Boolean, default False): cờ cảnh báo IP không khớp danh sách được phép
  - `geo_location_id` (Many2one → `trcf.geo.location`): cơ sở nơi nhân viên check-in (cơ sở khớp GPS được gắn tại thời điểm check-in)
- **Cấu hình cơ sở GPS (trcf.geo.location)**: Model mới lưu: `name` (tên cơ sở/chi nhánh), `latitude` (Float), `longitude` (Float), `radius` (Float, mét, mặc định 100m), `active` (Boolean), `allowed_ips` (Text, danh sách public IP cách nhau bởi dấu phẩy, có thể trống), `ip_check_mode` (Selection: 'none' – bỏ qua, 'warning' – cảnh báo, 'strict' – bắt buộc; mặc định 'none').
- **Nhân viên (hr.employee)**: Đã có `trcf_hourly_salary`. Không cần thêm field mới để check-in Geo hoạt động.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Nhân viên hoàn thành thao tác check-in Geolocation (từ khi mở tab đến khi nhận thông báo thành công) trong vòng dưới 15 giây khi có kết nối GPS ổn định.
- **SC-002**: 100% thao tác check-in / check-out từ vị trí hợp lệ được ghi nhận đúng vào hệ thống, không có bản ghi bị mất.
- **SC-003**: 100% thao tác check-in từ vị trí ngoài vùng Geofence bị từ chối và hiển thị lý do rõ ràng cho nhân viên.
- **SC-004**: Chức năng đăng ký ca và bảng giờ công (tab 1 và tab 2) không có regression — 100% test cases của `001-attendance-tab` vẫn pass.
- **SC-005**: Quản trị viên có thể cấu hình Geofence (tọa độ + bán kính + danh sách IP) cho một cơ sở trong vòng dưới 5 phút mà không cần hỗ trợ kỹ thuật.
- **SC-006**: Trang tab "Chấm Công" hoạt động bình thường trên các trình duyệt phổ biến (Chrome, Safari, Firefox) trên cả thiết bị di động và máy tính.
- **SC-007**: 100% thao tác check-in đều có `request_ip` được ghi nhận vào bản ghi. Với cơ sở bật chế độ "Bắt buộc", 100% check-in từ IP không hợp lệ bị từ chối.

---

## Assumptions

- Dự án đang dùng Odoo 19 Community. Controller `trcf_shift_registration_controller.py` là nơi sẽ thêm route và logic mới.
- Model `hr.attendance` đã được extend trong `trcf_hr_attendance.py` — sẽ thêm các geo-field và ip-field vào đây.
- Cấu hình Geofence sẽ dùng model mới `trcf.geo.location` thay vì nhét vào `res.config.settings` để hỗ trợ multi-location.
- Tọa độ GPS từ browser có độ chính xác đủ tốt (< 50m) trong điều kiện ngoài trời hoặc trong tòa nhà có wifi-assisted positioning.
- Không yêu cầu native app (iOS/Android) — chỉ dùng browser PWA-compatible.
- **Fake time**: Được xử lý hoàn toàn ở tầng server — timestamp luôn là giờ server, không phụ thuộc client.
- **Fake GPS**: Được xử lý qua cơ chế flag (`geo_suspicious`) dựa trên accuracy và velocity — không thể chặn 100% nhưng đủ để HR phát hiện và xử lý.
- **Public IP**: Server đọc IP từ `REMOTE_ADDR` xác nhận bởi reverse proxy (nginx), không tin vào giá trị `X-Forwarded-For` do client tự gửi. Giảm đầu ra giả mạo IP. Nếu Odoo chạy sau nginx với `proxy_mode = True`, lấy rightmost trusted hop từ `X-Forwarded-For` được nginx append.
- **IP văn phòng**: Giả định public IP của đường truyền WiFi văn phòng là cố định (static IP từ ISP) hoặc thay đổi ít. Admin chịu trách nhiệm cập nhật danh sách IP khi ISP thay đổi.

---

## Out of Scope

- Hiển thị bản đồ trực quan trên tab check-in của nhân viên (tab "Chấm Công") — chỉ dùng chỉ số khoảng cách text; bản đồ tương tác chỉ có ở trang cấu hình admin.
- Thông báo push (Push Notification) nhắc nhân viên check-in/out.
- Chấm công ngoại tuyến (offline attendance rồi đồng bộ sau).
- Báo cáo thống kê chi tiết về GPS/IP suspicious (dùng filter trong list view Odoo backend).
- Geo-IP lookup (tra cứu quốc gia/thành phố từ IP) — chỉ lưu IP thô, không phân tích địa lý.
- Certificate pinning hoặc anti-VPN nâng cao — lớp kiểm tra IP là đủ cho MVP.
