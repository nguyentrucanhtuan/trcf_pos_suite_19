# -*- coding: utf-8 -*-
"""
Lightweight EN translation layer for trcf_fnb_staff's custom HTTP-rendered
pages (plain Odoo http.Controller routes, not wired into Odoo's built-in
website translation system, so they need their own mechanism).

Mirrors trcf_fnb_inventory/i18n.py -- see that module for the full
rationale. Kept as a separate dict per module rather than a shared import
so each module's translations stay self-contained.

All native template/controller strings are Vietnamese. This module maps
them to English and exposes a `t()` callable that controllers pass into
their render() vals, and templates call as `t('Vietnamese text')`.

The language used is whatever the logged-in user has set under
My Profile > Preferences > Language (res.users.lang).

Usage in a controller:
    from ..i18n import get_translator
    ...
    vals = {'t': get_translator(request), ...}
    return request.render('trcf_fnb_staff.some_template', vals)

Usage in a QWeb template (for a Vietnamese string that appears in an
attribute or text node):
    <t t-esc="t('Đăng ký ca')"/>

If a string isn't in VI_TO_EN yet, t() just returns the original
Vietnamese text unchanged -- it never raises, so it's safe to wrap a
string before its translation has been added to the dict.
"""

VI_TO_EN = {
    # --- Shift registration: controller messages ---
    'Không tìm thấy thông tin nhân viên': 'Employee information not found',
    'Vui lòng chọn ít nhất một ca': 'Please select at least one shift',
    'Đã đăng ký thành công {count} ca!': 'Successfully registered {count} shift(s)!',
    'Đã hủy đăng ký!': 'Registration cancelled!',
    'Không tìm thấy đăng ký hoặc đăng ký đã được duyệt': 'Registration not found, or it has already been approved',

    # --- Shift registration: attendance status ---
    'Đúng giờ': 'On time',
    'Trễ {mins}': 'Late {mins}',
    'Sớm {mins}': 'Early {mins}',

    # --- Shift registration: weekday abbreviations ---
    'T2': 'Mon',
    'T3': 'Tue',
    'T4': 'Wed',
    'T5': 'Thu',
    'T6': 'Fri',
    'T7': 'Sat',
    'CN': 'Sun',

    # --- Geo attendance JS bridge (window.TRCF_STAFF_I18N) ---
    'Hợp lệ ✓': 'Valid ✓',
    'Ngoài vùng ✗': 'Out of range ✗',
    'mét so với cơ sở gần nhất': 'meters from nearest location',
    'km so với cơ sở gần nhất': 'km from nearest location',
    'Không thể xác định vị trí GPS.': 'Unable to determine GPS location.',
    'Bạn đã từ chối quyền truy cập vị trí. Vui lòng bật lại trong cài đặt trình duyệt.': 'You denied location access. Please re-enable it in your browser settings.',
    'Tín hiệu GPS không khả dụng. Vui lòng thử lại.': 'GPS signal unavailable. Please try again.',
    'Hết thời gian chờ GPS. Đang thử lại...': 'GPS request timed out. Retrying...',
    'Check-in thành công lúc {time} tại {location}': 'Checked in successfully at {time} at {location}',
    '⚠️ Cảnh báo: Thiết bị không kết nối đúng mạng WiFi văn phòng.': '⚠️ Warning: Device is not connected to the office WiFi network.',
    'Check-out thành công! Tổng giờ làm: {hours}': 'Checked out successfully! Total hours worked: {hours}',
    'Lỗi kết nối. Vui lòng thử lại.': 'Connection error. Please try again.',
    'Bạn đang ở ngoài vùng cho phép. Khoảng cách: {distance}m (bán kính: {radius}m)': 'You are out of the allowed range. Distance: {distance}m (radius: {radius}m)',
    'Thiết bị không kết nối đúng mạng WiFi văn phòng.': 'Device is not connected to the office WiFi network.',
    'Bạn đã check-in lúc {time}. Vui lòng check-out trước.': 'You already checked in at {time}. Please check out first.',
    'Không có phiên làm việc đang mở. Vui lòng check-in trước.': 'No open work session. Please check in first.',
    'Cơ sở chưa được cấu hình vị trí GPS. Vui lòng liên hệ quản trị.': 'This location has no GPS configuration. Please contact admin.',
    'Không tìm thấy thông tin nhân viên. Vui lòng liên hệ HR.': 'Employee information not found. Please contact HR.',
    'Đã xảy ra lỗi. Vui lòng thử lại.': 'An error occurred. Please try again.',

    # --- Shift registration: page template ---
    'Đăng ký ca & Bảng giờ công': 'Shift Registration & Timesheet',
    'Quản lý ca làm việc': 'Shift Management',
    'Xin chào,': 'Hello,',
    'Đăng ký ca': 'Register Shift',
    'Bảng giờ công': 'Timesheet',
    'Chấm Công': 'Attendance',
    'Chọn các ca bạn muốn đăng ký trong 2 tuần tới': 'Select the shifts you want to register for the next 2 weeks',
    'Ngày': 'Date',
    'Đã duyệt': 'Approved',
    'Lưu đăng ký': 'Save Registration',
    'Đã chọn:': 'Selected:',
    'ca': 'shift(s)',
    'Đã đăng ký (chờ duyệt)': 'Registered (pending approval)',
    'Đang chọn': 'Selecting',
    'Chưa chọn': 'Not selected',
    'Xem tháng:': 'View month:',
    'Tháng 1': 'January',
    'Tháng 2': 'February',
    'Tháng 3': 'March',
    'Tháng 4': 'April',
    'Tháng 5': 'May',
    'Tháng 6': 'June',
    'Tháng 7': 'July',
    'Tháng 8': 'August',
    'Tháng 9': 'September',
    'Tháng 10': 'October',
    'Tháng 11': 'November',
    'Tháng 12': 'December',
    'Đang tải...': 'Loading...',
    'Không có dữ liệu chấm công trong tháng này.': 'No attendance data for this month.',
    'Giờ vào': 'Check-in',
    'Giờ ra': 'Check-out',
    'TG làm việc': 'Hours worked',
    'Đi': 'In',
    'Về': 'Out',
    'Lương phiên': 'Session pay',
    'Nguồn chấm công': 'Attendance source',
    'Tổng lương tháng': 'Total monthly pay',
    'Tạm tính': 'Provisional',
    'Trình duyệt của bạn không hỗ trợ GPS. Vui lòng dùng trình duyệt hiện đại (Chrome / Safari / Firefox).': 'Your browser does not support GPS. Please use a modern browser (Chrome / Safari / Firefox).',
    'Đang xác định vị trí...': 'Determining location...',
    'Độ chính xác GPS rất cao (< 5m). Có thể dùng GPS giả lập. Hệ thống sẽ ghi nhận cảnh báo.': 'GPS accuracy is unusually high (< 5m). Spoofed GPS may be in use. The system will log a warning.',
    'Đang trong ca': 'Currently on shift',
    'Bạn đang nằm ngoài vùng cho phép. Check-out sẽ bị từ chối.': 'You are outside the allowed area. Check-out will be rejected.',
    'Tổng giờ làm hôm nay:': "Total hours worked today:",
    'Lương tạm tính:': 'Provisional pay:',
    'Năm': 'Year',
    'Lỗi không xác định': 'Unknown error',
    'Lỗi kết nối:': 'Connection error:',
    'Đang làm': 'Working',
    'Bạn muốn hủy đăng ký ca này?': 'Do you want to cancel this shift registration?',
    'Vui lòng chọn ít nhất một ca!': 'Please select at least one shift!',
    'Đang lưu...': 'Saving...',
    'Lỗi:': 'Error:',
    'Không xác định': 'Unknown',
    'Lỗi': 'Error',
    'Tài khoản của bạn chưa được liên kết với nhân viên. Vui lòng liên hệ quản trị viên.': 'Your account is not linked to an employee record. Please contact an administrator.',
    'Về trang chủ': 'Go to homepage',

    # --- Shift schedule grid: controller ---
    'Bạn không có quyền thực hiện thao tác này': "You don't have permission to perform this action",
    'Nhân viên đã được xếp vào ca này': 'This employee is already assigned to this shift',
    'Không tìm thấy đăng ký': 'Registration not found',
    'Đã duyệt {count} đăng ký ca!': 'Approved {count} shift registration(s)!',
    'Thứ 2': 'Mon',
    'Thứ 3': 'Tue',
    'Thứ 4': 'Wed',
    'Thứ 5': 'Thu',
    'Thứ 6': 'Fri',
    'Thứ 7': 'Sat',
    'Chủ nhật': 'Sun',

    # --- Shift schedule grid: template ---
    'Xếp ca theo tuần': 'Weekly Shift Schedule',
    'Tuần trước': 'Previous Week',
    'Tuần sau': 'Next Week',
    'Duyệt tất cả': 'Approve All',
    'Ca / Ngày': 'Shift / Date',
    'NV': 'staff',
    'Duyệt': 'Approve',
    'Từ chối': 'Reject',
    'Xóa': 'Remove',
    'Duyệt lại': 'Re-approve',
    'Thêm nhân viên': 'Add Employee',
    'Đã duyệt': 'Approved',
    'Chờ duyệt': 'Pending approval',
    'Đóng': 'Close',
    'Thêm': 'Add',
    'Tìm kiếm nhân viên...': 'Search employees...',
    'Bạn có chắc muốn xóa nhân viên này?': 'Are you sure you want to remove this employee?',
    'Lỗi:': 'Error:',
    'Không xác định': 'Unknown',
    'Vui lòng chọn nhân viên!': 'Please select an employee!',
    'Bạn có chắc muốn duyệt tất cả đăng ký ca trong tuần này?': 'Are you sure you want to approve all shift registrations for this week?',
    'Đang duyệt...': 'Approving...',
    'Không có quyền': 'Access Denied',
    'Từ chối truy cập': 'Access Denied',
    'Bạn không có quyền truy cập trang này. Chỉ HR mới có thể xem lịch xếp ca.': 'You do not have permission to access this page. Only HR can view the shift schedule.',

    # --- Task dashboard: controller + page ---
    'Bảng công việc chung': 'Team Task Board',
    'Tất cả nhân viên': 'All Employees',
    'Công việc của tôi': 'My Tasks',
    'Tài khoản của bạn chưa được liên kết với nhân viên.': 'Your account is not linked to an employee record.',
    'Không tìm thấy nhân viên': 'Employee not found',
    'Không tìm thấy công việc': 'Task not found',
    'Đang tải dữ liệu...': 'Loading data...',
    'Không có quyền': 'Access Denied',
    'Về trang chủ': 'Go to homepage',

    # --- Task dashboard: JS bridge (window.TRCF_TASK_I18N) ---
    'Không xác định': 'Unknown',
    'Lỗi:': 'Error:',
    'Xác nhận hoàn thành?': 'Confirm completion?',
    'Tiến độ chung': 'Overall progress',
    'Tiến độ hôm nay': "Today's progress",
    'công việc hoàn thành': 'tasks completed',
    'Đang chờ': 'Pending',
    'Hoàn thành': 'Done',
    'Quá hạn': 'Overdue',
    '⚠️ Sắp tới': '⚠️ Coming up',
    '🚨 Cần làm ngay': '🚨 Needs attention now',
    'Bắt đầu': 'Start',
    'công việc': 'tasks',
    'Chưa có công việc hôm nay': 'No tasks today',
    'Không có công việc hôm nay': 'No tasks today',
    'Chưa có nhân viên nào được gán công việc': 'No employees have been assigned tasks',
    'Bạn chưa được gán công việc nào': 'You have not been assigned any tasks',
}


def get_translator(request):
    """Return a callable t(vi_text) -> localized text based on the
    logged-in user's language preference."""
    lang = (request.env.user.lang or 'vi_VN')
    is_english = lang.startswith('en')

    def t(text):
        if not is_english:
            return text
        return VI_TO_EN.get(text, text)

    return t
