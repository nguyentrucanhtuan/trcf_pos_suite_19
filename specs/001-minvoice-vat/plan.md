# Implementation Plan: Xuất Hóa Đơn Điện Tử VAT qua MInvoice

**Branch**: `001-minvoice-vat` | **Date**: 2026-03-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-minvoice-vat/spec.md`

## Summary

Module mở rộng Odoo 19 POS để tích hợp xuất hóa đơn điện tử VAT qua nền tảng MInvoice. Kế toán có thể phát hành hàng loạt từ backend, khách hàng tự điền thông tin qua public web form. Kỹ thuật: inherit `pos.order` để lưu thông tin VAT + sobaomat, `res.config.settings` cho cấu hình API, TransientModel wizard + OWL component cho tiến trình realtime, HTTP controller cho public form.

## Technical Context

**Language/Version**: Python 3.12 / Odoo 19 Community  
**Primary Dependencies**: `point_of_sale`, `website` (Odoo built-in); `requests` (HTTP calls đến MInvoice API)  
**Storage**: PostgreSQL — extend `pos.order` table với các trường VAT; `ir.config_parameter` cho credentials  
**Testing**: Odoo test runner (`odoo-bin -i trcf_minvoice --test-enable`)  
**Target Platform**: Linux server (Odoo backend) + Browser (OWL wizard + public web form)  
**Project Type**: Odoo custom module (backend module + website controller)  
**Performance Goals**: Xuất 1 hóa đơn ≤ 10 giây (bao gồm API call); batch 10 đơn ≤ 5 phút  
**Constraints**: Token MInvoice có thể hết hạn — detect và dừng batch sớm. Public form không cần auth. Timeout API 30 giây.  
**Scale/Scope**: Chuỗi F&B ≤ 10 cửa hàng, ~100 đơn/ngày/cửa hàng cần xuất VAT

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Principle | Gate Question | Status |
|---|-----------|---------------|--------|
| I | Odoo 19-First | Odoo core không có tính năng phát hành hóa đơn điện tử VN (MInvoice). Dùng `_inherit` đúng chuẩn, không override core. | ✅ |
| II | Backend UX/UI | Dùng standard list/form view Odoo, action button header, wizard form. Không override widget chuẩn. | ✅ |
| III | Frontend UX/UI | Wizard tiến trình dùng OWL component + QWeb template. Public form dùng Website controller + QWeb. | ✅ |
| IV | Code Quality | PEP8, docstring cho tất cả business methods, không có print/pdb, có README.md. | ✅ |
| V | Performance | ORM search có domain/fields/limit. Batch wizard xử lý từng đơn tuần tự (không loop lớn). `trcf_reference_tax_code` có `index=True`. | ✅ |
| VI | Maintainability | Credentials qua `ir.config_parameter`. MInvoice API call tách thành service method `_send_single_vat_invoice()`. Migration script nếu thêm field. | ✅ |
| S | Security | Public controller `csrf=False` có justification (public form không có session). `t-esc` cho tất cả user content. `ir.model.access.csv` đầy đủ. `sudo()` chỉ ở public controller với comment. | ✅ |

**Constitution Check Result: ✅ ALL PASS** — Không có vi phạm cần justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-minvoice-vat/
├── plan.md              ✅ (this file)
├── research.md          ✅ (Phase 0 output)
├── data-model.md        ✅ (Phase 1 output)
├── quickstart.md        ✅ (Phase 1 output)
├── contracts/           ✅ (Phase 1 output)
└── tasks.md             (Phase 2 — /speckit.tasks command)
```

### Source Code (Odoo module layout)

```text
trcf_minvoice/
├── __manifest__.py
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── minvoice_res_config_settings.py   # res.config.settings inherit — API credentials
│   ├── trcf_minvoice_pos_order.py        # pos.order inherit — VAT fields + send logic
│   ├── trcf_pos_order_inherit.py         # pos.order inherit — vat_type, buyer info fields
│   └── trcf_vat_send_wizard.py           # TransientModel wizard + wizard line
├── controllers/
│   ├── __init__.py
│   └── trcf_vat_controller.py            # Public HTTP routes: /vat_info_form, /vat_info_submit
├── views/
│   ├── minvoice_res_config_settings_views.xml
│   ├── trcf_vat_send_wizard_views.xml
│   ├── trcf_order_pending_vat_views.xml
│   ├── trcf_order_pending_vat_search_view.xml
│   ├── trcf_order_pos_info.xml
│   └── trcf_vat_info_form.xml             # Public web form (QWeb)
├── static/src/
│   ├── js/
│   │   └── trcf_vat_send_progress.js      # OWL component — batch progress
│   └── xml/
│       └── trcf_vat_send_progress.xml     # OWL template
└── security/
    └── ir.model.access.csv
```

**Structure Decision**: Single Odoo module. Backend (models + views) + OWL frontend cho wizard + Website controller cho public form. Đây là pattern chuẩn cho Odoo POS extension module.
