# Custom Addons - Development Instructions

## Feature Specifications

Trước khi implement feature, PHẢI đọc spec tương ứng:

### Active Specs

1. **specs/001-attendance-tab/spec.md** - Thêm Tab Bảng Giờ Công Tháng vào `/dang-ky-ca`
   - Status: ✅ Implemented
   - Module: `trcf_fnb_staff`
   - 3 user stories, 11 FRs, 5 SCs

2. **specs/002-geo-attendance/spec.md** - Tab Chấm Công Geolocation GPS + IP verification
   - Status: ✅ Implemented
   - Module: `trcf_fnb_staff`
   - 4 user stories (incl. IP verification), 21 FRs, 7 SCs

3. **specs/001-momo-qr-payment/spec.md** - Thanh toán MoMo QR cho POS
   - Status: Draft
   - Module: `trcf_pos_momo` (chưa tạo)
   - 3 user stories, 18 FRs, 6 SCs

4. **specs/001-minvoice-vat/spec.md** - Xuất Hóa Đơn VAT qua MInvoice
   - Status: Draft
   - Module: `trcf_minvoice_vat` (chưa tạo)
   - 3 user stories, 15 FRs, 6 SCs

## Workflow: Implement Feature từ Spec

### Bước 1: Đọc & hiểu spec
```
Read custom_addons/specs/<feature>/spec.md
```
Chú ý: Clarifications, Edge Cases, và Out of Scope.

### Bước 2: Lập kế hoạch (Plan)
Từ spec, xác định:
- Models cần tạo/modify (xem Key Entities trong spec)
- Views cần tạo (form, list, template)
- Controllers cần tạo/modify (xem User Stories)
- Security rules cần thêm
- Tests cần viết (xem Acceptance Scenarios)

### Bước 3: Implement theo thứ tự
1. **Models** - Tạo/extend models theo Key Entities
2. **Security** - `ir.model.access.csv` + record rules
3. **Views** - XML views theo Odoo 19 conventions
4. **Controllers** - Routes cho frontend/API
5. **Templates** - QWeb templates cho frontend pages
6. **Static** - JS/CSS nếu cần
7. **Tests** - Unit + integration tests cho Acceptance Scenarios

### Bước 4: Verify
- Kiểm tra từng Acceptance Scenario trong spec
- Kiểm tra Edge Cases
- Đảm bảo Success Criteria đạt

## Workflow: Tạo Spec mới cho Feature

Khi user yêu cầu feature mới, tạo spec theo template:

```markdown
# Feature Specification: <Tên Feature>

**Feature Branch**: `<prefix>-<short-name>`
**Created**: <YYYY-MM-DD>
**Status**: Draft

---

## Clarifications
(Hỏi user để làm rõ yêu cầu trước khi viết spec)

## User Scenarios & Testing

### User Story N – <Mô tả> (Priority: P1/P2/P3)
<Mô tả chi tiết từ góc nhìn user>

**Why this priority**: <Lý do>
**Independent Test**: <Cách test độc lập>

**Acceptance Scenarios**:
1. **Given** ..., **When** ..., **Then** ...

### Edge Cases
- <Liệt kê các trường hợp biên>

## Requirements

### Functional Requirements
- **FR-001**: Hệ thống PHẢI ...

### Key Entities
- **<Entity name>**: <Mô tả fields và relationships>

## Success Criteria

### Measurable Outcomes
- **SC-001**: <Tiêu chí đo lường được>

## Assumptions
- <Giả định>

## Out of Scope
- <Những gì KHÔNG nằm trong scope>
```

## Workflow: Phân tích & Review Spec

Khi review spec, kiểm tra:
1. **Completeness** - Đủ user stories cho mọi actor?
2. **Clarity** - Acceptance scenarios cụ thể, không mơ hồ?
3. **Consistency** - FRs không mâu thuẫn nhau?
4. **Constitution alignment** - Tuân thủ 6 nguyên tắc Odoo 19?
5. **Edge cases** - Đã cover hết trường hợp biên?
6. **Measurability** - Success criteria đo lường được?

## Workflow: Tạo Checklist từ Spec

Sau khi spec hoàn chỉnh, tạo checklist kiểm tra:
- [ ] Mỗi FR có ít nhất 1 acceptance scenario
- [ ] Edge cases có handling plan
- [ ] Security requirements được address
- [ ] Performance considerations (N+1, batch, index)
- [ ] Migration script nếu thay đổi schema
- [ ] Tests cover business logic quan trọng

## Module Naming Convention

- Prefix: `trcf_` (Tuấn Rang Cà Phê)
- Pattern: `trcf_<domain>_<feature>` (e.g., `trcf_fnb_staff`, `trcf_pos_momo`)
- Model naming: `trcf.<domain>.<entity>` (e.g., `trcf.geo.location`, `trcf.work.shift`)
