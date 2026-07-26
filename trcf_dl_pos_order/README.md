# trcf_dl_pos_order — Xoá cứng đơn hàng POS

Thêm nút **Xoá cứng** vào danh sách đơn hàng POS (`/odoo/pos-orders`) để xoá
vĩnh viễn đơn hàng ở mọi trạng thái, bỏ qua ràng buộc ORM của Odoo.

## Cài đặt

```bash
python3 odoo-bin -c odoo19.conf -d <db> -i trcf_dl_pos_order --stop-after-init
```

Sau khi cài, vào **Cài đặt → Người dùng** và tick quyền
*Điểm bán hàng - Thao tác nguy hiểm → Xoá cứng đơn hàng POS* cho người được phép.
Mặc định **không ai** có quyền này, kể cả admin.

## Sử dụng

Ba lối vào, đều mở cùng một wizard xác nhận:

| Vị trí | Ghi chú |
|---|---|
| `/odoo/pos-orders` → tick đơn → nút đỏ **Xoá cứng** ở thanh header | dùng cho xoá hàng loạt |
| Menu bánh răng **Actions → Xoá cứng đơn hàng** | trên cả list và form |
| Form một đơn → nút **Xoá cứng** ở header | xoá lẻ |

Wizard hiển thị danh sách đơn, cảnh báo tác động, bảng thống kê bảng nào bị
xoá / bị cắt liên kết. Phải nhập **lý do** và gõ **`XOA`** mới xoá được.

Nhật ký: **Điểm bán hàng → Cấu hình → Nhật ký xoá cứng** (`/odoo/pos-hard-delete-log`).

## Cơ chế

Engine `trcf.hard.delete.engine` dò `pg_constraint` lúc chạy để lấy toàn bộ đồ
thị khoá ngoại, rồi lan đệ quy từ `pos_order`:

| Loại khoá ngoại | Hành động |
|---|---|
| NOT NULL hoặc `ON DELETE CASCADE` | xoá dòng phụ thuộc, lan tiếp xuống |
| NULLABLE | `SET NULL` → **chấp nhận dữ liệu mồ côi** |
| Bảng trong `HD_NEVER_DELETE` (partner, product, journal, session, valuation...) | không bao giờ xoá; NOT NULL thì báo lỗi dừng |
| Bảng quan hệ m2m (không có cột `id`) | xoá thẳng dòng quan hệ |

Sau đó dọn `ir_attachment`, `mail_message`, `mail_followers`, `mail_activity`,
`rating_rating`, `ir_model_data` trỏ tới bản ghi đã xoá (Postgres không dọn hộ
vì đây là tham chiếu `res_model`/`res_id`, không phải khoá ngoại thật).

Toàn bộ nằm trong **một transaction**: lỗi giữa chừng thì rollback sạch.
Mọi tên bảng/cột đưa vào SQL đều qua `SQL.identifier()`, giá trị qua `%s`.

Không hard-code danh sách bảng, nên cài thêm module POS mới vẫn chạy đúng.

## Chính sách dữ liệu đã chốt

* **`account_move` (hoá đơn / bút toán): XOÁ LUÔN.** Mặc định bật, có thể bỏ
  chọn trong wizard. Engine tự xoá `account_partial_reconcile` trước để vượt
  qua FK `RESTRICT` trên `account_move_line`.
* **`stock_picking`: GIỮ LẠI**, chỉ `SET NULL` cột `pos_order_id`
  (hằng số `HD_KEEP_TABLES`). Không phá số liệu tồn kho / định giá.
* Tối đa **1000 đơn/lần** (`HD_MAX_ORDERS_PER_RUN`), SQL chia lô 500 id.

## Cảnh báo

1. **Không thể hoàn tác.** Chỉ còn `trcf.pos.hard.delete.log` với snapshot JSON.
2. Xoá bút toán đã vào sổ tạo **lỗ hổng số hiệu chứng từ** và phá **chuỗi hash
   bất biến**; Odoo sẽ báo "gap in sequence" ở lần vào sổ tiếp theo. DB có
   `l10n_vn` nên đây là rủi ro tuân thủ thật, không chỉ kỹ thuật.
3. Xoá đơn thuộc phiên đã đóng làm lệch báo cáo phiên và sổ quỹ. Module không
   tự điều chỉnh `pos.session`.
4. File đính kèm bị xoá khỏi `ir_attachment` nhưng file vật lý còn trong
   filestore (Odoo dọn định kỳ bằng cron `ir_attachment` vacuum).
5. **Backup DB trước lần chạy đầu trên production.**

## Test

```bash
python3 odoo-bin -c odoo19.conf -d <db> -u trcf_dl_pos_order \
    --test-enable --test-tags=/trcf_dl_pos_order --stop-after-init
```
