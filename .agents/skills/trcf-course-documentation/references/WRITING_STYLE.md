# Quy Tắc Viết Nội Dung Tài Liệu

> ✍️ Hướng dẫn về ngôn ngữ, giọng văn và format khi viết tài liệu khoá học TRCF.

---

## 🎯 Nguyên tắc chung

1. **Rõ ràng**: Người đọc hiểu ngay cần làm gì
2. **Ngắn gọn**: Không dài dòng, đi thẳng vào vấn đề
3. **Thực tế**: Có ví dụ cụ thể cho mọi hướng dẫn
4. **Nhất quán**: Giữ phong cách đồng nhất trong toàn bộ tài liệu

---

## 🗣️ Giọng văn

### Nên dùng
- Giọng thân thiện, gần gũi
- Xưng "bạn" với người đọc
- Hướng dẫn trực tiếp, rõ ràng

### Không nên
- Giọng văn quá formal, khô khan
- Dùng thuật ngữ kỹ thuật không giải thích
- Câu quá dài, phức tạp

### Ví dụ

❌ **Không nên:**
> "Người dùng cần thực hiện thao tác click vào button có label 'Mới' được đặt tại vị trí góc trên bên trái của giao diện màn hình."

✅ **Nên:**
> "Nhấn nút **Mới** ở góc trên bên trái."

---

## 📝 Format text

### In đậm (Bold)

Sử dụng cho:
- Tên trường: **Tên sản phẩm**
- Tên nút: **Lưu**, **Mới**, **Xóa**
- Tên menu: **Tồn kho** → **Sản phẩm**
- Từ khóa quan trọng

### Code block

Sử dụng cho:
- Giá trị kỹ thuật: `59,000 đ`
- Phím tắt: `Ctrl + S`
- Đường dẫn menu: `Tồn kho` → `Sản phẩm`

### Emoji

| Emoji | Sử dụng khi |
|-------|-------------|
| ✅ | Có, đúng, bật |
| ❌ | Không, sai, tắt |
| ⚠️ | Cảnh báo, lưu ý quan trọng |
| 💡 | Mẹo, thủ thuật |
| 📌 | Ghi chú quan trọng |
| 💾 | Lưu |
| 📷 | Hình ảnh |

---

## 📋 Cấu trúc mỗi bước

Mỗi bước hướng dẫn PHẢI có đủ các phần sau:

### 1. Heading (Tiêu đề)
```markdown
### Bước X: [Động từ hành động]
```

Ví dụ:
- `### Bước 1: Nhấn nút Mới`
- `### Bước 2: Điền thông tin sản phẩm`
- `### Bước 3: Chọn danh mục`

### 2. Mô tả hành động
Giải thích **chi tiết** người dùng cần làm gì, ở đâu.

Ví dụ:
> Tại trang danh sách sản phẩm, nhấn nút **Mới** ở góc trên bên trái để mở form tạo sản phẩm.

### 3. Ví dụ cụ thể ⭐
**YÊU CẦU BẮT BUỘC**: Mọi bước đều phải có ví dụ với giá trị thực tế.

Format:
```markdown
**Ví dụ:** [Mô tả với giá trị cụ thể]
```

Ví dụ:
> **Ví dụ:** Nhập tên sản phẩm: *Cà phê sữa đá*, giá bán: *35,000 đ*

### 4. Hình ảnh minh họa
Đặt **ngay sau** mô tả và ví dụ.

```markdown
![Mô tả ngắn gọn](đường_dẫn_ảnh)
```

### 5. Ghi chú (nếu có)
Sử dụng blockquote với emoji phù hợp:

```markdown
> 💡 **Mẹo:** [Nội dung mẹo]

> ⚠️ **Lưu ý:** [Nội dung cảnh báo]

> 📌 **Ghi nhớ:** [Điều quan trọng cần nhớ]
```

---

## 📊 Bảng giải thích trường

### Format bảng

```markdown
| Trường | Bắt buộc | Ý nghĩa | Ví dụ |
|--------|----------|---------|-------|
| **Tên** | ✅ | Mô tả | `Giá trị` |
```

### Cột bắt buộc phải có

1. **Trường**: Tên trường (in đậm)
2. **Bắt buộc**: ✅ hoặc ❌
3. **Ý nghĩa**: Giải thích ngắn gọn
4. **Ví dụ**: Giá trị mẫu thực tế

### Ví dụ

| Trường | Bắt buộc | Ý nghĩa | Ví dụ |
|--------|----------|---------|-------|
| **Tên sản phẩm** | ✅ | Tên hiển thị cho khách hàng | `Cà phê đen đá` |
| **Giá bán** | ✅ | Giá bán lẻ | `35,000 đ` |
| **Danh mục** | ❌ | Phân loại sản phẩm | `Thức uống` |

---

## ❓ FAQ Format

### Câu hỏi
```markdown
### Q: [Câu hỏi dạng tiếng Việt tự nhiên]?
```

### Trả lời
```markdown
**A:** [Câu trả lời đầy đủ, dễ hiểu]
```

### Ví dụ

```markdown
### Q: Sản phẩm không hiển thị trong POS?
**A:** Kiểm tra đã tích chọn checkbox **POS** chưa. Nếu vẫn không thấy, 
vào **Danh mục POS** và thêm sản phẩm vào danh mục.
```

---

## ✅ Checklist tự kiểm tra

### Nội dung
- [ ] Mỗi bước có tiêu đề rõ ràng
- [ ] Mỗi bước có mô tả đầy đủ
- [ ] Mỗi bước có ví dụ cụ thể
- [ ] Mỗi bước có hình ảnh minh họa
- [ ] Các ghi chú/mẹo được đánh dấu đúng

### Format
- [ ] Tên trường/nút được in đậm
- [ ] Giá trị kỹ thuật dùng code block
- [ ] Emoji sử dụng phù hợp
- [ ] Bảng có đủ cột cần thiết

### Ngôn ngữ
- [ ] Giọng văn thân thiện, rõ ràng
- [ ] Không có lỗi chính tả
- [ ] Câu không quá dài
- [ ] Thuật ngữ được giải thích

---

*Tài liệu tham khảo cho skill trcf-course-documentation*
