# Hướng Dẫn Chụp và Xử Lý Hình Ảnh

> 📸 Tài liệu hướng dẫn chụp screenshot và upload hình ảnh cho tài liệu khoá học.

---

## 🎯 Mục tiêu

Hình ảnh trong tài liệu phải:
- Rõ ràng, dễ nhìn
- Đúng nội dung cần minh họa
- Có thể highlight các vùng quan trọng
- Upload lên cloud để nhúng vào Notion

---

## 📂 Thư mục lưu trữ

| Loại | Đường dẫn |
|------|-----------|
| **Ảnh local** | `/Users/tuan/coffeetree_odoo19_dev/custom_addons/docs/images/` |
| **Ảnh cloud** | ImgBB (external URL) |

---

## 📛 Quy tắc đặt tên file

### Format
```
[ten_tinh_nang]_[mo_ta_noi_dung].png
```

### Quy tắc
- Chữ thường, không dấu tiếng Việt
- Phân cách bằng underscore `_`
- Mô tả ngắn gọn, dễ hiểu
- Định dạng: `.png` hoặc `.jpg`

### Ví dụ

| Nội dung | Tên file |
|----------|----------|
| Danh sách sản phẩm | `san_pham_danh_sach.png` |
| Form tạo sản phẩm mới | `san_pham_form_tao_moi.png` |
| Bước 1 - Nhấn nút Mới | `san_pham_buoc1_nut_moi.png` |
| Kết quả sau khi lưu | `san_pham_ket_qua.png` |

---

## 📷 Chụp Screenshot

### Sử dụng Browser Subagent

```
Task: Chụp screenshot màn hình [tên màn hình]
1. Mở trình duyệt tại URL: http://localhost:9091
2. Đăng nhập với email/password đã cung cấp
3. Navigate đến: [đường dẫn menu]
4. Chụp screenshot toàn trang
5. Lưu vào: /Users/tuan/coffeetree_odoo19_dev/custom_addons/docs/images/[tên_file].png
```

### Lưu ý khi chụp

1. **Kích thước**: Ưu tiên độ phân giải cao (1920x1080)
2. **Vùng focus**: Chỉ chụp phần cần thiết, tránh quá rộng
3. **Trạng thái**: Đảm bảo form đã có dữ liệu mẫu
4. **Sidebar**: Có thể ẩn sidebar nếu không cần thiết

---

## 🎨 Highlight vùng quan trọng

### Khi nào cần highlight
- Nút cần nhấn
- Trường cần điền
- Vùng quan trọng cần chú ý

### Cách highlight
- Vẽ khung đỏ xung quanh
- Thêm mũi tên chỉ vào
- Thêm số thứ tự nếu nhiều vùng

### Ví dụ prompt cho generate_image
```
Task: Thêm highlight vào screenshot
- Đọc ảnh gốc: [đường dẫn]
- Vẽ khung đỏ xung quanh nút "Mới" ở góc trên trái
- Lưu ảnh mới: [đường dẫn]_highlighted.png
```

---

## ☁️ Upload lên ImgBB

### API Endpoint
```
POST https://api.imgbb.com/1/upload
```

### API Key
```
0b893385aabdc7ded0fea2ee14d45156
```

### Lệnh CURL

```bash
curl --location --request POST \
  "https://api.imgbb.com/1/upload?key=0b893385aabdc7ded0fea2ee14d45156" \
  --form "image=@/Users/tuan/coffeetree_odoo19_dev/custom_addons/docs/images/ten_file.png"
```

### Response mẫu

```json
{
  "data": {
    "id": "2ndCYJK",
    "url": "https://i.ibb.co/2ndCYJK/ten-file.png",
    "display_url": "https://i.ibb.co/2ndCYJK/ten-file.png",
    "delete_url": "https://ibb.co/2ndCYJK/abc123"
  },
  "success": true,
  "status": 200
}
```

### Sử dụng URL

Lấy giá trị `data.url` hoặc `data.display_url` để nhúng vào Notion:
```
https://i.ibb.co/2ndCYJK/ten-file.png
```

---

## 📋 Checklist hình ảnh

### Trước khi chụp
- [ ] Đã xác định màn hình cần chụp
- [ ] Đã chuẩn bị dữ liệu mẫu
- [ ] Đã xác định tên file

### Sau khi chụp
- [ ] Hình ảnh rõ ràng, đầy đủ
- [ ] Đã lưu vào đúng thư mục
- [ ] Đã đặt tên theo quy tắc

### Upload
- [ ] Đã upload lên ImgBB
- [ ] Đã lưu URL trả về
- [ ] URL hoạt động (test bằng trình duyệt)

---

## ⚠️ Lưu ý quan trọng

1. **Bảo mật**: Không chụp thông tin nhạy cảm (mật khẩu, API key)
2. **Kích thước**: File quá lớn (>5MB) có thể upload thất bại
3. **Định dạng**: ImgBB hỗ trợ PNG, JPG, GIF, WEBP
4. **Thời hạn**: Ảnh trên ImgBB lưu vĩnh viễn (free plan)

---

*Tài liệu tham khảo cho skill trcf-course-documentation*
