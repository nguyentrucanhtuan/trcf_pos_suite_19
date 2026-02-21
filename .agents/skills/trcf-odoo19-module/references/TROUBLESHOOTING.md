# Odoo 19 Troubleshooting & Debug Guide

Catalog lỗi thường gặp và cách khắc phục trong Odoo 19.
Validation Status: Verified with caveat (some entries require runtime verification on target Odoo minor/saas build).

## Table of Contents
- 1. Lỗi Installation & Upgrade
- 2. Lỗi Views & XML
- 3. Lỗi Python/ORM
- 4. Lỗi JavaScript/OWL
- 5. Lỗi Security & Access Rights
- 6. Lỗi Controllers & Routes
- 7. Lỗi Cron Jobs
- 8. Lỗi Performance
- 9. Lỗi Timezone & Datetime
- 10. Lỗi Database & Migration
- Emergency Debug Techniques
- Related References

> [!TIP]
> **Quy tắc**: Mỗi khi giải quyết xong lỗi phức tạp, cập nhật ngay vào file này theo format **Error → Cause → Solution**.

---

## 🔍 Quick Debug Commands

Xem `SKILL.md` > **Command Baseline** để biết cách chạy install/upgrade/debug.

---

## 1️⃣ Lỗi Installation & Upgrade

### Error: "Module [name] could not be loaded"
- **Cause**: Syntax error trong Python hoặc missing `__init__.py`
- **Solution**: 
  1. Kiểm tra log chi tiết: `grep ERROR odoo.log`
  2. Verify tất cả folders có `__init__.py`
  3. Check Python syntax: `python -m py_compile models/*.py`

### Error: "External ID not found: [module.xml_id]"
- **Cause**: Dependency module chưa install hoặc XML ID sai
- **Solution**:
  1. Check `depends` trong `__manifest__.py`
  2. Install dependency: `./odoo-bin -i dependency_module`
  3. Verify XML ID tồn tại: Settings → Technical → External Identifiers

### Error: "Invalid field 'numbercall' on model 'ir.cron'" [Needs verification on target runtime]
- **Cause**: Field `numbercall` đã bị remove trong Odoo 19
- **Solution**: Xóa dòng `<field name="numbercall">` trong XML cron definition

### WARNING: "_sql_constraints is no longer supported"
- **Cause**: Odoo 19 deprecate `_sql_constraints`, thay bằng `models.Constraint`
- **Solution**:
```python
# ❌ CŨ
_sql_constraints = [('code_unique', 'UNIQUE(code)', 'Mã phải là duy nhất!')]

# ✅ MỚI (Odoo 19)
_code_unique = models.Constraint('UNIQUE(code)', 'Mã phải là duy nhất!')
```

### WARNING: POS assets not loading / custom JS not executed
- **Cause**: Dùng sai asset bundle name
- **Solution**:
```python
# ❌ CŨ (Odoo 16)
'point_of_sale.assets': [...]

# ✅ ĐÚNG (Odoo 17+/19)
'point_of_sale._assets_pos': [...]
```

---

## 2️⃣ Lỗi Views & XML

### Error: "Invalid view definition"
- **Cause**: XML structure không hợp lệ với Odoo 19
- **Solution**: Check các patterns sau:

```xml
<!-- ❌ WRONG: <tree> deprecated -->
<tree string="Title">

<!-- ✅ CORRECT: Use <list> -->
<list string="Title">

<!-- ❌ WRONG: attrs syntax -->
<field name="amount" attrs="{'invisible': [('state', '=', 'draft')]}"/>

<!-- ✅ CORRECT: Direct modifiers -->
<field name="amount" invisible="state == 'draft'"/>

<!-- ✅ VALID: <group> in search views for Group By -->
<search>
    <group expand="0" string="Group By">
        <filter name="group_state" string="State" context="{'group_by': 'state'}"/>
    </group>
</search>
```

### Error: "OwlError: field is undefined"
- **Cause**: Field chưa được declare trong model hoặc module chưa update
- **Solution**:
  1. Check field definition trong Python model
  2. Update module: `./odoo-bin -u module_name --stop-after-init`
  3. Hard refresh browser: `Cmd+Shift+R` (Mac) / `Ctrl+F5` (Win)
  4. Clear Odoo assets: Settings → Technical → Assets → Regenerate

### Error: "Missing 'card' template in kanban view"
- **Cause**: Kanban template name changed in Odoo 19
- **Solution**:

```xml
<!-- ❌ WRONG -->
<t t-name="kanban-box">

<!-- ✅ CORRECT -->
<t t-name="card">
```

### Error: "Field 'active_id' does not exist"
- **Cause**: Context variable not passed from action/wizard caller, or XML expression refers to undefined symbols.
- **Solution**:
  1. Verify the caller actually sets `active_id` / `active_ids` in context.
  2. Use `context.get('active_id')` style access where appropriate.
  3. Avoid hardcoded replacements (`active_id` -> `id`) without checking flow semantics.

---

## 3️⃣ Lỗi Python/ORM

### Error: "AttributeError: object has no attribute '_context'"
- **Cause**: Accessing `_context` on an object that is not an Odoo recordset/model instance, or context propagation was lost.
- **Solution**: Use `self.env.context` on recordsets and validate caller type/context flow before access.

```python
# ❌ WRONG
value = self._context.get('key')

# ✅ CORRECT
value = self.env.context.get('key')
```

### Error: "KeyError: '2025-12-15'" (Date operations)
- **Cause**: Timezone mismatch giữa UTC và local time
- **Solution**: Xem `BEST_PRACTICES.md` > **4. Xử lý Timezone** để biết cách convert chuẩn.

### Error: "AccessError: Record does not exist or was deleted"
- **Cause**: Multi-company access restriction
- **Solution**:

```python
# Option 1: Switch company context
record.with_company(company_id).action()

# Option 2: Check company before access
if record.company_id != self.env.company:
    raise UserError(_("Không có quyền truy cập"))

# Option 3: Bypass company check (careful!)
record.sudo().with_context(allowed_company_ids=[company_id]).action()
```

### Error: "cannot import name 'slug' from 'odoo.http'" [Needs verification on target runtime]
- **Cause**: `slug` utility is not exported from `odoo.http` in current runtime.
- **Solution**: Use `ir.http` helper methods via `request.env` compatibility wrapper.

```python
from odoo.http import request

def slug(value):
    """Compatibility wrapper for slug function"""
    return request.env['ir.http']._slug(value)

def unslug(value):
    """Compatibility wrapper for unslug function"""
    return request.env['ir.http']._unslug(value)
```

### Error: "RecursionError: maximum recursion depth exceeded"
- **Cause**: Infinite loop trong computed fields hoặc onchange
- **Solution**:
  1. Check computed field dependencies: `@api.depends('field1', 'field2')`
  2. Avoid circular dependencies
  3. Use `self.env.context.get('skip_compute')` flag nếu cần

---

## 4️⃣ Lỗi JavaScript/OWL

### Error: "Service rpc is not available"
- **Cause**: Service registration/load issue in current web client context, not a global removal of RPC capability.
- **Solution**: Use one of the supported patterns based on context.

```javascript
// Pattern A: Service style
import { useService } from "@web/core/utils/hooks";
const rpcService = useService("rpc");
await rpcService("/api/endpoint", params);

// Pattern B: Direct helper import
import { rpc } from "@web/core/network/rpc";
await rpc("/api/endpoint", params);
```

### Error: "Component does not render"
- **Cause**: Template name mismatch hoặc assets chưa được load
- **Solution**:

```javascript
// 1. Check template name matches XML
static template = "module_name.ComponentTemplate";

// 2. Verify assets in __manifest__.py
'assets': {
    'web.assets_backend': [
        'module_name/static/src/js/**/*.js',
        'module_name/static/src/xml/**/*.xml',
    ],
},

// 3. Regenerate assets
// Settings → Technical → Assets → Regenerate
```

### Error: "JS changes not reflecting"
- **Cause**: Browser cache hoặc Odoo assets cache
- **Solution**:
  1. Hard refresh: `Cmd+Shift+R` (Mac) / `Ctrl+F5` (Win)
  2. Clear browser cache: DevTools → Application → Clear site data
  3. Regenerate Odoo assets: Settings → Technical → Assets
  4. Run with `--dev=js` flag

### Error: "Cannot read property of undefined"
- **Cause**: Accessing undefined props hoặc state
- **Solution**:

```javascript
// Use optional chaining
const value = this.props.record?.data?.field_name;

// Or provide defaults
const value = this.props.record.data.field_name || 'default';

// Check existence first
if (this.state.data && this.state.data.items) {
    // Safe to access
}
```

---

## 5️⃣ Lỗi Security & Access Rights

### Error: "Access Denied" khi user thường truy cập
- **Cause**: Missing access rights trong `ir.model.access.csv`
- **Solution**:

```csv
id,name,model_id:id,group_id:id,perm_read,perm_write,perm_create,perm_unlink
access_trcf_model_user,trcf.model.user,model_trcf_model,base.group_user,1,1,1,1
access_trcf_model_manager,trcf.model.manager,model_trcf_model,base.group_system,1,1,1,1
```

### Error: "You are not allowed to access this document"
- **Cause**: Record rules filtering records
- **Solution**: Check record rules in Settings → Technical → Security → Record Rules

```python
# Debug: Bypass record rules temporarily
records = self.env['model.name'].sudo().search([])
```

---

## 6️⃣ Lỗi Controllers & Routes

### Error: "404 Not Found" cho custom route
- **Cause**: Route chưa được register hoặc syntax sai
- **Solution**:

```python
from odoo import http
from odoo.http import request

class MyController(http.Controller):
    
    @http.route('/my/route', type='http', auth='public', website=True)
    def my_route(self, **kwargs):
        return request.render('module.template')
```

### Error: "X-Frame-Options: deny" (Iframe blocked)
- **Cause**: Security header blocking iframe
- **Solution**:

```python
@http.route('/my/route', type='http', auth='public', allow_frames=True)
def my_route(self):
    return request.render('template')
```

Or set system parameter: `web.browser_security_disable_x_frame_options` = `True`

### Error: "CSRF validation failed"
- **Cause**: Missing CSRF token trong POST request
- **Solution**:

```javascript
// Include CSRF token in fetch requests
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;

fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-Csrf-Token': csrfToken,
    },
    body: JSON.stringify(data)
});
```

---

## 7️⃣ Lỗi Cron Jobs

### Error: "Cron job not executing"
- **Cause**: Cron inactive hoặc nextcall time sai
- **Solution**:

```python
# Check cron status
cron = self.env.ref('module.cron_xmlid')
print(f"Active: {cron.active}, Nextcall: {cron.nextcall}")

# Manually trigger cron
cron.method_direct_trigger()

# Fix nextcall time (convert local to UTC)
import pytz
local_tz = pytz.timezone('Asia/Ho_Chi_Minh')
local_time = local_tz.localize(datetime.strptime('07:00', '%H:%M'))
utc_time = local_time.astimezone(pytz.UTC)
cron.write({'nextcall': utc_time})
```

---

## 8️⃣ Lỗi Performance

### Error: "Request timeout" hoặc slow loading
- **Cause**: N+1 queries hoặc missing database indexes
- **Solution**: Xem `BEST_PRACTICES.md` > **6. Performance Patterns** (Prefetch & Batch Processing).

---

## 9️⃣ Lỗi Timezone & Datetime

### Error: "Shift không match với attendance"
- **Cause**: UTC vs Local timezone mismatch
- **Solution**: Xem `BEST_PRACTICES.md` > **4. Xử lý Timezone**.

---

## 🔟 Lỗi Database & Migration

### Error: "column does not exist" sau khi thêm field
- **Cause**: Module chưa được update
- **Solution**:

```bash
# Update module
./odoo-bin -c odoo19.conf -d database -u module_name --stop-after-init

# If still error, check field definition
# Ensure field is in correct model file
```

### Error: "duplicate key value violates unique constraint"
- **Cause**: Unique constraint conflict
- **Solution**:

```python
# Add SQL constraint in model (Odoo 19)
_unique_field = models.Constraint(
    'UNIQUE(field_name)',
    'Field must be unique!',
)

# Or check before create
existing = self.search([('field', '=', value)])
if existing:
    raise UserError(_("Record already exists"))
```

---

## 🆘 Emergency Debug Techniques

### Technique 1: Python Debugger (pdb)
```python
import pdb; pdb.set_trace()
# Code will pause here, use:
# n - next line
# c - continue
# p variable - print variable
# q - quit
```

### Technique 2: Logging
```python
import logging
_logger = logging.getLogger(__name__)

_logger.info("Info message")
_logger.warning("Warning message")
_logger.error("Error message")
_logger.debug("Debug message")  # Only shows with --log-level=debug
```

### Technique 3: Browser Console
```javascript
// In OWL component
console.log("Props:", this.props);
console.log("State:", this.state);

// Check network calls
// F12 → Network tab → Filter by XHR
```

---

## 📚 Related References

- [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) - Comprehensive testing guide
- [BEST_PRACTICES.md](BEST_PRACTICES.md) - Code quality standards
- [OWL_GUIDE.md](OWL_GUIDE.md) - Frontend development guide

---

*(Tiếp tục cập nhật khi phát hiện lỗi mới...)*
