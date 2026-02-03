# Testing Checklist cho Module Odoo 19

## 📋 Checklist Tổng Quan

Sử dụng checklist này sau mỗi lần tạo/cập nhật module để đảm bảo chất lượng.

---

## 1️⃣ Module Installation & Upgrade

### Installation Testing
```bash
# Test cài đặt module mới
./odoo-bin -c odoo19.conf -d test_db -i trcf_module_name --stop-after-init

# Kiểm tra log
# ✅ Không có ERROR hoặc CRITICAL
# ✅ Thấy "Module trcf_module_name: successfully installed"
```

- [ ] Module cài đặt thành công không có lỗi
- [ ] Tất cả dependencies được load đúng
- [ ] Database migrations chạy thành công
- [ ] Không có warning về missing dependencies

### Upgrade Testing
```bash
# Test nâng cấp module
./odoo-bin -c odoo19.conf -d test_db -u trcf_module_name --stop-after-init
```

- [ ] Module upgrade thành công
- [ ] Data migration không bị mất dữ liệu
- [ ] Computed fields được tính toán lại đúng
- [ ] Không có orphan records

---

## 2️⃣ Views & UI Testing

### List Views
- [ ] List view hiển thị đúng columns
- [ ] Sorting hoạt động (click vào header)
- [ ] Pagination hoạt động (nếu có >80 records)
- [ ] Action buttons hiển thị đúng
- [ ] Colors/decorations hiển thị đúng
- [ ] Editable list (nếu có) cho phép edit inline

### Form Views
- [ ] Form view load đầy đủ fields
- [ ] Required fields có dấu * đỏ
- [ ] Readonly fields không edit được
- [ ] Invisible fields ẩn đúng điều kiện
- [ ] Notebook tabs chuyển đổi mượt
- [ ] Statusbar hiển thị đúng states
- [ ] Smart buttons hoạt động
- [ ] Chatter (mail.thread) hoạt động (nếu có)

### Search Views
- [ ] Search bar tìm kiếm đúng
- [ ] Filters hoạt động
- [ ] Group By hoạt động
- [ ] Default filters apply đúng
- [ ] Custom filters có thể save

### Kanban Views
- [ ] Cards hiển thị đúng template
- [ ] Drag & drop hoạt động (nếu có)
- [ ] Quick create hoạt động
- [ ] Colors/priority hiển thị đúng

### Calendar/Gantt Views (nếu có)
- [ ] Events hiển thị đúng
- [ ] Drag & drop update dates
- [ ] Quick create từ calendar

---

## 3️⃣ Business Logic Testing

### Model Methods
```python
# Test trong Odoo shell
./odoo-bin shell -c odoo19.conf -d test_db

# Trong shell:
record = env['trcf.model'].create({'name': 'Test'})
record.custom_method()  # Test method
```

- [ ] Create records thành công
- [ ] Update records không lỗi
- [ ] Delete records (check constraints)
- [ ] Computed fields tính toán đúng
- [ ] Onchange methods hoạt động
- [ ] Constraints validate đúng
- [ ] Default values apply đúng

### Workflows & States
- [ ] State transitions hoạt động
- [ ] Button actions thay đổi state đúng
- [ ] Readonly/invisible theo state đúng
- [ ] Email notifications gửi đúng lúc (nếu có)

### Security & Access Rights
```bash
# Test với user khác admin
# Login as normal user và kiểm tra
```

- [ ] User có quyền đọc thấy records
- [ ] User không có quyền write không edit được
- [ ] User không có quyền create không tạo được
- [ ] User không có quyền unlink không xóa được
- [ ] Record rules filter đúng records
- [ ] Field-level security hoạt động (nếu có)

---

## 4️⃣ JavaScript/OWL Components Testing

### Component Rendering
- [ ] Component render đúng template
- [ ] Props truyền vào đúng
- [ ] State management hoạt động
- [ ] Event handlers hoạt động

### Services & RPC Calls
```javascript
// Kiểm tra trong browser console
// F12 > Console > Network tab
```

- [ ] RPC calls thành công (status 200)
- [ ] Data trả về đúng format
- [ ] Error handling hoạt động
- [ ] Loading states hiển thị

### Browser Compatibility
- [ ] Chrome/Edge hoạt động
- [ ] Firefox hoạt động
- [ ] Safari hoạt động (nếu cần)
- [ ] Mobile responsive (nếu cần)

---

## 5️⃣ API Endpoints & Controllers

### HTTP Routes Testing
```bash
# Test với curl hoặc Postman
curl -X POST http://localhost:8069/api/endpoint \
  -H "Content-Type: application/json" \
  -d '{"param": "value"}'
```

- [ ] GET endpoints trả về data đúng
- [ ] POST endpoints tạo/update thành công
- [ ] Authentication/CSRF token hoạt động
- [ ] Error responses trả về đúng status code
- [ ] JSON response format đúng chuẩn

---

## 6️⃣ Scheduled Actions (Cron Jobs)

### Cron Testing
```python
# Test trong Odoo shell
cron = env.ref('trcf_module.cron_job_xmlid')
cron.method_direct_trigger()  # Chạy ngay không đợi schedule
```

- [ ] Cron job chạy thành công
- [ ] Nextcall time update đúng
- [ ] Numbercall giảm đúng (nếu có limit)
- [ ] Error handling không crash server
- [ ] Log ghi lại execution

---

## 7️⃣ Reports & Printing

### QWeb Reports
- [ ] Report PDF generate thành công
- [ ] Layout đúng format
- [ ] Data hiển thị đầy đủ
- [ ] Multi-language support (nếu có)
- [ ] Company logo/header hiển thị

---

## 8️⃣ Performance Testing

### Query Performance
```bash
# Bật query logging
./odoo-bin -c odoo19.conf --log-sql
```

- [ ] Không có N+1 queries
- [ ] Queries có index đúng
- [ ] Load time < 2s cho list view
- [ ] Load time < 1s cho form view
- [ ] Memory usage hợp lý

### Large Dataset Testing
- [ ] Test với >1000 records
- [ ] Pagination hoạt động tốt
- [ ] Search/filter nhanh
- [ ] Export Excel/CSV không timeout

---

## 9️⃣ Integration Testing

### Module Dependencies
- [ ] Tất cả depends modules hoạt động
- [ ] Không conflict với modules khác
- [ ] Uninstall không break dependencies

### External Services (nếu có)
- [ ] API calls đến external services thành công
- [ ] Timeout handling đúng
- [ ] Retry logic hoạt động
- [ ] Error logging đầy đủ

---

## 🔟 Development Mode Testing

### Debug Mode
```bash
# Chạy với development mode
./odoo-bin -c odoo19.conf --dev=xml,css,js
```

- [ ] XML changes reload tự động
- [ ] CSS changes apply ngay
- [ ] JS changes không cần restart
- [ ] No cache issues

---

## ✅ Final Checklist

Trước khi deploy production:

- [ ] Tất cả tests ở trên đều PASS
- [ ] Code review đã hoàn thành
- [ ] Documentation đã cập nhật
- [ ] Changelog đã ghi lại
- [ ] Backup database trước khi upgrade
- [ ] Rollback plan đã chuẩn bị

---

## 🚨 Red Flags - Dừng ngay nếu thấy

- ❌ ERROR trong log khi install/upgrade
- ❌ Traceback Python trong console
- ❌ JavaScript errors trong browser console
- ❌ Views không load (blank screen)
- ❌ Data bị mất sau upgrade
- ❌ Performance chậm hơn version cũ
- ❌ Security warnings

---

## 📝 Testing Report Template

```markdown
# Testing Report - [Module Name] v[Version]

**Date**: YYYY-MM-DD
**Tester**: [Tên]
**Environment**: Odoo 19.0 / Database: [DB Name]

## Test Results

| Category | Status | Notes |
|----------|--------|-------|
| Installation | ✅/❌ | |
| Views | ✅/❌ | |
| Business Logic | ✅/❌ | |
| JavaScript | ✅/❌ | |
| API Endpoints | ✅/❌ | |
| Cron Jobs | ✅/❌ | |
| Reports | ✅/❌ | |
| Performance | ✅/❌ | |

## Issues Found

1. [Issue description]
   - **Severity**: High/Medium/Low
   - **Steps to reproduce**: ...
   - **Expected**: ...
   - **Actual**: ...

## Conclusion

- [ ] Ready for production
- [ ] Needs fixes
- [ ] Blocked by: ...
```

---

## 🔗 Related References

- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Khi gặp lỗi
- [BEST_PRACTICES.md](BEST_PRACTICES.md) - Code quality
- [OWL_GUIDE.md](OWL_GUIDE.md) - Frontend testing
