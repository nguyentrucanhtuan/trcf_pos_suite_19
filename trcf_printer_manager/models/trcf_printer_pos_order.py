from odoo import models, fields, api
import logging
import socket
from datetime import datetime
from escpos.printer import Network
import unicodedata
import json

_logger = logging.getLogger(__name__)

class TrcfPrinterPosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def sync_from_ui(self, orders):
        result = super().sync_from_ui(orders)
        
        if result and 'pos.order' in result:
            for order_data in result['pos.order']:
                self._print_invoice_escpos(order_data)
                self._print_kitchen_order_ticket_escpos(order_data)
                self._print_label_tspl(order_data)
        return result

    @api.model
    def _print_invoice_escpos(self, order_data):
        """In hóa đơn cho khách"""

        # LẤY MÁY IN
        printer_search = self.env['trcf.printer.manager'].search([
            ('active', '=', True),
            ('printer_type', '=', 'invoice')
        ])

        if not printer_search:
            return False
        
        # LẤY THÔNG TIN CÔNG TY
        company = self.env.company
        company_name = company.name or "TÊN THƯƠNG HIỆU"
        company_address = company.street or "Địa chỉ công ty"
        
        # LẤY THÔNG TIN ĐƠN HÀNG
        order_id = order_data.get('id')
        table_id = order_data.get('table_id')

        date_order_utc = order_data.get('date_order')
        date_order_local = fields.Datetime.context_timestamp(self, date_order_utc)
        print_date_time = date_order_local.strftime('%d/%m/%Y %H:%M:%S') 

        # LẤY CHI TIẾT MÓN ĂN
        order = self.browse(order_id)
        #print("order", order.lines.read())

        # Lấy phần số cuối của mã đơn hàng
        order_number = order.pos_reference.split('-')[-1]

        for one_printer in printer_search: 
            printer_ip = one_printer.ip_address
            printer_port = one_printer.port
            invoice_footer_text = one_printer.invoice_footer_text or ""

            try: 
                printer = Network(printer_ip, printer_port, timeout=5)
                # IN HEADER
                printer.set(bold=True, width=2, height=2, align='center')
                printer.text(f"{self._convert_vi_to_unsigned(company_name)}\n")
                printer.set(bold=False, width=1, height=1, align='center')
                printer.text(f"{self._convert_vi_to_unsigned(company_address)}\n")
                printer.text("-" * 48 + "\n")
                
                # IN THÔNG TIN BÀN
                printer.set(bold=True, width=3, height=3, align='center')
                printer.text(f"BAN {order.table_id.display_name} - {order_number}\n")
                printer.set(bold=False, width=2, height=2, align='center')
                printer.text(f"THOI GIAN: {print_date_time}\n")
                printer.text("-" * 48 + "\n\n")
                
                # IN DANH SÁCH MÓN ĂN
                printer.set(bold=False, width=1, height=1, align='left')
                
                for line in order.lines:
                    # TÊN MÓN (dòng đầu)
                    printer.set(bold=True, width=1, height=1)
                    printer.text(f"{self._convert_vi_to_unsigned(line.full_product_name)}\n")
                    
                    # SỐ LƯỢNG x GIÁ = TỔNG (dòng thứ 2, căn phải)
                    printer.set(bold=False, width=1, height=1)
                    qty = int(line.qty) if line.qty == int(line.qty) else line.qty
                    price_unit = f"{line.price_unit:,.0f}"
                    price_subtotal = f"{(int(line.qty)*int(line.price_unit)):,.0f}"
                    
                    # Format: "  2 x 50,000 =          100,000"
                    detail_line = f"  {qty} x {price_unit}"
                    total_part = f"{price_subtotal}"
                    
                    # Tính toán khoảng cách để căn phải (giả sử màn hình 48 ký tự)
                    space_count = 48 - len(detail_line) - len(total_part)
                    full_line = detail_line + " " * space_count + total_part + "\n"
                    
                    printer.text(full_line)
                    printer.text("\n")  # Dòng trống giữa các món
                
                # TỔNG CỘNG
                printer.text("-" * 48 + "\n")
                printer.set(bold=True, width=1, height=1, align='left')
                
                # Tổng tiền (chưa thuế/phí)
                subtotal = f"{order.amount_total:,.0f}"
                printer.text(f"TAM TINH:" + " " * (48 - 9 - len(subtotal)) + subtotal + "\n")
                
                # Thuế (nếu có)
                # if order.amount_tax > 0:
                #     tax = f"{order.amount_tax:,.0f}"
                #     printer.text(f"THUE:" + " " * (48 - 5 - len(tax)) + tax + "\n")
                
                # Tổng thanh toán
                printer.set(bold=True, width=2, height=2)
                total_amount = f"{order.amount_total:,.0f}"
                printer.text(f"TONG CONG:" + " " * (48 - 10 - len(total_amount)) + total_amount + "\n")
                
                printer.text("-" * 48 + "\n")
                
                # PHƯƠNG THỨC THANH TOÁN
                printer.set(bold=False, width=1, height=1, align='left')
                printer.text("\nPHUONG THUC THANH TOAN:\n")
                
                for payment in order.payment_ids:
                    payment_method = self._convert_vi_to_unsigned(payment.payment_method_id.name)
                    payment_amount = f"{payment.amount:,.0f}"
                    
                    printer.set(bold=False, width=1, height=1)
                    payment_line = f"  {payment_method}:"
                    space_count = 48 - len(payment_line) - len(payment_amount)
                    full_payment_line = payment_line + " " * space_count + payment_amount + "\n"
                    printer.text(full_payment_line)
                
                # WIFI
                printer.text("\n")
                printer.set(bold=True, width=1, height=1, align='center')
                printer.text("-" * 48 + "\n")
                printer.text(self._convert_vi_to_unsigned(invoice_footer_text))
                printer.text("\n")
                printer.text("-" * 48 + "\n")
                printer.text("\n\n")
                printer.cut()
                printer.close()
            except Exception as e:
                print(f"✗ Lỗi in nhãn: {e}")
                continue
        return True

    @api.model
    def _print_label_tspl(self, order_data):
        
        # LẤY THÔNG TIN ĐƠN HÀNG TỪ ODOO
        order_id = order_data.get('id')
        table_id = order_data.get('table_id', False)
        order = self.browse(order_id)
        pos_preset_id = order.preset_id.id

        # Lấy mã đơn hàng
        order_code = order.pos_reference

        # Tính tổng số tem cần in (tổng tất cả số lượng)
        total_labels = sum(int(line.qty) for line in order.lines)
        
        # Lấy thời gian hiện tại
        # now = datetime.now()
        # datetime_str = now.strftime("%d.%m.%Y %H:%M:%S")

        date_order_utc = order_data.get('date_order')
        date_order_local = fields.Datetime.context_timestamp(self, date_order_utc)
        print_date_time = date_order_local.strftime('%d/%m/%Y %H:%M:%S')

        # Xử lý số bàn
        if table_id:
            table_name = order.table_id.display_name
        else:
            table_name = "MANG VE"

        # KẾT NỐI ĐẾN CÁC MÁY IN
        printer_search = self.env['trcf.printer.manager'].search([
            ('active', '=', True),
            ('printer_type', '=', 'label')
        ])

        for one_printer in printer_search:
            printer_ip = one_printer.ip_address
            printer_port = one_printer.port

            printer_label_pos_preset_ids = set(one_printer.printer_label_pos_preset_ids.ids)
            label_counter = 0

            # Thực hiện kiểm tra pos_preset_id của đơn hàng không có trong danh sách của máy in
            if pos_preset_id not in printer_label_pos_preset_ids:
                continue

            for line in order.lines:
                # Lấy thông tin món
                full_product_name = self._convert_vi_to_unsigned(line.full_product_name.upper())  # Chuyển thành chữ hoa
                
                # Xử lý ghi chú - format đẹp hơn
                note = ""
                if line.note:
                    note = line.note.upper()
                    # Giới hạn độ dài ghi chú để vừa tem (max 30 ký tự)
                    if len(note) > 30:
                        note = note[:27] + "..."
                
                # Format giá tiền VNĐ
                price = f"{line.price_unit:,.0f}".replace(",", ".")
                
                # Số lượng cần in
                quantity = int(line.qty)

                for qty_idx in range(1, quantity + 1):
                    label_counter += 1
                    # Tạo lệnh cho mỗi nhãn
                    commands = f"""SIZE 37 mm, 30 mm
                        GAP 2 mm, 0 mm
                        DIRECTION 1,0
                        CLS

                        TEXT 25,25,"2",0,1,1,"BAN {table_name} - ({label_counter}/{total_labels})"
                        TEXT 25,50,"0",0,1,1,"{order_code}"
                        BAR 25,85,276,1
                        TEXT 25,100,"2",0,1,1,"{full_product_name}"
                        TEXT 25,125,"0",0,1,1,"{note}"
                        BAR 25,160,276,1
                        TEXT 25,175,"0",0,1,1,"{price}"
                        TEXT 25,200,"0",0,1,1,"{print_date_time}"

                        PRINT 1,1
                        """
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(5)
                        sock.connect((printer_ip, printer_port))
                        sock.send(commands.encode('utf-8'))
                        sock.close()
                    except Exception as e:
                        print(f"✗ Lỗi in nhãn: {e}")

        return True

    @api.model
    def _print_kitchen_order_ticket_escpos(self, order_data):
        from escpos.printer import Network
        
        # LẤY THÔNG TIN ĐƠN HÀNG TỪ order_data
        order_id = order_data.get('id')
        table_id = order_data.get('table_id', False)
        
        # Lấy thông tin từ order record
        order = self.browse(order_id)
        
        # Lấy số hóa đơn
        order_number = order.pos_reference if order.pos_reference else f"HD{order_id}"
        
        # Lấy số thứ tự (có thể dùng id hoặc sequence number)
        sequence_number = str(order.id).zfill(2)  # Pad với 0 nếu cần

        date_order_utc = order_data.get('date_order')
        date_order_local = fields.Datetime.context_timestamp(self, date_order_utc)
        print_date_time = date_order_local.strftime('%d/%m/%Y %H:%M:%S')
        
        # KẾT NỐI MÁY IN BẾP
        printer_search = self.env['trcf.printer.manager'].search([
            ('active', '=', True),
            ('printer_type', '=', 'kitchen_order_ticket')
        ])

        if not printer_search:
            _logger.warning("Không tìm thấy máy in bếp được cấu hình")
            return False 
        
        for one_printer in printer_search:
            printer_ip = one_printer.ip_address
            printer_port = one_printer.port

            # Lấy danh sách các ID của danh mục sản phẩm được cấu hình cho máy in
            printer_category_ids = one_printer.printer_kot_pos_category_ids.ids

            # Tạo một danh sách các món ăn cần in
            lines_to_print = []
            for line in order.lines:
                # Kiểm tra xem danh mục của món ăn có nằm trong danh mục của máy in không
                if line.product_id.pos_categ_ids.id in printer_category_ids:
                    lines_to_print.append(line)

            # Nếu không có món nào cần in, kết thúc hàm
            if not lines_to_print:
                _logger.info(f"Không có món ăn thuộc danh mục in phiếu bếp cho đơn hàng {order_number}")
                continue 
            
            try:
                printer = Network(printer_ip, printer_port, timeout=5)
                
                # IN DÒNG 1: Bàn X - Mã hóa đơn
                printer.set(bold=True, width=2, height=2, align='center')

                if table_id:
                    table_name = f"BAN {order.table_id.display_name}"
                else:
                    table_name = "MANG VE"

                printer.text(f"{table_name} - {order_number}\n")
                
                # IN DÒNG 2: Ngày giờ - số thứ tự
                printer.set(bold=False, width=1, height=1, align='center')
                printer.text(f"{print_date_time} - {sequence_number}\n")
                printer.text("-" * 48 + "\n")
                
                # IN DANH SÁCH MÓN
                printer.set(bold=True, width=1, height=1, align='left')
                
                for line in lines_to_print:
                    # Lấy tên món
                    full_product_name = self._convert_vi_to_unsigned(line.full_product_name)
                    
                    # Lấy số lượng (format số nguyên nếu không có phần thập phân)
                    qty = int(line.qty) if line.qty == int(line.qty) else line.qty
                    
                    # Xử lý ghi chú - kiểm tra trước khi parse JSON
                    notes_list = []
                    if line.note and line.note.strip():
                        try:
                            notes_list = json.loads(line.note)
                        except (json.JSONDecodeError, ValueError):
                            _logger.warning(f"Không thể parse ghi chú JSON cho món {full_product_name}: {line.note}")
                    
                    # Thêm ghi chú vào tên món nếu có
                    if notes_list and len(notes_list) > 0 and 'text' in notes_list[0]:
                        product_display = f"{full_product_name} ({self._convert_vi_to_unsigned(notes_list[0]['text'])})"
                    else:
                        product_display = full_product_name
                    
                    # In theo format: Tên món x số lượng
                    printer.text(f"{product_display} x {qty}\n")
                
                # Cắt giấy
                printer.text("\n\n")
                printer.cut()
                printer.close()
                _logger.info(f"Đã in phiếu bếp cho đơn hàng {order_number}")
                
            except Exception as e:
                _logger.error(f"Lỗi khi in phiếu yêu cầu bếp: {str(e)}")

    def _convert_vi_to_unsigned(self, text):
        """
        Chuyển đổi chuỗi tiếng Việt có dấu thành không dấu.
        Ví dụ: "Cà phê sữa đá" -> "Ca phe sua da"
        """

        # Bước 1: Thay thế 'Đ' và 'đ' trước khi chuẩn hóa Unicode
        text = text.replace('Đ', 'D').replace('đ', 'd')

        # Bước 2: Chuẩn hóa chuỗi Unicode (NFD - Normalization Form D)
        # Tách các ký tự có dấu thành ký tự cơ bản và dấu thanh riêng biệt.
        normalized_text = unicodedata.normalize('NFD', text)
        
        # Bước 3: Lọc bỏ các ký tự dấu (combining characters)
        unsigned_text = "".join([c for c in normalized_text if unicodedata.category(c) != 'Mn'])
        
        return unsigned_text