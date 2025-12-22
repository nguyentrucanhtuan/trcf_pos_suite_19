# 📄 Standard Odoo 19 Templates

Bộ templates chuẩn cho các module Odoo 19 không sử dụng AI Agent.

## 📁 Cấu trúc
```
odoo19_standard/
├── __manifest__.py.template      # Manifest chuẩn Odoo 19
├── __init__.py.template          # Root init
├── models/
│   ├── __init__.py.template      # Models init
│   └── model.py.template         # Model chuẩn với CRUD/Actions
├── views/
│   └── views.xml.xml.template    # List, Form, Search, Menu
├── security/
│   └── ir.model.access.csv.template
└── static/src/                   # OWL Components
    ├── js/xml/css/               # JS/XML/CSS templates
```

## 🚀 Cách dùng
Dùng lệnh `/trcf_module_create` để AI tự động áp dụng bộ template này khi tạo module mới.
