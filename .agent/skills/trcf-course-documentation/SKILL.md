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

Mỗi tài liệu **BẮT BUỘC** có 5 phần:

| # | Phần | Nội dung |
|---|------|----------|
| 1 | **Giới thiệu** | Mục đích + Ý nghĩa của tính năng |
| 2 | **Truy cập** | Đường dẫn `Menu → Submenu → Action` |
| 3 | **Hướng dẫn từng bước** | Bước 1, 2, 3... với ảnh minh họa |
| 4 | **Giải thích trường** | Bảng giải thích fields quan trọng |
| 5 | **FAQ** | Câu hỏi thường gặp và cách xử lý |

**Template chi tiết:** Xem [templates/basic_guide.md](templates/basic_guide.md)

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

| Markdown | Notion Block |
|----------|--------------|
| `## H2` | `heading_2` |
| `### H3` | `heading_3` |
| `- item` | `bulleted_list_item` |
| `> 💡 mẹo` | `callout` 💡 |
| `![](url)` | `image` external |

---

## ✅ Checklist hoàn thành

- [ ] Có đủ 5 phần (Giới thiệu, Truy cập, Hướng dẫn, Giải thích, FAQ)
- [ ] Mỗi bước có ví dụ cụ thể
- [ ] Mỗi bước có ảnh minh họa
- [ ] Ảnh đã upload ImgBB và link hoạt động
- [ ] Đã đồng bộ Notion thành công
