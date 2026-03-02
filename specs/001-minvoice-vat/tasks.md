# Tasks: Xuất Hóa Đơn Điện Tử VAT qua MInvoice

**Input**: Design documents from `/specs/001-minvoice-vat/`
**Branch**: `001-minvoice-vat` | **Date**: 2026-03-02

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Chạy song song được (file khác nhau, không có dependency)
- **[Story]**: US1/US2/US3 — map với user story trong spec.md
- Tất cả path là tuyệt đối trong module `trcf_minvoice/`

---

## Phase 1: Setup

**Purpose**: Khởi tạo module structure và infrastructure cơ bản

- [ ] T001 Cập nhật `trcf_minvoice/__manifest__.py` — bổ sung `skipped_count` field vào wizard nếu chưa có, kiểm tra dependencies `['point_of_sale', 'website']` đã đủ
- [ ] T002 [P] Cập nhật `trcf_minvoice/security/ir.model.access.csv` — thêm dòng access cho `trcf.vat.send.wizard` và `trcf.vat.send.wizard.line` với quyền read/write/create cho nhóm kế toán
- [ ] T003 [P] Tạo `trcf_minvoice/README.md` — ghi mục đích module, dependencies, hướng dẫn cài đặt và cấu hình MInvoice cơ bản

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Các field và model cốt lõi mà TẤT CẢ user stories đều phụ thuộc

**⚠️ CRITICAL**: Không user story nào có thể bắt đầu trước khi phase này hoàn tất

- [ ] T004 Cập nhật `trcf_minvoice/models/trcf_pos_order_inherit.py` — đảm bảo tất cả 13 fields customer info (`vat_type`, `vat_email`, `vat_tax_id`, `vat_customer_name`, `vat_company_name`, `vat_address`, `vat_phone`, `vat_citizen_id`, `vat_note`, `vat_account_number`, `vat_bank_name`, `vat_estimated_unit_code`, `vat_passport_number`) đã đầy đủ và có string/help tiếng Việt
- [ ] T005 Cập nhật `trcf_minvoice/models/trcf_minvoice_pos_order.py` — đảm bảo `trcf_reference_tax_code` có `index=True, copy=False`, `trcf_is_vat_sent` là computed boolean với `store=True, index=True`. Validate: `_send_single_vat_invoice()` chỉ chạy khi `state in ['paid', 'done']`
- [ ] T006 [P] Cập nhật `trcf_minvoice/models/trcf_vat_send_wizard.py` — thêm field `skipped_count` (computed, số đơn bị skip), update `_compute_counts()` để đếm dòng có `status='skipped'`; thêm logic auto-skip trong `action_rpc_process_line()`: nếu đơn đã có `trcf_reference_tax_code` → set status=`skipped` ngay, không gọi API

**Checkpoint**: `pos.order` đã có đủ VAT fields, wizard có `skipped_count`, auto-skip hoạt động

---

## Phase 3: User Story 1 — Kế Toán Xuất VAT Hàng Loạt (Priority: P1) 🎯 MVP

**Goal**: Kế toán chọn nhiều đơn POS → phát hành hóa đơn VAT → thấy tiến trình realtime → thống kê cuối batch

**Independent Test**: Chọn 3 đơn POS (1 đã có sobaomat, 2 chưa) → nhấn "Phát hành hoá đơn" → wizard hiện → đơn có sobaomat tự skip → 2 đơn còn lại xuất thành công → thống kê: Total=3, Success=2, Skipped=1, Failed=0

### Implementation for User Story 1

- [ ] T007 [P] [US1] Cập nhật `trcf_minvoice/models/trcf_minvoice_pos_order.py` method `action_send_vat_minvoice_api()` — kiểm tra 3 config params (tax_code, invoice_series, api_token) trước khi mở wizard; hiển thị cảnh báo chi tiết nếu thiếu bất kỳ item nào
- [ ] T008 [P] [US1] Cập nhật `trcf_minvoice/models/trcf_minvoice_pos_order.py` method `_send_single_vat_invoice()` — thêm logic detect HTTP 401 (token hết hạn): raise exception riêng `MInvoiceTokenExpiredError` để caller phân biệt với lỗi thông thường
- [ ] T009 [US1] Cập nhật `trcf_minvoice/models/trcf_vat_send_wizard.py` method `action_rpc_process_line()` — xử lý `MInvoiceTokenExpiredError`: set line status=`failed`, error_message="Token hết hạn, vui lòng vào Settings → Lấy Token", set `wizard.state='token_expired'` (thêm selection mới), OWL sẽ detect state này và dừng batch toàn bộ
- [ ] T010 [US1] Cập nhật `trcf_minvoice/views/trcf_order_pending_vat_views.xml` — thêm cột `skipped_count` vào header thống kê wizard (nếu có), đảm bảo button "Phát hành hoá đơn" ở header list view có `confirm="Bạn có chắc muốn tiến hành?"` 
- [ ] T011 [US1] Cập nhật `trcf_minvoice/static/src/js/trcf_vat_send_progress.js` OWL component — sau mỗi `action_rpc_process_line` response, kiểm tra `result.all_done` hoặc `wizard.state == 'token_expired'` để dừng loop; hiển thị thống kê gồm cả `skipped`
- [ ] T012 [US1] Cập nhật `trcf_minvoice/static/src/xml/trcf_vat_send_progress.xml` — thêm hiển thị `Đã bỏ qua (skipped)` trong summary block cuối wizard; hiển thị banner "Token hết hạn" khi `state='token_expired'`

**Checkpoint**: Kế toán có thể xuất hàng loạt, auto-skip, detect token expired — US1 có thể test độc lập

---

## Phase 4: User Story 2 — Nhập Thông Tin Khách Hàng VAT (Priority: P2)

**Goal**: Khách hàng tự điền thông tin VAT qua link công khai; form bị khóa sau khi hóa đơn đã phát hành

**Independent Test**: Truy cập `/vat_info_form/POS001` ẩn danh → điền info "Doanh nghiệp" → submit → trang cảm ơn → kiểm tra POS order lưu đúng. Test lock: truy cập lại sau khi có sobaomat → form hiển thị trạng thái khóa.

### Implementation for User Story 2

- [ ] T013 [P] [US2] Cập nhật `trcf_minvoice/controllers/trcf_vat_controller.py` route `GET /vat_info_form/<pos_reference>` — thêm check: nếu `order.trcf_reference_tax_code` tồn tại → truyền `is_locked=True` vào context template thay vì redirect
- [ ] T014 [P] [US2] Cập nhật `trcf_minvoice/controllers/trcf_vat_controller.py` route `POST /vat_info_submit` — thêm guard: nếu order đã có sobaomat → trả về thông báo lỗi "Hóa đơn đã được phát hành, không thể chỉnh sửa thông tin" thay vì ghi vào DB
- [ ] T015 [US2] Cập nhật `trcf_minvoice/views/trcf_vat_info_form.xml` QWeb template `vat_info_form_template` — thêm conditional block: khi `is_locked=True` hiển thị banner "🔒 Hóa đơn đã được phát hành, không thể chỉnh sửa thông tin" + ẩn form submit; khi `is_locked=False` hiển thị form bình thường
- [ ] T016 [US2] Cập nhật `trcf_minvoice/views/trcf_vat_info_form.xml` — đảm bảo form hiển thị đúng 3 loại: fields Doanh nghiệp (MST, tên công ty, địa chỉ, email, tài khoản ngân hàng), Cá nhân (tên, CCCD/hộ chiếu, địa chỉ, email), Vãng lai (thông báo "Không cần thông tin thêm"); dùng JavaScript đơn giản để show/hide fields theo `vat_type` selection
- [ ] T017 [US2] Kiểm tra `trcf_minvoice/views/trcf_order_pos_info.xml` — đảm bảo link `/vat_info_form/<pos_reference>` hiển thị đúng trong form view của POS order backend để thu ngân có thể copy/share link cho khách

**Checkpoint**: Public form hoạt động cho cả 3 loại khách, form lock sau khi xuất VAT

---

## Phase 5: User Story 3 — Admin Cấu Hình Kết Nối MInvoice (Priority: P3)

**Goal**: Admin có thể cấu hình credentials, lấy token và series tự động từ Settings

**Independent Test**: Vào Settings → điền MST/Username/Password → nhấn "Lấy Token" → thành công → nhấn "Lấy Series" → series tự động điền → Save → vào màn hình xuất VAT, không còn cảnh báo thiếu cấu hình

### Implementation for User Story 3

- [ ] T018 [P] [US3] Cập nhật `trcf_minvoice/models/minvoice_res_config_settings.py` — đảm bảo `_compute_minvoice_api_token_display()` che bớt token (chỉ hiện 15 ký tự cuối với prefix `...`); kiểm tra `action_get_minvoice_token()` xử lý đúng HTTP error codes và trả về thông báo lỗi tiếng Việt; kiểm tra `action_get_minvoice_series()` dùng header `"Authorization": f"Bear {token}"` (đúng typo của MInvoice API)
- [ ] T019 [P] [US3] Cập nhật `trcf_minvoice/views/minvoice_res_config_settings_views.xml` — đảm bảo 6 fields hiển thị đúng (tax_code, username, password, api_token_display, invoice_series, company_name); password field dùng `widget="password"`; nút "Lấy Token" và "Lấy Series" hiển thị rõ ràng; thêm help text giải thích từng bước cấu hình
- [ ] T020 [US3] Thêm docstring đầy đủ vào tất cả methods trong `trcf_minvoice/models/minvoice_res_config_settings.py` — mô tả purpose, params, returns, side effects theo Odoo convention

**Checkpoint**: Admin hoàn tất cấu hình trong ≤ 3 phút — US3 test độc lập

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cải thiện ảnh hưởng nhiều user stories

- [ ] T021 [P] Kiểm tra toàn bộ `trcf_minvoice/models/` — đảm bảo không còn `print()` hay debug statements; mọi business method quan trọng có `_logger.info/warning/error` theo pattern `f"📤/✅/⚠️/❌ Order {ref}: ..."` nhất quán
- [ ] T022 [P] Kiểm tra toàn bộ XML views — đảm bảo mọi string user-facing có `_(...)` hoặc trong `<field name>` đúng chuẩn i18n Odoo; không có `t-raw` không justified
- [ ] T023 Kiểm tra bảo mật `trcf_minvoice/controllers/trcf_vat_controller.py` — thêm comment giải thích `csrf=False` justification trên cả 2 routes public; đảm bảo `sudo()` có comment; không có SQL injection risk trong search
- [ ] T024 [P] Chạy Odoo test runner để verify module install/upgrade không có ERROR/CRITICAL: `python odoo-bin -i trcf_minvoice --test-enable --log-level=test`
- [ ] T025 Validate toàn bộ 7 test scenarios trong `quickstart.md` — ghi kết quả pass/fail vào `quickstart.md` dưới mỗi scenario

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Bắt đầu ngay, không phụ thuộc
- **Foundational (Phase 2)**: Phụ thuộc Phase 1 — **BLOCKS tất cả user stories**
- **US1 (Phase 3)**: Phụ thuộc Phase 2
- **US2 (Phase 4)**: Phụ thuộc Phase 2 — **độc lập với US1**
- **US3 (Phase 5)**: Phụ thuộc Phase 2 — **độc lập với US1, US2**
- **Polish (Phase 6)**: Phụ thuộc tất cả US phases hoàn tất

### User Story Dependencies

- **US1 (P1)**: Sau Phase 2; không cần US2, US3
- **US2 (P2)**: Sau Phase 2; không cần US1, US3
- **US3 (P3)**: Sau Phase 2; không cần US1, US2

### Parallel Opportunities

```
Phase 1: T001 → [T002 || T003]
Phase 2: T004 → [T005 || T006]
Phase 3: [T007 || T008] → T009 → T010 → [T011 || T012]
Phase 4: [T013 || T014] → [T015 || T016] → T017
Phase 5: [T018 || T019] → T020
Phase 6: [T021 || T022 || T023 || T024] → T025
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (T001–T003)
2. Phase 2: Foundational (T004–T006) — **không skip**
3. Phase 3: US1 Batch Wizard (T007–T012)
4. **STOP & VALIDATE**: Test 7 scenarios trong quickstart.md #3, #4, #5, #6
5. Nếu pass → deploy staging

### Incremental Delivery

- US1 → Kế toán có thể xuất VAT ngay, kể cả chưa có public form
- US2 → Khách tự điền, giảm tải thu ngân
- US3 → Admin tự cấu hình, không cần dev support

---

## Notes

- Module đã có sẵn code chạy ổn — các tasks chủ yếu là **cập nhật/hoàn thiện** chứ không phải viết từ đầu
- Ưu tiên test Scenario #6 (token expired) vì đây là edge case khó simulate nhất
- Commit sau mỗi phase để dễ rollback
- Kiểm tra Odoo log sau mỗi module upgrade: `grep -E "ERROR|CRITICAL" odoo.log`
