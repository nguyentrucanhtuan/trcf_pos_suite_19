 #!/usr/bin/env python3
"""
Script đồng bộ tài liệu Markdown lên Notion với formatting đầy đủ theo chuẩn TRCF
Tự động parse Markdown và tạo tables, callouts, images

Sử dụng: python3 sync_to_notion.py <file_markdown.md>
"""

import os
import sys
import re
from notion_client import Client
from pathlib import Path

# Cấu hình
NOTION_API_KEY = "ntn_a622032207869SnUhDmqk3gZjzW2OFbBDMOuUGPSScE3dv"
PARENT_PAGE_ID = "2ef172c2951e803da68aec0574f3aca4"
IMGBB_API_KEY = "0b893385aabdc7ded0fea2ee14d45156"

def parse_markdown_to_notion_blocks(md_content, image_urls=None):
    """
    Parse Markdown thành Notion blocks với formatting đầy đủ
    Hỗ trợ: headings, paragraphs, lists, tables, callouts, images
    """
    blocks = []
    lines = md_content.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].rstrip()
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Heading 1
        if line.startswith('# '):
            blocks.append({
                "type": "heading_1",
                "heading_1": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                }
            })
        
        # Heading 2 (thêm emoji nếu có)
        elif line.startswith('## '):
            content = line[3:]
            blocks.append({
                "type": "heading_2",
                "heading_2": {
                    "rich_text": [{"type": "text", "text": {"content": content}}]
                }
            })
        
        # Heading 3
        elif line.startswith('### '):
            blocks.append({
                "type": "heading_3",
                "heading_3": {
                    "rich_text": [{"type": "text", "text": {"content": line[4:]}}]
                }
            })
        
        # Divider
        elif line.strip() == '---':
            blocks.append({"type": "divider", "divider": {}})
        
        # Code block (```)
        elif line.startswith('```'):
            language = line[3:].strip() or "plain text"
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].startswith('```'):
                code_lines.append(lines[i])
                i += 1
            code_content = '\n'.join(code_lines)
            blocks.append({
                "type": "code",
                "code": {
                    "language": language,
                    "rich_text": [{"type": "text", "text": {"content": code_content}}]
                }
            })
        
        # Callout (💡 hoặc ⚠️)
        elif line.startswith('> 💡') or line.startswith('> ⚠️'):
            emoji = "💡" if "💡" in line else "⚠️"
            content = line.replace('> 💡', '').replace('> ⚠️', '').strip()
            # Parse rich text (bold, code)
            rich_text = parse_rich_text(content)
            blocks.append({
                "type": "callout",
                "callout": {
                    "icon": {"type": "emoji", "emoji": emoji},
                    "rich_text": rich_text
                }
            })
        
        # Quote
        elif line.startswith('> '):
            blocks.append({
                "type": "quote",
                "quote": {
                    "rich_text": [{"type": "text", "text": {"content": line[2:]}}]
                }
            })
        
        # Table (Markdown table)
        elif '|' in line and i + 1 < len(lines) and '|' in lines[i + 1]:
            table_lines = [line]
            i += 1
            # Skip separator line (|---|---|)
            if re.match(r'^\|[\s\-:]+\|', lines[i]):
                i += 1
            # Collect table rows
            while i < len(lines) and '|' in lines[i]:
                table_lines.append(lines[i])
                i += 1
            i -= 1  # Back one line
            
            # Parse table
            if len(table_lines) >= 2:
                table_block = parse_markdown_table(table_lines)
                if table_block:
                    blocks.append(table_block)
        
        # Bullet list
        elif line.startswith('- ') or line.startswith('* '):
            content = line[2:]
            # Parse bold text **text**
            rich_text = parse_rich_text(content)
            blocks.append({
                "type": "bulleted_list_item",
                "bulleted_list_item": {
                    "rich_text": rich_text
                }
            })
        
        # Numbered list
        elif re.match(r'^\d+\.\s', line):
            content = re.sub(r'^\d+\.\s', '', line)
            rich_text = parse_rich_text(content)
            blocks.append({
                "type": "numbered_list_item",
                "numbered_list_item": {
                    "rich_text": rich_text
                }
            })
        
        # Image
        elif line.startswith('!['):
            match = re.match(r'!\[(.*?)\]\((.*?)\)', line)
            if match:
                caption = match.group(1)
                url = match.group(2)
                # Nếu là local path, cần upload lên ImgBB trước
                if url.startswith('http'):
                    blocks.append({
                        "type": "image",
                        "image": {
                            "type": "external",
                            "external": {"url": url},
                            "caption": [{"type": "text", "text": {"content": caption}}] if caption else []
                        }
                    })
        
        # Regular paragraph
        else:
            rich_text = parse_rich_text(line)
            if rich_text:
                blocks.append({
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": rich_text
                    }
                })
        
        i += 1
    
    return blocks

def parse_rich_text(text):
    """Parse text với bold, italic, code"""
    rich_text = []
    
    # Simple implementation: split by **bold** and `code`
    parts = re.split(r'(\*\*.*?\*\*|`.*?`)', text)
    
    for part in parts:
        if not part:
            continue
        
        if part.startswith('**') and part.endswith('**'):
            # Bold text
            content = part[2:-2]
            rich_text.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"bold": True}
            })
        elif part.startswith('`') and part.endswith('`'):
            # Code text
            content = part[1:-1]
            rich_text.append({
                "type": "text",
                "text": {"content": content},
                "annotations": {"code": True}
            })
        else:
            # Normal text
            rich_text.append({
                "type": "text",
                "text": {"content": part}
            })
    
    return rich_text

def parse_markdown_table(table_lines):
    """Parse Markdown table thành Notion table block"""
    if len(table_lines) < 2:
        return None
    
    # Parse header
    header_cells = [cell.strip() for cell in table_lines[0].split('|')[1:-1]]
    table_width = len(header_cells)
    
    # Parse rows
    rows = []
    
    # Header row
    header_row_cells = []
    for cell in header_cells:
        cell_text = cell.replace('**', '').strip()
        header_row_cells.append([{
            "type": "text",
            "text": {"content": cell_text},
            "annotations": {"bold": True}
        }])
    
    rows.append({
        "type": "table_row",
        "table_row": {"cells": header_row_cells}
    })
    
    # Data rows
    for line in table_lines[1:]:
        cells = [cell.strip() for cell in line.split('|')[1:-1]]
        if len(cells) != table_width:
            continue
        
        row_cells = []
        for i, cell in enumerate(cells):
            # First column is bold
            is_first_col = (i == 0)
            # Parse bold **text** and code `text`
            cell_rich_text = []
            
            if '**' in cell:
                cell = cell.replace('**', '')
                cell_rich_text.append({
                    "type": "text",
                    "text": {"content": cell},
                    "annotations": {"bold": True}
                })
            elif '`' in cell:
                cell = cell.replace('`', '')
                cell_rich_text.append({
                    "type": "text",
                    "text": {"content": cell},
                    "annotations": {"code": True}
                })
            else:
                cell_rich_text.append({
                    "type": "text",
                    "text": {"content": cell},
                    "annotations": {"bold": is_first_col}
                })
            
            row_cells.append(cell_rich_text)
        
        rows.append({
            "type": "table_row",
            "table_row": {"cells": row_cells}
        })
    
    return {
        "type": "table",
        "table": {
            "table_width": table_width,
            "has_column_header": True,
            "has_row_header": False,
            "children": rows
        }
    }

def upload_to_notion(file_path):
    """Upload file Markdown lên Notion"""
    
    # Đọc file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Lấy tiêu đề từ dòng đầu tiên
    first_line = content.split('\n')[0]
    title = first_line.replace('# ', '').strip() if first_line.startswith('# ') else Path(file_path).stem
    
    # Khởi tạo Notion client
    notion = Client(auth=NOTION_API_KEY)
    
    # Tạo page mới
    print(f"Đang tạo page: {title}")
    new_page = notion.pages.create(
        parent={"page_id": PARENT_PAGE_ID},
        properties={
            "title": {
                "title": [{"text": {"content": title}}]
            }
        }
    )
    
    page_id = new_page["id"]
    print(f"✓ Đã tạo page ID: {page_id}")
    
    # Parse content thành blocks
    print("Đang parse Markdown...")
    blocks = parse_markdown_to_notion_blocks(content)
    
    # Upload blocks (Notion giới hạn 100 blocks/request)
    print(f"Đang upload {len(blocks)} blocks...")
    batch_size = 100
    for i in range(0, len(blocks), batch_size):
        batch = blocks[i:i+batch_size]
        try:
            notion.blocks.children.append(
                block_id=page_id,
                children=batch
            )
            print(f"✓ Đã upload {min(i+batch_size, len(blocks))}/{len(blocks)} blocks")
        except Exception as e:
            print(f"✗ Lỗi khi upload batch {i//batch_size + 1}: {e}")
            import traceback
            traceback.print_exc()
    
    # Lấy URL của page
    page_url = f"https://www.notion.so/{page_id.replace('-', '')}"
    print(f"\n✅ Hoàn thành! URL: {page_url}")
    return page_url

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Sử dụng: python3 sync_to_notion.py <file_markdown>")
        print("\nVí dụ:")
        print("  python3 sync_to_notion.py khoa_hoc/chuong_6/6.1_tao_nhan_vien.md")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"✗ Không tìm thấy file: {file_path}")
        sys.exit(1)
    
    try:
        upload_to_notion(file_path)
    except Exception as e:
        print(f"✗ Lỗi: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
