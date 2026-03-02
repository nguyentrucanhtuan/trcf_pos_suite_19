# Contracts: MInvoice API & Internal Interfaces

**Branch**: `001-minvoice-vat` | **Date**: 2026-03-02

---

## 1. External: MInvoice REST API

### 1a. Login — Lấy Bearer Token

```
POST https://{tax_code}.minvoice.app/api/Account/Login
Content-Type: application/json

Request:
{
  "username": "string",
  "password": "string",
  "ma_dvcs": "VP"
}

Response (success):
{
  "code": "00",
  "token": "eyJ..."
}

Response (error):
{
  "code": "01",
  "message": "Tên đăng nhập hoặc mật khẩu không đúng"
}
```

### 1b. Save Invoice — Phát Hành Hóa Đơn

```
POST https://{tax_code}.minvoice.app/api/InvoiceApi78/Save
Content-Type: application/json
Authorization: Bearer {token}

Request body: xem data-model.md section MInvoice Payload

Response (success):
{
  "ok": true,
  "code": "00",
  "data": {
    "sobaomat": "ABC123XYZ"
  }
}

Response (error):
{
  "ok": false,
  "code": "XX",
  "message": "Mô tả lỗi"
}

Response (token expired): HTTP 401 Unauthorized
```

### 1c. Get Invoice Series

```
GET https://{tax_code}.minvoice.app/api/Invoice68/GetTypeInvoiceSeries
Authorization: Bear {token}   ← NOTE: typo "Bear" (không phải "Bearer") — đây là behavior thực tế của MInvoice

Response (success):
{
  "ok": true,
  "code": "00",
  "data": [
    { "value": "1C25MYY", "text": "Ký hiệu hóa đơn" }
  ]
}
```

---

## 2. Internal: Odoo HTTP Controller (Public)

### 2a. GET `/vat_info_form/<pos_reference>`

```
Method: GET
Auth: public (no login required)
Parameters: pos_reference (URL path)

Response:
- 200: Render QWeb template trcf_minvoice.vat_info_form_template
  - Context: { pos_reference, order_id }
  - If order has sobaomat: render locked form with message "Hóa đơn đã phát hành"
- 404/error: Render trcf_minvoice.vat_info_error_template
```

### 2b. POST `/vat_info_submit`

```
Method: POST
Auth: public (csrf=False — justified: public form without Odoo session)
Content-Type: application/x-www-form-urlencoded

Form fields:
  pos_reference: string (required)
  vat_type: 'no_vat' | 'company' | 'individual'
  vat_customer_name: string
  vat_company_name: string (company only)
  vat_tax_id: string (company only)
  vat_address: string
  vat_email: string
  vat_phone: string
  vat_citizen_id: string (individual only)
  vat_passport_number: string (individual only)
  vat_account_number: string (company only)
  vat_bank_name: string (company only)
  vat_note: string

Response:
- Order found + no sobaomat: Save fields, render vat_info_thanks_template
- Order has sobaomat: Render error — "Hóa đơn đã phát hành, không thể chỉnh sửa"
- Order not found: Render vat_info_error_template
```

---

## 3. Internal: Odoo RPC Methods (Backend → Wizard)

### 3a. `action_rpc_process_line(line_id)`

```
Model: trcf.vat.send.wizard
Called by: OWL component trcf_vat_send_progress.js

Input: line_id (integer)
Output: {
  "success": bool,
  "status": "success" | "failed" | "skipped",
  "vat_code": string | null,
  "error_message": string | null,
  "all_done": bool,
  "counts": {
    "success": int,
    "failed": int,
    "pending": int,
    "skipped": int
  }
}
```
