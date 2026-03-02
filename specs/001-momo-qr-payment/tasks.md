# Tasks: Tích Hợp Thanh Toán MoMo QR vào Odoo 19 POS

**Input**: Design documents from `/specs/001-momo-qr-payment/`
**Branch**: `001-momo-qr-payment` | **Date**: 2026-03-02

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Chạy song song được (file khác nhau, không có dependency)
- **[Story]**: US1/US2/US3 — map với user story trong spec.md
- Path trong module `trcf_payment_momo/`

---

## Phase 1: Setup

**Purpose**: Khởi tạo module structure và security infrastructure

- [ ] T001 Kiểm tra và cập nhật `trcf_payment_momo/__manifest__.py` — đảm bảo dependencies `['point_of_sale']`, assets JS/XML đăng ký đúng, version và author đầy đủ
- [ ] T002 [P] Cập nhật `trcf_payment_momo/security/ir.model.access.csv` — thêm dòng access cho `trcf.momo.transaction` với quyền read/write/create/unlink cho nhóm `base.group_user`; đảm bảo `pos.payment.method` không cần thêm row (inherit sẵn)
- [ ] T003 [P] Tạo `trcf_payment_momo/README.md` — ghi mục đích module, prerequisites (M4B account, public URL cho IPN), hướng dẫn cài đặt và cấu hình từng bước

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Model giao dịch và class MoMoAPI — nền tảng cho TẤT CẢ user stories

**⚠️ CRITICAL**: Không user story nào có thể bắt đầu trước khi phase này hoàn tất

- [ ] T004 Cập nhật `trcf_payment_momo/models/momo_transaction.py` — đảm bảo model `trcf.momo.transaction` có đủ 13 fields theo data-model.md; `momo_order_id` và `pos_order_ref` có `index=True`; `create_pending_transaction()` nhận `request_id`; `update_from_ipn()` chỉ cập nhật khi status còn `pending` (idempotent)
- [ ] T005 [P] Cập nhật `trcf_payment_momo/models/momo_api.py` class `MoMoAPI` — đảm bảo HMAC-SHA256 raw string đúng thứ tự alphabetical theo MoMo API v3 spec trong contracts/api-contracts.md; `create_payment()` map đúng `qrCodeUrl` từ response; `query_payment_status()` nhận `request_id` mới (không dùng request_id cũ)
- [ ] T006 [P] Cập nhật `trcf_payment_momo/models/trcf_pos_payment_method.py` — đảm bảo `create_momo_payment_rpc()` kiểm tra đủ 3 credentials trước khi khởi tạo MoMoAPI; tạo transaction record SAU khi API thành công (không trước); `check_momo_payment_status_rpc()` trả về cached status nếu đã success/failed

**Checkpoint**: MoMoAPI class hoạt động với sandbox, transaction record tạo/cập nhật đúng

---

## Phase 3: User Story 1 — Thu Ngân Nhận Thanh Toán MoMo QR (Priority: P1) 🎯 MVP

**Goal**: Thu ngân chọn MoMo → QR động hiển thị ≤5s → khách quét → auto-validate ≤10s (qua IPN hoặc polling)

**Independent Test**: Scenario 2 + Scenario 3 + Scenario 7 trong quickstart.md — Happy path IPN, polling recover, và no-duplicate guard

### Implementation for User Story 1

- [ ] T007 [P] [US1] Cập nhật `trcf_payment_momo/controllers/momo_controller.py` route `POST /momo/ipn` — thêm STRICT HMAC-SHA256 validation: nếu chữ ký không khớp → trả 204, ghi log warning, KHÔNG cập nhật transaction (FR-017); nếu hợp lệ → gọi `update_from_ipn()` → gọi `_notify_pos_payment_success()`
- [ ] T008 [P] [US1] Cập nhật `trcf_payment_momo/models/momo_transaction.py` method `_notify_pos_payment_success()` — đảm bảo dùng Odoo 19 bus pattern: `bus.bus._sendone(config.access_token, f"{access_token}-MOMO_PAYMENT_SUCCESS", payload)` với đúng payload schema theo contracts/api-contracts.md
- [ ] T009 [US1] Cập nhật `trcf_payment_momo/static/src/js/momo_terminal.js` — thêm `momoState.isExpired = false` vào initial state; sau khi polling kết thúc (pollCount >= maxPolls) set `isExpired = true` thay vì im lặng; thêm method `_resetMomoForNewQr()` để thu ngân tạo lại QR (reset state + gọi lại `addNewPaymentLine` hoặc tạo payment mới)
- [ ] T010 [US1] Cập nhật `trcf_payment_momo/static/src/js/momo_terminal.js` — thay thế `generateQRCodeUrl()` dùng `quickchart.io` bằng cách render QR local: import hoặc inline thư viện `qrcode` (ví dụ `qrcodejs` hoặc `qrcode-svg`) để tạo ảnh QR từ deeplink URL mà không cần internet (FR-018)
- [ ] T011 [US1] Cập nhật `trcf_payment_momo/static/src/xml/momo_payment_screen.xml` (hoặc `trcf_momo_payment_templates.xml`) — thêm block conditional: khi `showMomoExpired` = true hiển thị banner "QR đã hết hiệu lực sau 5 phút" + button `t-on-click="createNewMomoQr"` (FR-016); khi false hiển thị QR image bình thường

**Checkpoint**: US1 test độc lập — Scenario 2, 3, 7 từ quickstart.md pass

---

## Phase 4: User Story 2 — Fallback QR Tĩnh (Priority: P2)

**Goal**: API thất bại hoặc thiếu credentials → QR tĩnh/placeholder hiển thị ngay, không crash

**Independent Test**: Scenario 5 từ quickstart.md — xóa Partner Code → chọn MoMo → QR tĩnh hoặc placeholder SVG hiển thị, không có lỗi

### Implementation for User Story 2

- [ ] T012 [P] [US2] Kiểm tra `trcf_payment_momo/static/src/js/momo_terminal.js` method `addNewPaymentLine()` fallback logic — đảm bảo: (1) khi API fail → hiển thị `momo_qr_code` base64 nếu đã upload, ELSE `DEFAULT_MOMO_QR_SVG`; (2) khi `response.success = false` do thiếu credentials → fallback về QR tĩnh với log warning, không throw error
- [ ] T013 [US2] Kiểm tra constant `DEFAULT_MOMO_QR_SVG` — đảm bảo placeholder SVG hiển thị đúng style (màu MoMo `#a50064`), có text hướng dẫn "Upload QR in Payment Method Settings" để thu ngân biết cần làm gì
- [ ] T014 [US2] Đảm bảo `trcf_payment_momo/views/trcf_momo_payment_views.xml` — field `momo_qr_code` dùng `widget="image"` với options size phù hợp; có `div.alert-warning` hướng dẫn rõ cách lấy QR tĩnh từ app MoMo (Ví → Nhận tiền → QR)

**Checkpoint**: US2 test độc lập — Scenario 5 pass mà không ảnh hưởng US1

---

## Phase 5: User Story 3 — Admin Cấu Hình MoMo Payment Method (Priority: P3)

**Goal**: Admin tạo payment method, nhập credentials M4B, bật sandbox, lưu — POS nhận đúng config

**Independent Test**: Scenario 1 từ quickstart.md — tạo payment method → nhập credentials → Secret Key hiển thị dạng `****` → save → assign vào POS config → vào POS chọn MoMo → không có lỗi missing config

### Implementation for User Story 3

- [ ] T015 [P] [US3] Kiểm tra `trcf_payment_momo/models/trcf_pos_payment_method.py` method `_load_pos_data_fields()` — đảm bảo load `momo_qr_code` và `momo_test_mode` vào POS data (cần thiết cho OWL component biết dùng QR tĩnh hay sandbox); KHÔNG load `momo_secret_key` lên client (bảo mật)
- [ ] T016 [P] [US3] Kiểm tra `trcf_payment_momo/views/trcf_momo_payment_views.xml` — đảm bảo `momo_secret_key` có `password="True"` attribute; group config chỉ hiển thị khi `use_payment_terminal == 'trcf_momo'`; thêm help text giải thích M4B sandbox vs production
- [ ] T017 [US3] Thêm docstring đầy đủ vào `trcf_payment_momo/models/trcf_pos_payment_method.py` — mô tả `create_momo_payment_rpc()`, `check_momo_payment_status_rpc()`, bao gồm params, returns, side effects (tạo transaction record)

**Checkpoint**: US3 test độc lập — Scenario 1 pass; credentials không xuất hiện trong JS/POS client

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Security hardening, logging, và validation cuối

- [ ] T018 [P] Kiểm tra `trcf_payment_momo/controllers/momo_controller.py` — xác nhận `csrf=False` có comment justification rõ ràng trên route IPN; `sudo()` trong controller có comment giải thích; Secret Key không bao giờ được log (`_logger.info`)
- [ ] T019 [P] Kiểm tra toàn bộ `trcf_payment_momo/models/` — đảm bảo: không có `print()`, không có hardcoded credentials, `_logger` dùng đúng level (info cho flow, warning cho abnormal, error cho exception)
- [ ] T020 Kiểm tra `trcf_payment_momo/static/src/js/momo_terminal.js` — đảm bảo `onWillUnmount` cleanup cả polling interval lẫn bus subscription; không có memory leak; `console.error` chỉ còn trong catch blocks thực sự cần thiết
- [ ] T021 [P] Chạy Odoo module upgrade để verify không có ERROR/CRITICAL: `python odoo-bin -u trcf_payment_momo --log-level=test`
- [ ] T022 Validate 7 test scenarios trong `quickstart.md` với MoMo sandbox — ghi kết quả pass/fail vào `quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Bắt đầu ngay
- **Foundational (Phase 2)**: Phụ thuộc Phase 1 — **BLOCKS tất cả US**
- **US1 (Phase 3)**: Phụ thuộc Phase 2
- **US2 (Phase 4)**: Phụ thuộc Phase 2 — **độc lập với US1**
- **US3 (Phase 5)**: Phụ thuộc Phase 2 — **độc lập với US1, US2**
- **Polish (Phase 6)**: Phụ thuộc tất cả US hoàn tất

### Parallel Opportunities

```
Phase 1: T001 → [T002 || T003]
Phase 2: [T004 || T005 || T006]       ← 3 files khác nhau, song song được
Phase 3: [T007 || T008] → T009 → T010 → T011
Phase 4: [T012 || T013 || T014]       ← độc lập nhau
Phase 5: [T015 || T016] → T017
Phase 6: [T018 || T019 || T020 || T021] → T022
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup (T001–T003) — nhanh, ≤ 30 phút
2. Phase 2: Foundational (T004–T006) — **không skip**, là core
3. Phase 3: US1 (T007–T011) — thanh toán hoạt động end-to-end
4. **STOP & VALIDATE**: Test Scenario 2 + 3 + 7 với MoMo sandbox
5. Nếu pass → deploy staging

### Incremental Delivery

- US1 → Thu ngân thanh toán MoMo đầy đủ (QR động + auto-validate)
- US2 → Đảm bảo liên tục khi API gặp sự cố (không mất giao dịch)
- US3 → Admin tự cấu hình (không cần dev support)

---

## Notes

- Module đã có code chạy ổn — tasks chủ yếu là **hoàn thiện gap** từ clarify: strict IPN validation, local QR lib, isExpired state, "Tạo QR Mới" button
- **Quan trọng nhất**: T007 (IPN strict validation) + T010 (local QR library) — 2 thay đổi kiến trúc từ clarify
- Không load `momo_secret_key` lên POS client (T015) — bảo mật quan trọng
- Commit sau mỗi phase, kiểm tra Odoo log
