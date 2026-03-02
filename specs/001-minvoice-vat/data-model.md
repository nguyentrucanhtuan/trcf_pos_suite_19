# Data Model: Xuất Hóa Đơn Điện Tử VAT qua MInvoice

**Branch**: `001-minvoice-vat` | **Date**: 2026-03-02

## Entity Map

```
res.config.settings (TransientModel)
    │ inherits
    ▼
[MInvoice Settings Fields]
    minvoice_tax_code, minvoice_username, minvoice_password
    minvoice_api_token, minvoice_invoice_series, minvoice_company_name

pos.order (inherited x2)
    │ extends (trcf_pos_order_inherit.py)
    │   vat_type, vat_email, vat_tax_id, vat_customer_name
    │   vat_company_name, vat_address, vat_phone, vat_citizen_id
    │   vat_note, vat_account_number, vat_bank_name
    │   vat_estimated_unit_code, vat_passport_number
    │
    │ extends (trcf_minvoice_pos_order.py)
    │   trcf_reference_tax_code (sobaomat), trcf_is_vat_sent (computed)
    │
    └── line: pos.order.line (used for invoice details — no changes needed)

trcf.vat.send.wizard (TransientModel)
    │ one2many
    ▼
trcf.vat.send.wizard.line (TransientModel)
    │ many2one → pos.order
```

---

## 1. `pos.order` — Extended VAT Buyer Fields

Mở rộng bảng `pos_order` qua `_inherit`.

### Buyer Information Fields (`trcf_pos_order_inherit.py`)

| Field | Type | Description | Constraint |
|-------|------|-------------|-----------|
| `vat_type` | Selection | Loại khách: `no_vat`, `company`, `individual` | Default: `no_vat` |
| `vat_customer_name` | Char | Tên khách hàng (cá nhân hoặc người đại diện) | |
| `vat_company_name` | Char | Tên công ty (chỉ dùng khi `vat_type=company`) | |
| `vat_tax_id` | Char | Mã số thuế công ty | |
| `vat_address` | Char | Địa chỉ người mua | |
| `vat_email` | Char | Email nhận hóa đơn | |
| `vat_phone` | Char | Số điện thoại | |
| `vat_citizen_id` | Char | Căn cước công dân (cá nhân) | |
| `vat_passport_number` | Char | Số hộ chiếu (cá nhân, thay thế CCCD) | |
| `vat_account_number` | Char | Số tài khoản ngân hàng (công ty) | |
| `vat_bank_name` | Char | Tên ngân hàng (công ty) | |
| `vat_estimated_unit_code` | Char | Mã đơn vị dự toán (đặc thù VN) | |
| `vat_note` | Text | Ghi chú thêm | |

### VAT Status Fields (`trcf_minvoice_pos_order.py`)

| Field | Type | Description | Index |
|-------|------|-------------|-------|
| `trcf_reference_tax_code` | Char | Mã bảo mật hóa đơn (sobaomat) từ MInvoice | `index=True` |
| `trcf_is_vat_sent` | Boolean | Computed: `True` khi `trcf_reference_tax_code` có giá trị | `store=True`, `index=True` |

**State Transitions (`trcf_is_vat_sent`)**:
```
False (default) → True (khi sobaomat được lưu thành công)
Không có chiều ngược lại — hóa đơn đã phát hành không thể hủy bỏ trong app
```

**Validation Rules**:
- Chỉ cho phép gọi `_send_single_vat_invoice()` khi `state in ['paid', 'done']`
- Đơn đã có `trcf_reference_tax_code` → auto-skip trong batch (không gọi API)

---

## 2. `trcf.vat.send.wizard` — Batch Progress Wizard

TransientModel (không lưu vĩnh viễn).

| Field | Type | Description |
|-------|------|-------------|
| `order_ids` | Many2many → `pos.order` | Danh sách đơn cần xuất |
| `line_ids` | One2many → `trcf.vat.send.wizard.line` | Tiến trình từng đơn |
| `total_count` | Integer (computed) | Tổng số đơn |
| `success_count` | Integer (computed) | Số đơn thành công |
| `failed_count` | Integer (computed) | Số đơn thất bại |
| `pending_count` | Integer (computed) | Số đơn chờ xử lý |
| `skipped_count` | Integer (computed) | Số đơn bị skip (đã có sobaomat) |
| `state` | Selection | `draft` → `processing` → `done` |

---

## 3. `trcf.vat.send.wizard.line` — Per-Order Progress

| Field | Type | Description |
|-------|------|-------------|
| `wizard_id` | Many2one → `trcf.vat.send.wizard` | Parent wizard |
| `order_id` | Many2one → `pos.order` | Đơn hàng |
| `order_ref` | Char (related) | `pos.order.pos_reference` |
| `order_amount` | Monetary (related) | `pos.order.amount_total` |
| `status` | Selection | `pending` / `processing` / `success` / `failed` / `skipped` |
| `error_message` | Text | Thông báo lỗi từ MInvoice API |
| `vat_code` | Char | sobaomat sau khi thành công |

**Status Transitions**:
```
pending → skipped    (đơn đã có sobaomat — auto-skip)
pending → processing → success  (gọi API thành công)
pending → processing → failed   (API lỗi hoặc timeout)
processing → failed             (token hết hạn → dừng batch)
```

---

## 4. `res.config.settings` — MInvoice Credentials

Lưu qua `ir.config_parameter` (không lưu vào bảng `res_config_settings`).

| Config Key | Mô tả |
|-----------|-------|
| `trcf_minvoice.tax_code` | Mã số thuế (subdomain MInvoice) |
| `trcf_minvoice.username` | Username đăng nhập MInvoice |
| `trcf_minvoice.password` | Password đăng nhập MInvoice |
| `trcf_minvoice.api_token` | Bearer token (được lấy tự động) |
| `trcf_minvoice.invoice_series` | Ký hiệu hóa đơn (e.g., `1C25MYY`) |
| `trcf_minvoice.company_name` | Tên cửa hàng/công ty trên hóa đơn |

**Security**: `api_token` display che bớt 15 ký tự cuối. Password không hiển thị lại sau khi lưu.
