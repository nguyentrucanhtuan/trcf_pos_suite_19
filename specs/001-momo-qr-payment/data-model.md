# Data Model: Tích Hợp Thanh Toán MoMo QR vào Odoo 19 POS

**Branch**: `001-momo-qr-payment` | **Date**: 2026-03-02

## Entity Map

```
pos.payment.method (inherited)
    │ extends
    │   momo_qr_code (Binary - QR tĩnh backup)
    │   momo_partner_code, momo_access_key, momo_secret_key (Char)
    │   momo_test_mode (Boolean)
    │
    │ RPC methods:
    │   create_momo_payment_rpc()
    │   check_momo_payment_status_rpc()
    │
    └── linked via search → trcf.momo.transaction

trcf.momo.transaction (NEW Model)
    │ many2one → pos.session
    │ many2one → pos.config
    │ tracks: momo_order_id, status, trans_id, amount...

[OWL Frontend State - in-memory only]
    momoState: {
        showQr, qrCode, loading,
        pendingOrderId, momoOrderId,
        pollingInterval, isExpired
    }
```

---

## 1. `pos.payment.method` — Extended MoMo Fields

Mở rộng bảng `pos_payment_method` qua `_inherit`.

| Field | Type | Description | Constraint |
|-------|------|-------------|-----------|
| `momo_qr_code` | Binary | Ảnh QR tĩnh backup (base64) | Nullable |
| `momo_partner_code` | Char | Partner Code từ M4B | Nullable (required khi dùng API) |
| `momo_access_key` | Char | Access Key từ M4B | Nullable |
| `momo_secret_key` | Char | Secret Key từ M4B | Nullable, `password=True` in view |
| `momo_test_mode` | Boolean | Dùng sandbox MoMo | Default: `True` |

**Validation Rules**:
- Nếu `use_payment_terminal == 'trcf_momo'` và `momo_partner_code` trống → `create_momo_payment_rpc()` trả lỗi, fallback về QR tĩnh.
- Khi tạo QR, tất cả 3 keys (partner_code, access_key, secret_key) đều cần. Nếu thiếu bất kỳ → error response ngay, không call API.

---

## 2. `trcf.momo.transaction` — Giao Dịch MoMo

Model chính, lưu lịch sử định kỳ mỗi lần tạo QR.

| Field | Type | Description | Index |
|-------|------|-------------|-------|
| `pos_order_ref` | Char | Mã đơn POS gốc (e.g. "POS-0001-001") | `index=True` |
| `pos_session_id` | Many2one → `pos.session` | POS Session hiện tại | |
| `pos_config_id` | Many2one → `pos.config` | POS Config (dùng để gửi bus notification đúng kênh) | |
| `momo_order_id` | Char | Mã giao dịch MoMo (có timestamp suffix) — unique per QR | `required=True`, `index=True` |
| `momo_request_id` | Char | Request ID MoMo (dùng khi query status) | |
| `amount` | Float | Số tiền thanh toán (VND) | |
| `status` | Selection | `pending` / `success` / `failed` / `expired` | Default: `pending` |
| `result_code` | Integer | Result code từ MoMo API/IPN | |
| `message` | Char | Thông báo từ MoMo | |
| `trans_id` | Char | Transaction ID MoMo (sau khi success) | |
| `payment_time` | Datetime | Thời điểm thanh toán thành công | |

**State Transitions**:
```
pending → success   (IPN result_code=0 hoặc polling result_code=0)
pending → failed    (IPN result_code ≠ 0, 1000, 9000)
pending → expired   (future: cleanup job sau N ngày — ngoài scope hiện tại)
```

**Key Rules**:
- `momo_order_id` được tạo: `{clean_pos_ref}_{uuid4_hex8}` (đảm bảo unique)
- Một đơn POS có thể có nhiều transaction (thu ngân tạo QR mới nhiều lần) — chỉ 1 transaction thành công
- Khi status đã là `success` hoặc `failed` → polling/IPN trả về cached status, không gọi API thêm

**Bus Notification** (trigger khi `status → success`):
```python
channel      = config.access_token
notification = f"{access_token}-MOMO_PAYMENT_SUCCESS"
payload      = { pos_order_ref, momo_order_id, amount, trans_id }
```

---

## 3. OWL Frontend State (In-Memory)

Không lưu DB — chỉ tồn tại trong POS session.

| State Key | Type | Description |
|-----------|------|-------------|
| `showQr` | Boolean | Có đang hiển thị QR panel không |
| `qrCode` | String | Data URL ảnh QR hiện tại (placeholder / loading / dynamic / success / static) |
| `loading` | Boolean | Đang gọi API tạo QR |
| `pendingOrderId` | String | Mã đơn POS đang chờ thanh toán |
| `momoOrderId` | String | `momo_order_id` MoMo (dùng cho polling + matching) |
| `pollingInterval` | Timer | setInterval handle (cleanup khi unmount) |
| `isExpired` | Boolean | True sau 5 phút polling không có kết quả → hiển thị timeout UX |

**QR Display State Machine**:
```
Initial: DEFAULT_MOMO_QR_SVG (placeholder)
  ↓ Thu ngân chọn MoMo
Loading: LOADING_QR_SVG (spinner)
  ↓ API thành công
Dynamic: generateQRCodeLocal(deeplink_url)  ← thư viện local
  ↓ Thanh toán thành công (IPN hoặc polling)
Success: SUCCESS_QR_SVG (dấu tích xanh)

  ↓ API thất bại HOẶC thiếu credentials
Static: momo_qr_code (base64 từ Payment Method) hoặc DEFAULT_MOMO_QR_SVG

  ↓ Polling 5 phút không có kết quả
Expired: hiển thị banner "QR đã hết hiệu lực" + nút "Tạo QR Mới"
```
