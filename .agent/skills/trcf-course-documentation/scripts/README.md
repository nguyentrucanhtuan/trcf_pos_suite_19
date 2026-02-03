# Script Đồng Bộ Notion

Script `sync_to_notion.py` giúp đồng bộ tài liệu Markdown lên Notion với formatting đầy đủ.

## Sử dụng

```bash
cd /Users/tuan/coffeetree_odoo19_dev/custom_addons/.agent/skills/trcf-course-documentation/scripts

python3 sync_to_notion.py <đường_dẫn_file_markdown>
```

## Ví dụ

```bash
# Upload bài tạo nhân viên
python3 sync_to_notion.py ../../../docs/khoa_hoc/chuong_6/6.1_tao_nhan_vien.md

# Upload bài khác
python3 sync_to_notion.py ../../../docs/khoa_hoc/chuong_7/7.1_nhap_chi_phi.md
```

## Tính năng

Script tự động chuyển đổi Markdown sang Notion với đầy đủ formatting:

- ✅ **Headings** (H1, H2, H3)
- ✅ **Tables** với formatting (bold, code trong cells)
- ✅ **Callouts** (💡 mẹo, ⚠️ cảnh báo)
- ✅ **Images** (external URLs từ ImgBB)
- ✅ **Lists** (bullet và numbered)
- ✅ **Code blocks** (```language)
- ✅ **Rich text** (bold `**text**`, code `` `text` ``)
- ✅ **Dividers** (`---`)
- ✅ **Quotes** (`> text`)

## Lưu ý

1. **Images**: Chỉ hỗ trợ external URLs (http/https). Local images cần upload lên ImgBB trước.
2. **Tables**: Phải đúng format Markdown table với separator line `|---|---|`
3. **Callouts**: Dùng `> 💡` hoặc `> ⚠️` ở đầu dòng

## Cấu hình

API keys được cấu hình sẵn trong script:
- `NOTION_API_KEY`: API key Notion
- `PARENT_PAGE_ID`: ID của page "KHOÁ HỌC VẬN HÀNH"
- `IMGBB_API_KEY`: API key ImgBB (cho tương lai)
