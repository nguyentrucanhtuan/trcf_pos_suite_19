# -*- coding: utf-8 -*-
from odoo import models, fields, api
from collections import defaultdict
import pytz
from odoo.exceptions import UserError
from odoo import _
import traceback
from datetime import datetime, timedelta, time

# Hằng số cấu hình
DUPLICATE_THRESHOLD_MINUTES = 15  # Ngưỡng phát hiện duplicate (phút)

class TrcfZktecoDevice(models.Model):
    _name = 'trcf.zkteco.device'
    _description = 'Thiết bị ZKTeco'
    _rec_name = 'name'
    _order = 'name'
    
    sync_date_from = fields.Date(
        string='Từ ngày',
        default=lambda self: fields.Date.today().replace(day=1),  # Ngày 1 tháng hiện tại
        store=False  # ✅ Không lưu vào database
    )

    sync_date_to = fields.Date(
        string='Đến ngày', 
        default=fields.Date.today,  # Ngày hiện tại
        store=False  # ✅ Không lưu vào database
    )

    # ===== BASIC FIELDS =====
    name = fields.Char(
        string='Tên thiết bị',
        required=True,
        help='Tên hiển thị của thiết bị ZKTeco'
    )
    
    ip_address = fields.Char(
        string='Địa chỉ IP',
        required=True,
        help='Địa chỉ IP của thiết bị (VD: 192.168.1.100)'
    )
    
    port = fields.Integer(
        string='Port',
        default=4370,
        required=True,
        help='Port kết nối đến thiết bị (mặc định: 4370)'
    )
    
    password = fields.Char(
        string='Mật khẩu',
        help='Mật khẩu kết nối đến thiết bị (nếu có)'
    )
    
    timeout = fields.Integer(
        string='Timeout (giây)',
        default=30,
        help='Thời gian chờ kết nối tối đa (10-300 giây)'
    )
    
    # ===== STATUS FIELDS =====
    is_connected = fields.Boolean(
        string='Trạng thái kết nối',
        compute='_compute_connection_status',
        store=False,
        help='Trạng thái kết nối hiện tại với thiết bị'
    )
    
    device_info = fields.Text(
        string='Thông tin thiết bị',
        readonly=True,
        help='Thông tin chi tiết về thiết bị'
    )
    
    last_sync_date = fields.Datetime(
        string='Lần sync cuối',
        readonly=True,
        help='Thời điểm đồng bộ dữ liệu gần nhất'
    )
    
    # ===== ADDITIONAL FIELDS =====
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Kích hoạt/Vô hiệu hóa thiết bị'
    )

    @api.depends()
    def _compute_connection_status(self):
        """Kiểm tra kết nối bằng cách lấy serial number"""
        for record in self:
            try:
                from zk import ZK
                
                # Kiểm tra có IP không
                if not record.ip_address:
                    record.is_connected = False
                    continue
                
                # Thử kết nối và lấy serial
                zk = ZK(record.ip_address, port=record.port or 4370, timeout=3)
                conn = zk.connect()
                
                if conn:
                    try:
                        # Lấy serial number làm test kết nối
                        serial = conn.get_serialnumber()
                        record.is_connected = bool(serial)
                    finally:
                        conn.disconnect()
                else:
                    record.is_connected = False
                
            except Exception:
                record.is_connected = False

    # ====== METHOD =====
    def action_check_connection(self):
        try:
            from zk import ZK
            
            # Kết nối và lấy tên thiết bị
            zk = ZK(self.ip_address, port=self.port or 4370, timeout=5)
            conn = zk.connect()
            
            if conn:
                serial_number = conn.get_serialnumber()
                user_count = len(conn.get_users())      # Số lượng user
                # firmware = conn.get_firmware_version()  # Phiên bản firmware
                # platform = conn.get_platform()         # Platform info
                # mac_address = conn.get_mac()            # MAC address (nếu hỗ trợ)

                conn.disconnect()
                
                # Cập nhật trạng thái
                self.is_connected = True

                message = f'Serial: {serial_number} - {user_count} nhân viên'
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '✅ Kết nối thành công',
                        'message': message,
                        'type': 'success',
                    }
                }
            else:
                self.is_connected = False
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '❌ Kết nối thất bại',
                        'message': 'Không thể kết nối thiết bị',
                        'type': 'danger',
                    }
                }
        
        except Exception as e:
            self.is_connected = False
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '❌ Lỗi',
                    'message': f'{str(e)}',
                    'type': 'danger',
                }
            }

    def action_sync_data(self):
        """Đồng bộ dữ liệu từ thiết bị ZKTeco"""

        # SET TIMEZONE TRƯỚC KHI SYNC
        self.action_set_timezone()

        try:
            from zk import ZK
            # Kết nối đến thiết bị
            zk = ZK(self.ip_address, port=self.port or 4370, timeout=5)
            conn = zk.connect()
            
            if not conn:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '❌ Lỗi kết nối',
                        'message': 'Không thể kết nối đến thiết bị',
                        'type': 'danger',
                    }
                }
            
            try:
                # Lấy danh sách users => users_data
                users = conn.get_users()
                users_data = []
                for user in users:
                    user_info = {
                        'uid': user.uid,
                        'name': user.name,
                        'privilege': user.privilege,
                        'password': user.password,
                        'group_id': user.group_id,
                        'user_id': user.user_id,
                    }
                    users_data.append(user_info)
                    print(f"ID: {user.uid} | Name: {user.name} | Privilege: {user.privilege} | Group: {user.group_id}")

                # Lấy dữ liệu chấm công
                attendances = conn.get_attendance()
                print("=== DỮ LIỆU CHẤM CÔNG THÁNG===")
                attendance_data = []

                # ===== FILTER THEO KHOẢNG THỜI GIAN =====
                sync_from = self.env.context.get('sync_from') or self.sync_date_from
                sync_to = self.env.context.get('sync_to') or self.sync_date_to

                # Convert về datetime.date - cách Odoo chuẩn
                if sync_from:
                    sync_from = fields.Date.from_string(sync_from) if isinstance(sync_from, str) else sync_from
                if sync_to:
                    sync_to = fields.Date.from_string(sync_to) if isinstance(sync_to, str) else sync_to

                for att in attendances:
                    att_date = att.timestamp.date()
                    # Kiểm tra trong khoảng thời gian
                    if sync_from <= att_date <= sync_to:
                        attendance_info = {
                            'uid': att.uid,
                            'user_id': att.user_id,
                            'timestamp': att.timestamp.strftime('%Y-%m-%d %H:%M:%S') if att.timestamp else None,
                            'status': att.status,
                            'punch': att.punch,
                            'date': att.timestamp.date() if att.timestamp else None,
                            'time': att.timestamp.time() if att.timestamp else None,
                        }
                        attendance_data.append(attendance_info)
                        print(f"User ID: {att.user_id} | Time: {att.timestamp}")
                
                # Sắp xếp lại thứ tự theo thời gian
                attendance_data.sort(key=lambda x: datetime.strptime(x['timestamp'], '%Y-%m-%d %H:%M:%S'))
                print(f"\nTổng số bản ghi chấm công {sync_from} - {sync_to}: {len(attendance_data)}")

                attendance_group = defaultdict(lambda: defaultdict(list))
                
                for record in attendance_data:
                    user_id_tamp = str(record['user_id'])
                    date_tamp = str(record['date'])
                    if not user_id_tamp or not date_tamp:
                        continue
                    attendance_group[user_id_tamp][date_tamp].append(record)

                #Danh sách hr_attendance_list sẵn sàn đưa vào dữ liệu
                hr_attendance_list = []
                
                for user_id, dates_dict in attendance_group.items(): 
                    print(f"\n=== Xử lý User ID: {user_id} ===")

                    # Chuyển user_id trên máy thành employee_id
                    employee_find  = self._find_employee_by_device_id(user_id)
                    if not employee_find:
                        print(f"❌ Không tìm thấy employee với device_user_id: {user_id}")
                        continue
                    
                    # Sắp xếp các ngày theo thứ tự thời gian
                    sorted_dates = sorted(dates_dict.keys())
                    
                    for date_str in sorted_dates:
                        attendance_list = dates_dict.get(date_str, [])
                        if not attendance_list:
                            continue
                        print(f"  📅 Ngày: {date_str}")
                        
                        # Sắp xếp theo thời gian trong ngày
                        attendance_list.sort(key=lambda record: datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S'))
                        
                        check_count = 0;
                        for current_record in attendance_list: 
                            if(check_count == 0):
                                print(f"    ✅ CHECKIN: {current_record['timestamp']}")
                                checkin_str = current_record['timestamp']

                                hr_attendance_record = {}
                                hr_attendance_record['employee_id'] = employee_find.id
                                hr_attendance_record['check_in'] = current_record['timestamp']

                                check_count = 1
                                previous_time = datetime.strptime(current_record['timestamp'], '%Y-%m-%d %H:%M:%S')
                            else: 
                                is_duplicate_record = False
                                
                                # Lấy thời gian record hiện tại 
                                current_time = datetime.strptime(current_record['timestamp'], '%Y-%m-%d %H:%M:%S')

                                #so sánh 2 giá trị gần nhau quá 15 phút là sẽ là duplitcate
                                time_difference_minutes = abs((current_time - previous_time).total_seconds() / 60)

                                #Lấy lại thời gian record trước
                                previous_time = datetime.strptime(current_record['timestamp'], '%Y-%m-%d %H:%M:%S')

                                if(time_difference_minutes < DUPLICATE_THRESHOLD_MINUTES): 
                                    is_duplicate_record = True

                                if(is_duplicate_record == True):
                                    time_gap = round(time_difference_minutes, 1)
                                    print(f"    ⏭️  DUPLICATE: {current_record['timestamp']} (cách {time_gap} phút)")
                                else:
                                    check_count +=1
                                    if(check_count % 2 == 1):
                                        print(f"    ✅ CHECKIN: {current_record['timestamp']}")
                                        checkin_str = current_record['timestamp']
                                        hr_attendance_record = {}
                                        hr_attendance_record['employee_id'] = employee_find.id
                                        hr_attendance_record['check_in'] = current_record['timestamp']
                                    else: 
                                        print(f"    🚪 CHECKOUT: {current_record['timestamp']}")
                                        hr_attendance_record['check_out'] = current_record['timestamp']
                                        hr_attendance_list.append(hr_attendance_record)
                                        # print(f" record: {hr_attendance_record}")

                        if check_count % 2 == 1: 
                            checkin = datetime.strptime(checkin_str, "%Y-%m-%d %H:%M:%S")
                            hr_attendance_record['check_out'] = datetime.combine(checkin.date(), time(23, 59, 59)).strftime("%Y-%m-%d %H:%M:%S")
                            hr_attendance_list.append(hr_attendance_record)
                            # print(f" record: {hr_attendance_record}")

                # Tạo message tóm tắt
                message = f"Số lượng nhân viên: chưa tính | Lần chấm công: chưa tính"
                
                for hr_record in hr_attendance_list: 
                    # Tạo record mới trong hr.attendance
                    
                    # Lấy timezone user
                    user_timezone = pytz.timezone(self.env.user.tz or 'UTC')
                    offset_hours = datetime.now(user_timezone).utcoffset().total_seconds() / 3600

                    # Chuyển thời gian thiết bị về UTC
                    check_in_record = datetime.strptime(hr_record['check_in'], '%Y-%m-%d %H:%M:%S')
                    check_out_record = datetime.strptime(hr_record['check_out'], '%Y-%m-%d %H:%M:%S')

                    check_in = check_in_record - timedelta(hours=offset_hours)
                    check_out = check_out_record - timedelta(hours=offset_hours)

                    # 🔍 KIỂM TRA DUPLICATE: Đã có dữ liệu chấm công trong ngày này chưa?
                    existing_attendance = self.env['hr.attendance'].search([
                        ('employee_id', '=', hr_record['employee_id']),
                        ('check_in', '=', check_in), 
                    ], limit=1)

                    if existing_attendance :
                        print(f"❌ Đã có thông tin chấm công user_id {hr_record['employee_id']} : {check_in_record}")
                        continue; 

                    attendance_record = self.env['hr.attendance'].create({
                        'employee_id': int(hr_record['employee_id']),
                        'check_in': check_in,
                        'check_out': check_out,
                    })
                    print(f"✅ đã cập nhật chấm công user_id {hr_record['employee_id']} : {check_in_record} - {check_out_record}")

                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '✅ Đồng bộ thành công',
                        'message': message,
                        'type': 'success',
                        'sticky': True,
                    }
                }
                
            finally:
                conn.disconnect()
                
        except ImportError:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '📦 Thiếu thư viện',
                    'message': 'Chưa cài đặt thư viện pyzk',
                    'type': 'warning',
                }
            }
            
        except Exception as e:
            error_traceback = traceback.format_exc()
            print(f"Lỗi đồng bộ: {str(e)}\n{error_traceback}")
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': '❌ Lỗi đồng bộ',
                    'message': f'Chi tiết: {str(e)}',
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    # ===== THÊM CÁC METHOD HỖ TRỢ =====
    def action_set_timezone(self):
        """Set timezone với thời gian chính xác"""
        try:
            from zk import ZK
            
            zk = ZK(self.ip_address, port=self.port or 4370, timeout=15)
            conn = zk.connect()
            
            if not conn:
                raise UserError(_("Cannot connect to device."))
            
            try:
                # Lấy thời gian thiết bị trước khi set
                device_time_before = conn.get_time()
                print(f"⏰ Device time BEFORE: {device_time_before}")
                
                # ✅ SỬA: Lấy đúng thời gian theo timezone
                user_tz = self.env.context.get('tz') or self.env.user.tz or 'Asia/Saigon'
                target_timezone = pytz.timezone(user_tz)
                
                # ✅ ĐÚNG: Lấy thời gian hiện tại theo timezone
                local_now = datetime.now(target_timezone)
                local_naive = local_now.replace(tzinfo=None)  # Remove timezone info for device
                
                print(f"🖥️ Server UTC: {datetime.now()}")  # Hiển thị để so sánh
                print(f"🌍 Local time ({user_tz}): {local_now}")
                print(f"📱 Setting to device: {local_naive}")
                
                # ✅ SỬA: Set đúng thời gian local
                try:
                    conn.set_time(local_naive)  # ✅ Set local time thay vì UTC
                    print("✅ Method: Set local time successfully")
                except Exception as e1:
                    print(f"❌ Set local time failed: {e1}")

                # Verify sau khi set
                device_time_after = conn.get_time()
                time_diff = (device_time_after - device_time_before).total_seconds() / 3600
                
                print(f"✅ Device time AFTER: {device_time_after}")
                print(f"📊 Time difference: {time_diff:.1f} hours")
                
                # ✅ SỬA: Update với thông tin chính xác
                self.write({
                    'device_info': f'Timezone: {user_tz} | '
                                f'Before: {device_time_before} | '
                                f'After: {device_time_after} | '
                                f'Difference: {time_diff:.1f}h | '
                                f'Local time set: {local_now}'  # ✅ Hiển thị thời gian thực tế set
                })
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': '✅ Set timezone thành công',
                        'message': f'Device time: {device_time_after}. Adjusted: {time_diff:.1f}h',
                        'type': 'success',
                    }
                }
            finally:
                conn.disconnect()
                
        except Exception as e:
            raise UserError(_(f"Error: {str(e)}"))

    def _find_employee_by_device_id(self, device_user_id):
        """Tìm employee dựa trên device_user_id """
        
        # Phương pháp 1: Tìm theo trcf_device_id_num
        employee = self.env['hr.employee'].search([
            ('trcf_device_id_num', '=', str(device_user_id))
        ], limit=1)
        if employee.exists():
            return employee
        
        # Phương pháp 2: Tìm theo ID trực tiếp
        employee = self.env['hr.employee'].browse(device_user_id)
        if employee.exists():
            return employee
        
        # Không tìm thấy
        return False
