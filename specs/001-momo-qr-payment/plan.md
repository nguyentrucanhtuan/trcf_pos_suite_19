# Implementation Plan: Tích Hợp Thanh Toán MoMo QR vào Odoo 19 POS

**Branch**: `001-momo-qr-payment` | **Date**: 2026-03-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-momo-qr-payment/spec.md`

## Summary

Module mở rộng Odoo 19 POS để thu ngân nhận thanh toán qua MoMo QR Code động. Kỹ thuật: extend `pos.payment.method` lưu M4B credentials, `trcf.momo.transaction` model theo dõi trạng thái giao dịch, HTTP controller cho IPN webhook + 2 JSONRPC routes, OWL patch trên `PaymentScreen` để hiển thị QR, lắng nghe bus notification và auto-validate đơn. QR được render bằng thư viện local (không phụ thuộc external service). IPN được xác thực HMAC-SHA256 strict.

## Technical Context

**Language/Version**: Python 3.12 / Odoo 19 Community  
**Primary Dependencies**: `point_of_sale` (Odoo built-in); `requests` (MoMo API calls); `qrcode` hoặc JS library client-side (render QR local)  
**Storage**: PostgreSQL — bảng `trcf_momo_transaction` mới; extend `pos_payment_method` với MoMo fields  
**Testing**: Odoo test runner (`odoo-bin -i trcf_payment_momo --test-enable`); MoMo sandbox environment  
**Target Platform**: Linux server (Odoo backend + IPN webhook) + Browser (OWL POS frontend)  
**Project Type**: Odoo custom module (backend + POS JS frontend)  
**Performance Goals**: QR xuất hiện ≤ 5 giây; auto-validate ≤ 10 giây sau khi khách thanh toán  
**Constraints**: IPN cần public URL (web.base.url reachable). Tiền tệ VND nguyên. MoMo orderId format strict `[0-9a-zA-Z-_.:]+`. Polling 3s × tối đa 100 lần.  
**Scale/Scope**: Chuỗi F&B ≤ 10 cửa hàng, ~50-200 giao dịch MoMo/ngày

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Gate Question | Status |
|---|-----------|---------------|--------|
| I | Odoo 19-First | Odoo core không có tích hợp MoMo. Dùng `_inherit` chuẩn, `PaymentInterface`, `register_payment_method`, `patch()` đúng Odoo 19 pattern. | ✅ |
| II | Backend UX/UI | Form cấu hình credentials inherit `pos.payment.method` view chuẩn, không override widget. Secret Key dùng `password="True"`. | ✅ |
| III | Frontend UX/UI | OWL component patch `PaymentScreen.prototype` chuẩn Odoo 19 (hooks, useState, onWillUnmount). QR render local không dùng React/Vue. | ✅ |
| IV | Code Quality | PEP8, docstring trên `create_momo_payment_rpc`, `check_momo_payment_status_rpc`, `update_from_ipn`, `_verify_ipn_signature`. Không có print/pdb. README.md. | ✅ |
| V | Performance | `trcf.momo.transaction` search có domain + index=True trên `momo_order_id`, `pos_order_ref`. Polling cleanup khi unmount. | ✅ |
| VI | Maintainability | MoMoAPI tách thành class riêng (`momo_api.py`). Credentials gắn với Payment Method record (không `ir.config_parameter` — đúng vì multi-terminal). Migration nếu thêm field. | ✅ |
| S | Security | IPN signature HMAC-SHA256 strict (reject if invalid). `csrf=False` justified (public IPN endpoint). `sudo()` trong controller có comment. Credentials lưu trong DB record (không log). | ✅ |

**Constitution Check Result: ✅ ALL PASS** — Không có vi phạm, không cần Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/001-momo-qr-payment/
├── plan.md              ✅ (this file)
├── research.md          ✅ (Phase 0 output)
├── data-model.md        ✅ (Phase 1 output)
├── quickstart.md        ✅ (Phase 1 output)
├── contracts/           ✅ (Phase 1 output)
└── tasks.md             (Phase 2 — /speckit.tasks command)
```

### Source Code (Odoo module layout)

```text
trcf_payment_momo/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── momo_api.py                    # Class MoMoAPI — HMAC signing, HTTP calls
│   ├── momo_transaction.py            # trcf.momo.transaction model
│   └── trcf_pos_payment_method.py     # pos.payment.method inherit — credentials + RPC methods
├── controllers/
│   ├── __init__.py
│   └── momo_controller.py             # IPN /momo/ipn + 2 JSONRPC routes POS
├── views/
│   ├── trcf_momo_payment_views.xml    # Payment Method form — credentials config
│   └── trcf_momo_payment_templates.xml # Optional backend template
├── static/src/
│   ├── js/
│   │   └── momo_terminal.js           # OWL patch PaymentScreen — QR display, polling, bus
│   └── xml/
│       └── momo_payment_screen.xml    # QWeb template — QR display block
└── security/
    └── ir.model.access.csv            # trcf.momo.transaction access rules
```

**Structure Decision**: Single Odoo module. Backend Python (model + controller) + POS OWL JavaScript frontend. Pattern chuẩn Odoo 19 POS extension.
