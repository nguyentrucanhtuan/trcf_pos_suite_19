# Hướng Dẫn Sử Dụng Notion API

> 📘 Tài liệu hướng dẫn sử dụng Notion API thông qua MCP server để đồng bộ tài liệu.

---

## 🔑 Thông tin API

| Thông tin | Giá trị |
|-----------|---------|
| **Parent Page ID** | `2ef172c2-951e-803d-a68a-ec0574f3aca4` |
| **Parent Page Title** | KHOÁ HỌC VẬN HÀNH |
| **MCP Server** | `notion-mcp-server` |

---

## 📋 Các MCP Tools

### 1. Tìm kiếm trang
```
Tool: mcp_notion-mcp-server_API-post-search
```

**Parameters:**
- `query`: Text tìm kiếm
- `filter`: `{"property": "object", "value": "page"}` hoặc `"data_source"`

### 2. Tạo trang mới
```
Tool: mcp_notion-mcp-server_API-post-page
```

**Parameters:**
```json
{
  "parent": {
    "page_id": "2ef172c2-951e-803d-a68a-ec0574f3aca4"
  },
  "properties": {
    "title": [
      {
        "text": {
          "content": "Tên trang mới"
        }
      }
    ]
  }
}
```

### 3. Thêm nội dung vào trang
```
Tool: mcp_notion-mcp-server_API-patch-block-children
```

**Parameters:**
- `block_id`: ID của trang hoặc block cha
- `children`: Array các block objects

### 4. Xem thông tin trang
```
Tool: mcp_notion-mcp-server_API-retrieve-a-page
```

**Parameters:**
- `page_id`: ID của trang

### 5. Xem nội dung trang
```
Tool: mcp_notion-mcp-server_API-get-block-children
```

**Parameters:**
- `block_id`: ID của trang

---

## 🔄 Mapping Markdown → Notion Blocks

### Heading Blocks

| Markdown | Notion Block Type |
|----------|-------------------|
| `# H1` | `heading_1` |
| `## H2` | `heading_2` |
| `### H3` | `heading_3` |

**JSON Example - Heading 2:**
```json
{
  "type": "heading_2",
  "heading_2": {
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Tiêu đề section" }
      }
    ]
  }
}
```

### Paragraph Block

```json
{
  "type": "paragraph",
  "paragraph": {
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Nội dung văn bản thường." }
      }
    ]
  }
}
```

**Text với formatting:**
```json
{
  "type": "text",
  "text": { "content": "Text đậm" },
  "annotations": { "bold": true }
}
```

### Image Block

```json
{
  "type": "image",
  "image": {
    "type": "external",
    "external": {
      "url": "https://i.ibb.co/XXX/ten-file.png"
    },
    "caption": [
      {
        "type": "text",
        "text": { "content": "Mô tả hình ảnh" }
      }
    ]
  }
}
```

### Callout Block

**💡 Mẹo (lightbulb):**
```json
{
  "type": "callout",
  "callout": {
    "icon": { "type": "emoji", "emoji": "💡" },
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Nội dung mẹo hữu ích" }
      }
    ]
  }
}
```

**⚠️ Lưu ý (warning):**
```json
{
  "type": "callout",
  "callout": {
    "icon": { "type": "emoji", "emoji": "⚠️" },
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Nội dung cảnh báo" }
      }
    ]
  }
}
```

### List Blocks

**Bulleted list:**
```json
{
  "type": "bulleted_list_item",
  "bulleted_list_item": {
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Item trong danh sách" }
      }
    ]
  }
}
```

**Numbered list:**
```json
{
  "type": "numbered_list_item",
  "numbered_list_item": {
    "rich_text": [
      {
        "type": "text",
        "text": { "content": "Item có số thứ tự" }
      }
    ]
  }
}
```

### Divider Block

```json
{
  "type": "divider",
  "divider": {}
}
```

---

## 📝 Ví dụ hoàn chỉnh: Tạo một bước hướng dẫn

```json
[
  {
    "type": "heading_3",
    "heading_3": {
      "rich_text": [{"type": "text", "text": {"content": "Bước 1: Nhấn nút Mới"}}]
    }
  },
  {
    "type": "paragraph",
    "paragraph": {
      "rich_text": [{"type": "text", "text": {"content": "Tại trang danh sách sản phẩm, nhấn nút \"Mới\" ở góc trên bên trái."}}]
    }
  },
  {
    "type": "paragraph",
    "paragraph": {
      "rich_text": [
        {"type": "text", "text": {"content": "Ví dụ: "}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": "Nút Mới màu xanh dương nằm ở góc trên bên trái màn hình."}}
      ]
    }
  },
  {
    "type": "image",
    "image": {
      "type": "external",
      "external": {"url": "https://i.ibb.co/XXX/danh-sach-san-pham.png"},
      "caption": [{"type": "text", "text": {"content": "Trang danh sách sản phẩm"}}]
    }
  },
  {
    "type": "callout",
    "callout": {
      "icon": {"type": "emoji", "emoji": "💡"},
      "rich_text": [{"type": "text", "text": {"content": "Mẹo: Bạn cũng có thể dùng phím tắt Ctrl+N để tạo mới nhanh."}}]
    }
  }
]
```

---

## ⚠️ Lưu ý quan trọng

1. **Image URL phải public**: Notion không hỗ trợ upload file, phải dùng external URL (ImgBB)
2. **Giới hạn 100 blocks**: Mỗi lần gọi `patch-block-children` tối đa 100 blocks
3. **Rich text formatting**: Dùng `annotations` để bold, italic, code
4. **Block ID**: Page ID cũng có thể dùng làm block_id

---

*Tài liệu tham khảo cho skill trcf-course-documentation*
