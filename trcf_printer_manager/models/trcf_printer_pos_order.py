from odoo import models, fields, api
import logging
import json
import socket
from datetime import datetime

_logger = logging.getLogger(__name__)

class TrcfPrinterPosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def sync_from_ui(self, orders):
        # Odoo 18 dùng sync_from_ui thay vì create_from_ui
        result = super().sync_from_ui(orders)
                
        # Lặp qua từng order và in
        if result and 'pos.order' in result:
            for order_data in result['pos.order']:
                self._print_invoice_escpos(order_data)
                self._print_kitchen_order_ticket_escpos(order_data)
                self._print_label_tspl(order_data)

        return result

    @api.model
    def _print_invoice_escpos(self, order_data):
        from escpos.printer import Network
        
        # LẤY THÔNG TIN CÔNG TY
        company = self.env.company
        company_name = company.name or "TÊN THƯƠNG HIỆU"
        company_address = company.street or "Địa chỉ công ty"
        
        # LẤY THÔNG TIN ĐƠN HÀNG
        order_id = order_data.get('id')
        table_id = order_data.get('table_id')
        date_order = order_data.get('date_order')
        
        # LẤY CHI TIẾT MÓN ĂN
        order = self.browse(order_id)

        # Lấy phần số cuối của mã đơn hàng
        order_number = order.pos_reference.split('-')[-1]
        
        # KẾT NỐI MÁY IN
        printer_search = self.env['trcf.printer.manager'].search([
            ('active', '=', True),
            ('printer_type', '=', 'invoice')
        ], limit=1)

        if printer_search:
            printer = Network(printer_search.ip_address, printer_search.port)
        else: 
            return False

        # IN TIÊU ĐỀ - TÊN THƯƠNG HIỆU
        printer.set(bold=True, width=2, height=2, align='center')
        printer.text(f"{company_name}\n")
        
        # IN ĐỊA CHỈ
        printer.set(bold=False, width=1, height=1, align='center')
        printer.text(f"{company_address}\n")
        printer.text("-" * 48 + "\n")
        
        # IN BÀN
        printer.set(bold=True, width=3, height=3, align='center')
        printer.text(f"BAN {table_id} - {order_number}\n")
        
        # IN THỜI GIAN
        printer.set(bold=False, width=2, height=2, align='center')
        printer.text(f"THOI GIAN: {date_order}\n")
        printer.text("-" * 48 + "\n\n")
        
        # IN DANH SÁCH MÓN ĂN
        printer.set(bold=False, width=1, height=1, align='left')
        
        for line in order.lines:
            # TÊN MÓN (dòng đầu)
            printer.set(bold=True, width=1, height=1)
            printer.text(f"{line.product_id.name}\n")
            
            # SỐ LƯỢNG x GIÁ = TỔNG (dòng thứ 2, căn phải)
            printer.set(bold=False, width=1, height=1)
            qty = int(line.qty) if line.qty == int(line.qty) else line.qty
            price_unit = f"{line.price_unit:,.0f}"
            price_subtotal = f"{line.price_subtotal:,.0f}"
            
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
        if order.amount_tax > 0:
            tax = f"{order.amount_tax:,.0f}"
            printer.text(f"THUE:" + " " * (48 - 5 - len(tax)) + tax + "\n")
        
        # Tổng thanh toán
        printer.set(bold=True, width=2, height=2)
        total_amount = f"{order.amount_total:,.0f}"
        printer.text(f"TONG CONG:" + " " * (48 - 10 - len(total_amount)) + total_amount + "\n")
        
        printer.text("-" * 48 + "\n")
        
        # PHƯƠNG THỨC THANH TOÁN
        printer.set(bold=False, width=1, height=1, align='left')
        printer.text("\nPHUONG THUC THANH TOAN:\n")
        
        for payment in order.payment_ids:
            payment_method = payment.payment_method_id.name
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
        printer.text("WIFI: CoffeeTree Roastery\n")
        printer.text("coffeetree123@\n")
        printer.text("-" * 48 + "\n")
        
        printer.text("\n\n")
        printer.cut()
        printer.close()
        
        return True

    @api.model
    def _print_label_tspl(self, order_data):
        
        # KẾT NỐI MÁY IN
        printer_search = self.env['trcf.printer.manager'].search([
            ('active', '=', True),
            ('printer_type', '=', 'label')
        ], limit=1)

        if printer_search:
            printer_ip = printer_search.ip_address
            printer_port = printer_search.port
        else: 
            return False

        # LẤY THÔNG TIN ĐƠN HÀNG TỪ ODOO
        order_id = order_data.get('id')
        table_id = order_data.get('table_id', False)
        order = self.browse(order_id)

        pos_preset_id = order.preset_id.id
        printer_label_pos_preset_ids = set(printer_search.printer_label_pos_preset_ids.ids)

        # Thực hiện kiểm tra pos_preset_id của đơn hàng không có trong danh sách của máy in
        if pos_preset_id not in printer_label_pos_preset_ids:
            return False

        # Xử lý số bàn
        if table_id:
            # table_id có thể là tuple (id, name) hoặc chỉ là id
            if isinstance(table_id, (list, tuple)):
                table_name = str(table_id[1])  # Lấy tên bàn
            else:
                table_name = str(table_id)
        else:
            table_name = "MANG VE"

        # Lấy mã đơn hàng
        order_code = order.pos_reference

        # Tính tổng số tem cần in (tổng tất cả số lượng)
        total_labels = sum(int(line.qty) for line in order.lines)
        label_counter = 0

        # Lấy thời gian hiện tại
        now = datetime.now()
        datetime_str = now.strftime("%d.%m.%Y %H:%M:%S")

        for line in order.lines:
            # Lấy thông tin món
            product_name = line.product_id.name.upper()  # Chuyển thành chữ hoa
            
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
                    TEXT 25,100,"2",0,1,1,"{product_name}"
                    TEXT 25,125,"0",0,1,1,"{note}"
                    BAR 25,160,276,1
                    TEXT 25,175,"0",0,1,1,"{price}"
                    TEXT 25,200,"0",0,1,1,"{datetime_str}"

                    PRINT 1,1
                    """
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
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
        
        # Format ngày giờ
        if order.date_order:
            from datetime import datetime
            try:
                dt = order.date_order
                if isinstance(dt, str):
                    dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                date_str = dt.strftime("%d-%m-%Y")
            except:
                date_str = datetime.now().strftime("%d-%m-%Y")
        else:
            date_str = datetime.now().strftime("%d-%m-%Y")
        
        # KẾT NỐI MÁY IN BẾP
        printer_search = self.env['trcf.printer.manager'].search([
            ('active', '=', True),
            ('printer_type', '=', 'kitchen_order_ticket')
        ], limit=1)

        if not printer_search:
            _logger.warning("Không tìm thấy máy in bếp được cấu hình")
            return False

        # Lấy danh sách các ID của danh mục sản phẩm được cấu hình cho máy in
        printer_category_ids = printer_search.printer_kot_pos_category_ids.ids

        # Tạo một danh sách các món ăn cần in
        lines_to_print = []
        for line in order.lines:
            # Kiểm tra xem danh mục của món ăn có nằm trong danh mục của máy in không
            if line.product_id.pos_categ_ids.id in printer_category_ids:
                lines_to_print.append(line)

        # Nếu không có món nào cần in, kết thúc hàm
        if not lines_to_print:
            _logger.info(f"Không có món ăn thuộc danh mục in phiếu bếp cho đơn hàng {order_number}")
            return False
            
        try:
            printer = Network(printer_search.ip_address, printer_search.port)
            
            # IN DÒNG 1: Bàn X - Mã hóa đơn
            printer.set(bold=True, width=2, height=2, align='center')
            if table_id:
                table_name = f"Ban {table_id[1]}" if isinstance(table_id, (list, tuple)) else f"Ban {table_id}"
            else:
                table_name = "Mang ve"
            printer.text(f"{table_name} - {order_number}\n")
            
            # IN DÒNG 2: Ngày giờ - số thứ tự
            printer.set(bold=False, width=1, height=1, align='center')
            printer.text(f"{date_str} - {sequence_number}\n")
            printer.text("-" * 48 + "\n")
            
            # IN DANH SÁCH MÓN
            printer.set(bold=True, width=1, height=1, align='left')
            
            for line in lines_to_print:
                # Lấy tên món
                product_name = line.product_id.name
                
                # Lấy số lượng (format số nguyên nếu không có phần thập phân)
                qty = int(line.qty) if line.qty == int(line.qty) else line.qty
                
                # Thêm ghi chú vào tên món nếu có
                if line.note:
                    product_display = f"{product_name} ({line.note})"
                else:
                    product_display = product_name
                
                # In theo format: Tên món x số lượng
                printer.text(f"{product_display} x {qty}\n")
            
            # Cắt giấy
            printer.text("\n\n")
            printer.cut()
            printer.close()
            
            _logger.info(f"Đã in phiếu bếp cho đơn hàng {order_number}")
            return True
            
        except Exception as e:
            _logger.error(f"Lỗi khi in phiếu yêu cầu bếp: {str(e)}")
            return False