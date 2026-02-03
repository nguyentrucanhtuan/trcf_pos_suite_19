# Ví Dụ: Tạo Tài Liệu Notion Đầy Đủ

> 📘 Hướng dẫn tạo tài liệu Notion **đầy đủ chi tiết** như file markdown gốc.

---

## 🎯 Mục tiêu

Tạo tài liệu Notion cho **"7.2 Nhập Hàng Từ Nhà Cung Cấp"** với:
- ✅ Đầy đủ 6 phần: Giới thiệu, Truy cập, Hướng dẫn, Loại nhập hàng, FAQ, Checklist
- ✅ Bảng chi tiết cho mỗi bước
- ✅ Hình ảnh minh họa
- ✅ Callouts (💡, ⚠️)

---

## 📋 Quy trình tạo tài liệu

### Bước 1: Tạo trang Notion

```python
# Tool: mcp_notion-mcp-server_API-post-page
{
  "parent": {
    "page_id": "2ef172c2-951e-803d-a68a-ec0574f3aca4"
  },
  "properties": {
    "title": [
      {
        "text": {
          "content": "7.2 Nhập Hàng Từ Nhà Cung Cấp"
        }
      }
    ]
  }
}
```

Lưu lại `page_id` từ response.

---

### Bước 2: Thêm nội dung đầy đủ

```python
# Tool: mcp_notion-mcp-server_API-patch-block-children
# block_id: <page_id từ bước 1>
# children: [array các blocks dưới đây]
```

#### 2.1 Phần Giới Thiệu

```json
[
  {
    "type": "heading_2",
    "heading_2": {
      "rich_text": [{"type": "text", "text": {"content": "📌 Giới Thiệu"}}]
    }
  },
  {
    "type": "paragraph",
    "paragraph": {
      "rich_text": [
        {"type": "text", "text": {"content": "Nhập hàng từ nhà cung cấp (NCC) là nghiệp vụ "}},
        {"type": "text", "text": {"content": "bổ sung nguyên liệu"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": " vào kho khi nhận hàng từ đơn đặt hàng. Đây là bước quan trọng để:"}}
      ]
    }
  },
  {
    "type": "bulleted_list_item",
    "bulleted_list_item": {
      "rich_text": [
        {"type": "text", "text": {"content": "Cập nhật tồn kho"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": ": Hàng nhập sẽ tự động tăng số lượng trong kho"}}
      ]
    }
  },
  {
    "type": "bulleted_list_item",
    "bulleted_list_item": {
      "rich_text": [
        {"type": "text", "text": {"content": "Ghi nhận giá vốn"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": ": Hệ thống tính giá vốn trung bình tự động"}}
      ]
    }
  },
  {
    "type": "bulleted_list_item",
    "bulleted_list_item": {
      "rich_text": [
        {"type": "text", "text": {"content": "Đối soát công nợ"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": ": Liên kết với đơn mua hàng để theo dõi thanh toán"}}
      ]
    }
  },
  {
    "type": "callout",
    "callout": {
      "icon": {"type": "emoji", "emoji": "💡"},
      "rich_text": [
        {"type": "text", "text": {"content": "Lưu ý"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": ": Chỉ nhập hàng khi "}},
        {"type": "text", "text": {"content": "đã nhận thực tế"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": " từ NCC, kiểm tra số lượng và chất lượng trước khi xác nhận."}}
      ]
    }
  },
  {
    "type": "divider",
    "divider": {}
  }
]
```

#### 2.2 Phần Cách Truy Cập

```json
[
  {
    "type": "heading_2",
    "heading_2": {
      "rich_text": [{"type": "text", "text": {"content": "🔗 Cách Truy Cập"}}]
    }
  },
  {
    "type": "table",
    "table": {
      "table_width": 3,
      "has_column_header": true,
      "has_row_header": false,
      "children": [
        {
          "type": "table_row",
          "table_row": {
            "cells": [
              [{"type": "text", "text": {"content": "Giao diện"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "Phù hợp với"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "Đường dẫn"}, "annotations": {"bold": true}}]
            ]
          }
        },
        {
          "type": "table_row",
          "table_row": {
            "cells": [
              [{"type": "text", "text": {"content": "Giao diện nhân viên"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "Nhân viên kho"}}],
              [{"type": "text", "text": {"content": "/trcf_fnb_inventory/purchase_list"}, "annotations": {"code": true}}]
            ]
          }
        },
        {
          "type": "table_row",
          "table_row": {
            "cells": [
              [{"type": "text", "text": {"content": "Odoo mặc định"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "Quản lý, Kế toán"}}],
              [{"type": "text", "text": {"content": "Kho vận → Hoạt động → Phiếu nhập kho"}}]
            ]
          }
        }
      ]
    }
  },
  {
    "type": "divider",
    "divider": {}
  }
]
```

#### 2.3 Phần Hướng Dẫn Từng Bước (Ví dụ Bước 3)

```json
[
  {
    "type": "heading_2",
    "heading_2": {
      "rich_text": [{"type": "text", "text": {"content": "📋 Hướng Dẫn Nhập Hàng (Giao Diện Nhân Viên)"}}]
    }
  },
  {
    "type": "callout",
    "callout": {
      "icon": {"type": "emoji", "emoji": "⭐"},
      "rich_text": [{"type": "text", "text": {"content": "Giao diện đơn giản, phù hợp cho nhân viên kho nhập nhanh."}}]
    }
  },
  {
    "type": "heading_3",
    "heading_3": {
      "rich_text": [{"type": "text", "text": {"content": "Bước 3: Điền thông tin đơn hàng"}}]
    }
  },
  {
    "type": "table",
    "table": {
      "table_width": 3,
      "has_column_header": true,
      "has_row_header": false,
      "children": [
        {
          "type": "table_row",
          "table_row": {
            "cells": [
              [{"type": "text", "text": {"content": "Trường"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "Ví dụ"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "Giải thích"}, "annotations": {"bold": true}}]
            ]
          }
        },
        {
          "type": "table_row",
          "table_row": {
            "cells": [
              [{"type": "text", "text": {"content": "Ngày nhập hàng"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "01/02/2026"}, "annotations": {"code": true}}],
              [{"type": "text", "text": {"content": "Tự động điền ngày hiện tại"}}]
            ]
          }
        },
        {
          "type": "table_row",
          "table_row": {
            "cells": [
              [{"type": "text", "text": {"content": "Mã tham chiếu"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "PO0281"}, "annotations": {"code": true}}],
              [{"type": "text", "text": {"content": "Mã đơn mua hàng (nếu có)"}}]
            ]
          }
        },
        {
          "type": "table_row",
          "table_row": {
            "cells": [
              [{"type": "text", "text": {"content": "Chọn kho"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "KHO CHÍNH"}, "annotations": {"code": true}}],
              [{"type": "text", "text": {"content": "Kho nhận hàng"}}]
            ]
          }
        }
      ]
    }
  }
]
```

#### 2.4 Phần Các Loại Nhập Hàng

```json
[
  {
    "type": "heading_2",
    "heading_2": {
      "rich_text": [{"type": "text", "text": {"content": "📝 Các Loại Nhập Hàng Thường Gặp"}}]
    }
  },
  {
    "type": "table",
    "table": {
      "table_width": 2,
      "has_column_header": true,
      "has_row_header": false,
      "children": [
        {
          "type": "table_row",
          "table_row": {
            "cells": [
              [{"type": "text", "text": {"content": "Loại"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "Mô tả"}, "annotations": {"bold": true}}]
            ]
          }
        },
        {
          "type": "table_row",
          "table_row": {
            "cells": [
              [{"type": "text", "text": {"content": "Nhập từ đơn đặt hàng"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "Có mã PO, liên kết đơn mua"}}]
            ]
          }
        },
        {
          "type": "table_row",
          "table_row": {
            "cells": [
              [{"type": "text", "text": {"content": "Nhập trực tiếp"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "Mua lẻ, không có đơn đặt"}}]
            ]
          }
        },
        {
          "type": "table_row",
          "table_row": {
            "cells": [
              [{"type": "text", "text": {"content": "Nhập điều chỉnh"}, "annotations": {"bold": true}}],
              [{"type": "text", "text": {"content": "Nhập bổ sung sau kiểm kê"}}]
            ]
          }
        }
      ]
    }
  },
  {
    "type": "divider",
    "divider": {}
  }
]
```

#### 2.5 Phần FAQ

```json
[
  {
    "type": "heading_2",
    "heading_2": {
      "rich_text": [{"type": "text", "text": {"content": "❓ Câu Hỏi Thường Gặp (FAQ)"}}]
    }
  },
  {
    "type": "heading_3",
    "heading_3": {
      "rich_text": [{"type": "text", "text": {"content": "Q1: Nhập sai số lượng có sửa được không?"}}]
    }
  },
  {
    "type": "paragraph",
    "paragraph": {
      "rich_text": [
        {"type": "text", "text": {"content": "A:"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": " Được nếu phiếu chưa xác nhận. Sau khi xác nhận cần tạo phiếu điều chỉnh."}}
      ]
    }
  },
  {
    "type": "heading_3",
    "heading_3": {
      "rich_text": [{"type": "text", "text": {"content": "Q2: Làm sao biết đã nhập đủ hàng theo đơn đặt?"}}]
    }
  },
  {
    "type": "paragraph",
    "paragraph": {
      "rich_text": [
        {"type": "text", "text": {"content": "A:"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": " Hệ thống tự động so sánh số lượng đặt và số lượng nhận, hiển thị trong đơn mua hàng."}}
      ]
    }
  },
  {
    "type": "heading_3",
    "heading_3": {
      "rich_text": [{"type": "text", "text": {"content": "Q3: Có thể nhập hàng vào nhiều kho cùng lúc không?"}}]
    }
  },
  {
    "type": "paragraph",
    "paragraph": {
      "rich_text": [
        {"type": "text", "text": {"content": "A:"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": " Mỗi phiếu nhập 1 kho. Cần tạo nhiều phiếu cho nhiều kho."}}
      ]
    }
  },
  {
    "type": "divider",
    "divider": {}
  }
]
```

#### 2.6 Phần Checklist

```json
[
  {
    "type": "heading_2",
    "heading_2": {
      "rich_text": [{"type": "text", "text": {"content": "📋 Checklist Hoàn Thành"}}]
    }
  },
  {
    "type": "to_do",
    "to_do": {
      "rich_text": [{"type": "text", "text": {"content": "Đã kiểm tra hàng thực tế trước khi nhập"}}],
      "checked": false
    }
  },
  {
    "type": "to_do",
    "to_do": {
      "rich_text": [{"type": "text", "text": {"content": "Đã chọn đúng nhà cung cấp"}}],
      "checked": false
    }
  },
  {
    "type": "to_do",
    "to_do": {
      "rich_text": [{"type": "text", "text": {"content": "Đã chọn đúng kho nhận hàng"}}],
      "checked": false
    }
  },
  {
    "type": "to_do",
    "to_do": {
      "rich_text": [{"type": "text", "text": {"content": "Đã nhập đầy đủ số lượng và giá"}}],
      "checked": false
    }
  },
  {
    "type": "to_do",
    "to_do": {
      "rich_text": [{"type": "text", "text": {"content": "Đã xác nhận phiếu nhập"}}],
      "checked": false
    }
  },
  {
    "type": "divider",
    "divider": {}
  },
  {
    "type": "callout",
    "callout": {
      "icon": {"type": "emoji", "emoji": "📌"},
      "rich_text": [
        {"type": "text", "text": {"content": "Bước tiếp theo"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": ": Sau khi nhập hàng vào kho chính, có thể "}},
        {"type": "text", "text": {"content": "chuyển kho"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": " sang kho quầy ở "}},
        {"type": "text", "text": {"content": "Bài 7.3"}, "annotations": {"bold": true}},
        {"type": "text", "text": {"content": "."}}
      ]
    }
  }
]
```

---

## ✅ Checklist Hoàn Thành

Khi tạo tài liệu Notion, đảm bảo:

- [ ] **Có đủ 6 phần**: Giới thiệu, Truy cập, Hướng dẫn, Loại/Trường hợp, FAQ, Checklist
- [ ] **Mỗi bước có bảng chi tiết**: Trường | Ví dụ | Giải thích
- [ ] **Mỗi bước có hình ảnh**: Sử dụng image block với external URL
- [ ] **Có callouts**: 💡 Mẹo, ⚠️ Lưu ý, 📌 Ghi nhớ
- [ ] **FAQ tối thiểu 3 câu**: Format Q: ... / A: ...
- [ ] **Checklist cuối**: Sử dụng to_do blocks
- [ ] **Dividers phân cách**: Giữa các phần lớn

---

## 🎯 Lưu ý quan trọng

1. **Không rút gọn nội dung**: Tài liệu Notion phải đầy đủ như markdown
2. **Bảng phải có header**: `has_column_header: true`
3. **Formatting nhất quán**: 
   - Tên trường: `annotations: {"bold": true}`
   - Giá trị ví dụ: `annotations: {"code": true}`
4. **Giới hạn 100 blocks**: Nếu quá nhiều, chia thành nhiều lần gọi API
5. **Hình ảnh phải public**: Upload lên ImgBB trước

---

*Tài liệu tham khảo cho skill trcf-course-documentation*
