---
name: trcf-course-documentation
description: >
  Tạo tài liệu hướng dẫn sử dụng khoá học vận hành TRCF cho Odoo 19.
  Use when: (1) Viết tài liệu hướng dẫn tính năng Odoo, (2) Tạo hướng dẫn cho khoá học,
  (3) Đồng bộ tài liệu lên Notion, (4) Tạo tài liệu có hình ảnh minh họa.
  Keywords: tài liệu, hướng dẫn, documentation, guide, tutorial, notion, course, training, odoo.
---

# Skill Tạo Tài Liệu Khoá Học TRCF

Tạo tài liệu hướng dẫn sử dụng **chuẩn TRCF** với cấu trúc đầy đủ, hình ảnh minh họa, và đồng bộ lên Notion.

---

## 🚀 Quick Start

```
1. [ ] Thu thập thông tin (module/tính năng nào?)
2. [ ] Đọc code module để hiểu fields và logic
3. [ ] Chụp screenshot các bước (browser subagent)
4. [ ] Upload ảnh lên ImgBB
5. [ ] Viết nội dung theo template
6. [ ] Lưu markdown → Đồng bộ Notion
```

---

## 📋 Cấu trúc tài liệu chuẩn

> ⚠️ **QUAN TRỌNG**: Tài liệu Notion phải **ĐẦY ĐỦ VÀ CHI TIẾT** như file markdown gốc. Không được rút gọn hoặc bỏ qua bất kỳ phần nào.

Mỗi tài liệu **BẮT BUỘC** có các phần sau:

| # | Phần | Nội dung | Yêu cầu |
|---|------|----------|---------|
| 1 | **📌 Giới thiệu** | Mục đích + Ý nghĩa của tính năng | Giải thích TẠI SAO cần tính năng này |
| 2 | **🔗 Cách truy cập** | Đường dẫn URL + Menu path | Hướng dẫn rõ ràng cách tìm tính năng |
| 3 | **📋 Hướng dẫn từng bước** | Bước 1, 2, 3... với ảnh minh họa | Mỗi bước có: Heading + Mô tả + Bảng chi tiết + Ảnh |
| 4 | **📝 Bảng tham khảo nhanh** | Bảng giải thích các trường dữ liệu | Trường | Bắt buộc | Ví dụ | Ghi chú |
| 5 | **❓ FAQ** | Câu hỏi thường gặp và cách xử lý | Tối thiểu 3 câu hỏi thực thực tế |

> ❌ **LƯU Ý QUAN TRỌNG**: **KHÔNG** bao gồm mục "Mục lục" hoặc "Tóm tắt quy trình" (Mermaid diagram). Tài liệu cần tập trung vào nội dung trực tiếp, tiêu đề rõ ràng và hình ảnh minh họa trực quan.

### 🎯 Yêu cầu chi tiết cho mỗi phần

#### Phần Hướng dẫn từng bước
**BẮT BUỘC** mỗi bước phải có:
- ✅ Heading: `### Bước X: [Hành động]`
- ✅ Mô tả chi tiết hành động
- ✅ **Bảng chi tiết** (nếu có nhiều trường): Trường | Ví dụ | Giải thích
- ✅ Hình ảnh minh họa
- ✅ Callout (💡 Mẹo hoặc ⚠️ Lưu ý) nếu cần

#### Phần Bảng chi tiết
**Format chuẩn:**
```
| Trường | Ví dụ | Giải thích |
|--------|-------|------------|
| **Tên trường** | `Giá trị mẫu` | Mô tả ý nghĩa |
```

Hoặc với trường bắt buộc:
```
| Trường | Bắt buộc | Ý nghĩa | Ví dụ |
|--------|----------|---------|-------|
| **Tên** | ✅/❌ | Mô tả | `Giá trị` |
```

**Template chi tiết:** Xem [templates/basic_guide.md](templates/basic_guide.md)
**Ví dụ mẫu:** Xem [7.2_nhap_hang_tu_ncc.md](../../../docs/khoa_hoc/chuong_7/7.2_nhap_hang_tu_ncc.md)

---

## 🔑 API Credentials

| Service | Key/ID |
|---------|--------|
| **Notion Parent** | `2ef172c2-951e-803d-a68a-ec0574f3aca4` |
| **ImgBB API Key** | `0b893385aabdc7ded0fea2ee14d45156` |
| **Odoo URL** | `http://localhost:9091/` |
| **Odoo Login** | `nguyentrucanhtuan@gmail.com` / `anhtuan2609` |

---

## 📚 References (Load khi cần)

| Cần làm gì? | Đọc file |
|-------------|----------|
| Chụp screenshot | [IMAGE_CAPTURE.md](references/IMAGE_CAPTURE.md) |
| Đồng bộ Notion | [NOTION_API.md](references/NOTION_API.md) |
| Quy tắc viết nội dung | [WRITING_STYLE.md](references/WRITING_STYLE.md) |

## 📖 Best Practice Examples

| Bài mẫu | Mô tả |
|---------|-------|
| [2.2 Thiết lập UoM](examples/2.2_thiet_lap_don_vi_tinh_uom.md) | ✅ Cấu trúc đầy đủ: Giới thiệu, Truy cập, Hướng dẫn bước, Quy tắc đặt tên, FAQ |
| [Hướng dẫn thêm sản phẩm](examples/huong_dan_them_san_pham.md) | Ví dụ về tạo sản phẩm mới |
| [Notion Full Example](examples/notion_full_example.md) | ⭐ **MỚI**: Ví dụ đầy đủ cách tạo Notion documentation với tables, callouts, FAQ, checklist |

---

## ⚡ Quy trình chi tiết

### 1. Nghiên cứu tính năng

```bash
# Tìm model chính
find /Users/tuan/coffeetree_odoo19_dev/custom_addons/<module> -name "*.py" | head -20

# Tìm views
find /Users/tuan/coffeetree_odoo19_dev/custom_addons/<module> -name "*views*.xml" | head -10
```

### 2. Chụp screenshot

Dùng browser subagent:
- Navigate đến tính năng
- Chụp screenshot từng bước
- Lưu vào: `/Users/tuan/coffeetree_odoo19_dev/custom_addons/docs/images/`
- Đặt tên: `danh_sach_san_pham.png`, `form_tao_moi.png`

### 3. Upload ImgBB

```bash
curl -X POST "https://api.imgbb.com/1/upload?key=0b893385aabdc7ded0fea2ee14d45156" \
  --form "image=@<đường_dẫn_file>"
```

Lấy `data.url` từ response để dùng trong Notion.

### 4. Viết nội dung

Quy tắc:
- Ngôn ngữ: Tiếng Việt, rõ ràng
- Giọng văn: "Bạn nhấn vào nút..."
- Tên trường: **In đậm**
- Giá trị: `in code`
- Emoji: ✅ ❌ ⚠️ 💡 📌

### 5. Đồng bộ Notion

**Script tổng quát:** `scripts/sync_to_notion.py`

```bash
cd /Users/tuan/coffeetree_odoo19_dev/custom_addons/.agent/skills/trcf-course-documentation/scripts

# Upload bất kỳ file markdown nào
python3 sync_to_notion.py ../../../docs/khoa_hoc/chuong_X/bai_Y.md
```

**Tính năng:**
- ✅ Tự động parse Markdown → Notion blocks
- ✅ Hỗ trợ tables, callouts (💡⚠️), images
- ✅ Bold, code formatting
- ✅ Headings, lists, dividers

**Lưu ý:**
- Images phải là external URLs (upload lên ImgBB trước)
- Tables phải đúng format Markdown
- Callouts dùng `> 💡` hoặc `> ⚠️`

| Markdown | Notion Block |
|----------|--------------|
| `## H2` | `heading_2` |
| `### H3` | `heading_3` |
| `- item` | `bulleted_list_item` |
| `> 💡 mẹo` | `callout` 💡 |
| `![](url)` | `image` external |
| `| table |` | `table` with formatting |

---

## ✅ Checklist hoàn thành

- [ ] Có đủ 5 phần (Giới thiệu, Truy cập, Hướng dẫn, Giải thích, FAQ)
- [ ] Mỗi bước có ví dụ cụ thể
- [ ] Mỗi bước có ảnh minh họa
- [ ] Ảnh đã upload ImgBB và link hoạt động
- [ ] Đã đồng bộ Notion thành công bằng `sync_to_notion.py`
