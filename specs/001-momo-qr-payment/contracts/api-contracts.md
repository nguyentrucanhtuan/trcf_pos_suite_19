# Contracts: MoMo API & Internal Interfaces

**Branch**: `001-momo-qr-payment` | **Date**: 2026-03-02

---

## 1. External: MoMo Business API v3 (M4B)

### 1a. Create Payment — Tạo QR Code

```
POST https://payment.momo.vn/v2/gateway/api/create        (production)
POST https://test-payment.momo.vn/v2/gateway/api/create   (sandbox)
Content-Type: application/json

Request:
{
  "partnerCode": "string",
  "requestId": "uuid",
  "amount": 50000,
  "orderId": "POS001-abc12345",  ← format: [0-9a-zA-Z-_.:]+
  "orderInfo": "CFT{orderId}",
  "redirectUrl": "https://example.com",
  "ipnUrl": "https://yourodoo.com/momo/ipn",
  "requestType": "payWithMethod",
  "lang": "vi",
  "signature": "hmac_sha256_hex"  ← HMAC của raw string (alphabetical)
}

Response (success):
{
  "resultCode": 0,
  "qrCodeUrl": "https://qr.momo.vn/...",  ← deep link để render QR
  "payUrl": "https://payment.momo.vn/...",
  "deeplink": "momo://...",
  "requestId": "..."
}

Response (error):
{
  "resultCode": 13,   ← non-zero
  "message": "Merchant not found"
}
```

**HMAC Raw String Format** (alphabetical, dùng cho cả create và verify IPN):
```
accessKey=...&amount=...&extraData=...&message=...&orderId=...
&orderInfo=...&orderType=...&partnerCode=...&payType=...
&requestId=...&responseTime=...&resultCode=...&transId=...
```

### 1b. Query Payment Status

```
POST https://payment.momo.vn/v2/gateway/api/query
Content-Type: application/json

Request:
{
  "partnerCode": "string",
  "requestId": "uuid_new",
  "orderId": "momo_order_id",
  "signature": "hmac_sha256_hex"
}

Response:
{
  "resultCode": 0,      ← 0=success, 1000/9000=pending, others=failed
  "transId": 123456,
  "amount": 50000,
  "message": "..."
}
```

---

## 2. Internal: Odoo HTTP Controller

### 2a. POST `/momo/ipn` — MoMo Webhook

```
Method: POST
Auth: public (csrf=False — justified: external MoMo webhook without Odoo session)
Content-Type: application/json

MoMo sends:
{
  "partnerCode": "...",
  "orderId": "momo_order_id",
  "requestId": "...",
  "amount": 50000,
  "resultCode": 0,
  "message": "Successful",
  "transId": 123456,
  "signature": "hmac_sha256_hex",
  "orderInfo": "...",
  "orderType": "...",
  "payType": "...",
  "responseTime": 1234567890,
  "extraData": ""
}

Validation:
  - Verify HMAC-SHA256 signature
  - If invalid: log warning, return 204 (DO NOT process)
  - If valid: update trcf.momo.transaction, send bus notification

Response: 204 No Content (always, to prevent MoMo retry)
```

### 2b. POST `/pos/momo/create_payment` — JSONRPC

```
Method: POST (JSONRPC)
Auth: user (POS cashier logged in)
Route type: jsonrpc

Params:
  order_id: string       ← POS order reference
  amount: number         ← amount in VND (integer)
  order_info: string     ← optional description
  session_id: int        ← pos.session.id
  config_id: int         ← pos.config.id

Returns:
{
  "success": true,
  "qr_code_url": "https://qr.momo.vn/...",  ← render với local QR library
  "momo_order_id": "POS001-abc12345",
  "result_code": 0,
  "message": "..."
}

Error returns:
{
  "success": false,
  "qr_code_url": "",
  "result_code": -1,
  "message": "MoMo chưa được cấu hình..."
}
```

### 2c. POST `/pos/momo/check_payment_status` — JSONRPC

```
Method: POST (JSONRPC)
Auth: user

Params:
  momo_order_id: string

Returns:
{
  "success": bool,
  "status": "pending" | "success" | "failed" | "not_found" | "error",
  "result_code": int,
  "message": string,
  "trans_id": string
}
```

---

## 3. Internal: OWL ↔ Odoo Bus

### Bus Notification: `MOMO_PAYMENT_SUCCESS`

```
Channel: config.access_token  (unique per POS config)
Notification name: "{access_token}-MOMO_PAYMENT_SUCCESS"

Payload:
{
  "pos_order_ref": "POS-0001-001",
  "momo_order_id": "POS001-abc12345",
  "amount": 50000,
  "trans_id": "123456789"
}

POS receiver (OWL):
  getOnNotified(busService, accessToken)('MOMO_PAYMENT_SUCCESS', handler)
  → handler calls _handleMomoPaymentSuccess(payload)
  → validates order ref matches pendingOrderId
  → marks payment line done + auto validates order
```
