---
description: /trcf_write_documentation - Viết tài liệu hướng dẫn sử dụng chuẩn TRCF
---

Sử dụng skill `trcf-course-documentation` để tạo tài liệu.

### Quy trình:

1. **Thu thập yêu cầu**: Hỏi chủ đề và đối tượng người dùng
2. **Đọc skill**: Load `skills/trcf-course-documentation/SKILL.md`
3. **Nghiên cứu module**: Đọc code tính năng cần viết
4. **Chụp screenshot**: Browser subagent + upload ImgBB
5. **Viết nội dung**: Theo template `templates/basic_guide.md`
// turbo
6. **Đồng bộ Notion**: Dùng MCP notion-mcp-server
7. **Review**: Kiểm tra 5 phần bắt buộc đầy đủ

### 5 phần bắt buộc:
1. Giới thiệu (mục đích + ý nghĩa)
2. Truy cập (đường dẫn menu)
3. Hướng dẫn từng bước (với ảnh)
4. Giải thích các trường
5. FAQ