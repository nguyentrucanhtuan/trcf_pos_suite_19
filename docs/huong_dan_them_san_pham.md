# Hướng Dẫn Thêm Sản Phẩm Trong Odoo 19

## Mục Lục
1. [Giới thiệu](#1-giới-thiệu)
2. [Truy cập danhsách  sản phẩm](#2-truy-cập-danh-sách-sản-phẩm)
3. [Tạo sản phẩm mới](#3-tạo-sản-phẩm-mới)
4. [Giải thích các trường quan trọng](#4-giải-thích-các-trường-quan-trọng)
5. [FAQ - Câu hỏi thường gặp](#5-faq---câu-hỏi-thường-gặp)

---

## 1. Giới thiệu

**Mục đích:** Hướng dẫn tạo sản phẩm mới trong Odoo 19 với đầy đủ thông tin cần thiết.

**Đối tượng sử dụng:** 
- Quản lý cửa hàng
- Nhân viên kho
- Nhân viên bán hàng

---

## 2. Truy cập danh sách sản phẩm

**Đường dẫn:** `Tồn kho` → `Sản phẩm` → `Sản phẩm`

![Danh sách sản phẩm trong Odoo](./images/danh_sach_san_pham.png)

Tại đây bạn có thể:
- Xem danh sách tất cả sản phẩm
- Tìm kiếm sản phẩm theo tên, mã
- Lọc theo danh mục, loại sản phẩm

---

## 3. Tạo sản phẩm mới

### Bước 1: Nhấn nút "Mới"

Tại trang danh sách sản phẩm, nhấn nút **"Mới"** ở góc trên bên trái.

### Bước 2: Điền thông tin sản phẩm

![Form tạo sản phẩm mới](./images/form_tao_san_pham_moi.png)

**Các thông tin cần điền:**

1. **Tên sản phẩm**: Nhập tên sản phẩm rõ ràng
   - Ví dụ: "Burger phô mai"

2. **Kênh bán hàng**: Tích chọn các kênh phù hợp
   - ☑️ **Bán hàng**: Sản phẩm bán qua đơn hàng
   - ☑️ **POS**: Sản phẩm bán tại quầy thu ngân
   - ☑️ **Mua hàng**: Sản phẩm mua từ nhà cung cấp

3. **Loại sản phẩm**:
   - **Hàng hóa**: Hàng lưu kho, theo dõi số lượng
   - **Dịch vụ**: Dịch vụ, không lưu kho
   - **Combo**: Sản phẩm kết hợp nhiều món

4. **Giá bán**: Nhập giá bán cho khách hàng
   - Ví dụ: `59,000 đ` (đơn vị: mỗi LY)

5. **Chi phí**: Nhập giá vốn/giá mua
   - Ví dụ: `25,000 đ`

6. **Thuế bán hàng**: Chọn thuế VAT áp dụng khi bán
   - Ví dụ: `8%` (thuế GTGT)

7. **Thuế mua hàng**: Chọn thuế VAT khi mua từ NCC
   - Ví dụ: `8%`

### Bước 3: Thêm hình ảnh sản phẩm

Click vào biểu tượng 📷 ở góc trên bên phải để upload hình ảnh sản phẩm.

### Bước 4: Lưu sản phẩm

Nhấn **💾 Lưu** hoặc nhấn `Ctrl + S` để lưu sản phẩm.

---

## 4. Giải thích các trường quan trọng

### 4.1 Loại sản phẩm (Product Type)

| Loại | Ý nghĩa | Sử dụng khi |
|------|---------|-------------|
| **Hàng hóa** | Theo dõi tồn kho, có số lượng | Nguyên liệu, thành phẩm |
| **Dịch vụ** | Không theo dõi tồn kho | Phí ship, phí dịch vụ |
| **Combo** | Kết hợp nhiều sản phẩm | Combo bữa ăn |

### 4.2 Theo dõi hàng tồn kho (Track Inventory)

**Vị trí:** Tab "Thông tin chung", checkbox **"Theo dõi hàng tồn kho"**

| Trạng thái | Ý nghĩa | Sử dụng khi |
|------------|---------|-------------|
| ☑️ **Bật** | Hệ thống theo dõi số lượng tồn kho của sản phẩm | Nguyên liệu, hàng hóa cần kiểm soát số lượng |
| ☐ **Tắt** | Không theo dõi số lượng, luôn coi như có sẵn | Dịch vụ, sản phẩm tiêu hao nhỏ |

**Khi bật "Theo dõi hàng tồn kho":**
- ✅ Hiển thị số lượng **"Hiện có"** (On Hand) trên form sản phẩm
- ✅ Cập nhật tồn kho khi xuất/nhập kho
- ✅ Cảnh báo khi hết hàng hoặc dưới mức tối thiểu
- ✅ Có thể xem lịch sử di chuyển kho

**Khi tắt "Theo dõi hàng tồn kho":**
- ❌ Không hiển thị số lượng tồn
- ❌ Không cần nhập kho trước khi bán
- ✅ Phù hợp cho dịch vụ, phí ship

> 💡 **Mẹo**: Nếu bạn chọn loại sản phẩm là **"Hàng hóa"**, nên bật checkbox này để quản lý kho hiệu quả.

> ⚠️ **Lưu ý**: Sau khi đã có giao dịch kho, không nên tắt tùy chọn này vì có thể gây sai lệch dữ liệu.

### 4.3 Kênh bán hàng

| Checkbox | Ý nghĩa | Ví dụ |
|----------|---------|-------|
| ☑️ **Bán hàng** | Hiển thị trong module Sales | Đơn hàng B2B |
| ☑️ **POS** | Hiển thị tại màn hình POS | Bán lẻ tại quầy |
| ☑️ **Mua hàng** | Hiển thị trong module Purchase | Mua nguyên liệu |

### 4.4 Đơn vị tính (Unit of Measure)

- **Mỗi LY**: Bán theo ly (thức uống)
- **Cái**: Bán theo cái (bánh, burger)
- **Kg**: Bán theo cân (nguyên liệu)
- **Thùng**: Mua theo thùng từ NCC

> 💡 **Mẹo**: Có thể đặt đơn vị mua khác đơn vị bán (VD: mua theo Thùng, bán theo Lon)

### 4.5 Giá bán vs Chi phí

| Trường | Ý nghĩa | Ảnh hưởng đến |
|--------|---------|---------------|
| **Giá bán** | Giá bán cho khách hàng | Đơn hàng, Hóa đơn |
| **Chi phí** | Giá vốn/giá mua | Báo cáo lợi nhuận, Kho |

### 4.6 Thuế (Taxes)

| Trường | Ý nghĩa | Giá trị phổ biến |
|--------|---------|------------------|
| **Thuế bán hàng** | VAT tính khi bán | 8%, 10%, 0% |
| **Thuế mua hàng** | VAT tính khi mua | 8%, 10%, 0% |

> ⚠️ **Lưu ý**: Cấu hình thuế ảnh hưởng đến cách hiển thị giá (bao gồm thuế hoặc chưa bao gồm thuế)

### 4.7 Hình ảnh sản phẩm

- **Định dạng hỗ trợ**: PNG, JPG, WEBP
- **Kích thước khuyến nghị**: 500x500 pixel trở lên
- **Tỷ lệ**: 1:1 (vuông) để hiển thị đẹp trên POS

---

## 5. FAQ - Câu hỏi thường gặp

### Q: Sản phẩm không hiển thị trong POS?
**A:** Kiểm tra đã tích chọn checkbox **"POS"** chưa. Nếu vẫn không thấy, kiểm tra sản phẩm đã được thêm vào danh mục POS chưa.

### Q: Làm sao để tạo đơn vị tính mới?
**A:** Vào `Tồn kho` → `Cấu hình` → `Đơn vị tính` → `Mới`

### Q: Giá trên hóa đơn khác với giá nhập?
**A:** Kiểm tra cấu hình thuế. Giá có thể hiển thị đã bao gồm hoặc chưa bao gồm VAT tùy thiết lập.

### Q: Sản phẩm không thể mua được?
**A:** Kiểm tra đã tích chọn checkbox **"Mua hàng"** chưa.

---

*Tài liệu được tạo cho Odoo 19 - TRCF*
