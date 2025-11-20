import pytz
from datetime import datetime, time, timedelta
from odoo import http
from odoo.http import request

class TrcfFnbInventory(http.Controller):

    @http.route('/trcf_fnb_inventory/daily_report', type='http', auth='user', website=False)
    def daily_report(self, filter_type='today', date_from=None, date_to=None, **kw):

        # --- BƯỚC 1: LẤY TIMEZONE CỦA USER ---
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        # Lấy thời gian hiện tại theo giờ của User (Ví dụ: GMT+7)
        now_user_tz = datetime.now(user_tz)
        today = now_user_tz.date()

        # --- BƯỚC 2: XÁC ĐỊNH KHOẢNG THỜI GIAN (USER TIME) ---
        if filter_type == 'today':
            current_start = today
            current_end = today
        elif filter_type == 'week':
            current_start = today - timedelta(days=today.weekday())
            current_end = today
        elif filter_type == 'month':
            current_start = today.replace(day=1)
            current_end = today
        elif filter_type == 'custom' and date_from and date_to:
            current_start = datetime.strptime(date_from, '%Y-%m-%d').date()
            current_end = datetime.strptime(date_to, '%Y-%m-%d').date()
        else:
            filter_type = 'today'
            current_start = today
            current_end = today

        # Lấy dữ liệu kỳ hiện tại
        total_pos_revenue = self.get_pos_revenue(current_start, current_end)
        total_orders = self.get_pos_order_count(current_start, current_end)
        total_qty = self.get_pos_order_qty(current_start, current_end)
        payment_methods = self.get_payment_method_revenue(current_start, current_end)
        revenue_by_presets = self.get_revenue_by_preset(current_start, current_end)

        # Lấy dữ liệu kỳ trước để so sánh
        previous_start, previous_end = self.get_previous_period(filter_type, current_start, current_end)
        previous_revenue = self.get_pos_revenue(previous_start, previous_end)
        previous_orders = self.get_pos_order_count(previous_start, previous_end)
        previous_qty = self.get_pos_order_qty(previous_start, previous_end)

        # Tính % thay đổi
        revenue_comparison = self.calculate_comparison(total_pos_revenue, previous_revenue)
        orders_comparison = self.calculate_comparison(total_orders, previous_orders)
        qty_comparison = self.calculate_comparison(total_qty, previous_qty)

        # Xác định text so sánh
        comparison_text = {
            'today': 'so với hôm qua',
            'week': 'so với tuần trước',
            'month': 'so với tháng trước',
            'custom': 'so với kỳ trước'
        }.get(filter_type, 'so với kỳ trước')

        # 1. Lấy tiền tệ của công ty hiện tại (VND, USD, EUR...)
        currency = request.env.company.currency_id
        # 2. Sử dụng hàm format có sẵn của Odoo
        formatted_total_revenue = currency.format(total_pos_revenue)

        vals = {
            'filter_type': filter_type,
            'date_from': date_from,
            'date_to': date_to,
            'total_pos_revenue': formatted_total_revenue,
            'total_orders': total_orders,
            'total_qty': total_qty,
            'payment_methods': payment_methods,
            'revenue_by_presets': revenue_by_presets,
            'revenue_comparison': revenue_comparison,
            'orders_comparison': orders_comparison,
            'qty_comparison': qty_comparison,
            'comparison_text': comparison_text,
        }

        return request.render('trcf_fnb_inventory.daily_report_template', vals)

    def get_previous_period(self, filter_type, current_start, current_end):
        """Tính toán khoảng thời gian trước đó để so sánh"""
        if filter_type == 'today':
            # Hôm qua
            previous_start = current_start - timedelta(days=1)
            previous_end = current_end - timedelta(days=1)
        elif filter_type == 'week':
            # Tuần trước (cùng 7 ngày)
            previous_start = current_start - timedelta(days=7)
            previous_end = current_end - timedelta(days=7)
        elif filter_type == 'month':
            # Tháng trước (cùng khoảng thời gian)
            days_diff = (current_end - current_start).days
            previous_end = current_start - timedelta(days=1)
            previous_start = previous_end - timedelta(days=days_diff)
        else:
            # Mặc định: ngày hôm qua
            previous_start = current_start - timedelta(days=1)
            previous_end = current_end - timedelta(days=1)
        
        return previous_start, previous_end

    def calculate_comparison(self, current, previous):
        """Tính % thay đổi so với kỳ trước"""
        if previous == 0:
            if current > 0:
                return {'percentage': 100, 'trend': 'up', 'sign': '+', 'formatted': '+100.0%'}
            else:
                return {'percentage': 0, 'trend': 'neutral', 'sign': '', 'formatted': '0.0%'}
        
        change = ((current - previous) / previous) * 100
        trend = 'up' if change > 0 else 'down' if change < 0 else 'neutral'
        
        return {
            'percentage': abs(change),
            'trend': trend,
            'sign': '+' if change > 0 else '-' if change < 0 else '',
            'formatted': f"{'+' if change > 0 else ''}{change:.1f}%"
        }

    @http.route('/trcf_fnb_inventory/expense_list', type='http', auth='user', website=False)
    def expense_list(self, **kw):

        # today = date.today()
        expenses = []

        # Lấy các báo cáo chi phí từ hr.expense trong ngày hiện tại
        hr_expenses = request.env['hr.expense'].sudo().search([
            # ('date', '=', today),
            # ('state', 'in', ['approved', 'done']), 
        ])

        for expense in hr_expenses:
            expenses.append({
                'id': expense.id,
                'expense_type': expense.product_id.name if expense.product_id else 'N/A', # Tên sản phẩm/dịch vụ
                'expense_name': expense.name, # Tên của báo cáo chi phí
                'expense_date': expense.date, # Ngày của chi phí
                'expense_total_amount': expense.total_amount, # Tổng số tiền
                'expense_currency': expense.currency_id.symbol if expense.currency_id else '', # Ký hiệu tiền tệ
                'expense_employee': expense.employee_id.name if expense.employee_id else 'N/A', # Tên nhân viên
            })

        # Truyền dữ liệu chi phí vào template
        return request.render('trcf_fnb_inventory.expense_list_template', {
            'total_expenses': expenses,
            # 'today': today.strftime('%d/%m/%Y')
        })

    @http.route('/trcf_fnb_inventory/expense_add', type='http', auth='user', website=False, methods=['GET', 'POST'])
    def expense_add(self, **kw):
        success_message = False
        error_message = False

        if request.httprequest.method == 'POST':
            try:
                # Lấy thông tin từ form
                expense_type = int(request.params.get('expense_type'))
                expense_name = request.params.get('expense_name')
                expense_amount = float(request.params.get('expense_amount'))
                payment_method = request.params.get('payment_method')
                #employee_id = int(post.post('employee_id')) if post.post('employee_id') else False

                # Tạo phiếu chi mới
                expense = request.env['hr.expense'].sudo().create({
                    'name': expense_name,
                    'product_id': expense_type,
                    'product_uom_id': 1,
                    'company_id': 1,
                    'total_amount_currency': expense_amount,
                    'quantity': 1,
                    'employee_id': 1,
                    'payment_mode': 'company_account',
                    'currency_id' : 23,
                    'state' : 'draft',
                    'payment_method_line_id': 2
                })

                success_message = "Phiếu chi đã được tạo thành công!"
                return request.redirect('/trcf_fnb_inventory/expense_list?success=1')

            except Exception as e:
                error_message = f"Đã có lỗi xảy ra: {e}"
                print("error_message", error_message)

        return request.render('trcf_fnb_inventory.expense_form_template')

    def get_pos_revenue(self, start_date, end_date):
        # 1. Setup Timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        dt_start = datetime.combine(start_date, time.min)
        dt_end = datetime.combine(end_date, time.max)
        
        # 2. XỬ LÝ LỖI "Use naive datetimes":
        # Bước 1: Localize (gán múi giờ User) -> Bước 2: Đổi sang UTC -> Bước 3: Xóa info timezone (.replace(tzinfo=None))
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)

        domain = [
            ('date_order', '>=', dt_start_utc),
            ('date_order', '<=', dt_end_utc),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]

        # 3. XỬ LÝ LỖI "read_group is deprecated":
        # Sử dụng _read_group (có dấu gạch dưới). Hàm này trả về list các tuple.
        # aggregates=['amount_total:sum'] -> Tính tổng trường amount_total
        result = request.env['pos.order']._read_group(
            domain=domain,
            aggregates=['amount_total:sum']
        )
        
        # Kết quả trả về dạng: [(Tổng_tiền,)]
        # result[0] là tuple đầu tiên, result[0][0] là giá trị sum.
        # Nếu không có đơn hàng nào, nó có thể trả về None, nên dùng (or 0)
        return result[0][0] or 0

    def get_pos_order_count(self, start_date, end_date):
        # 1. Setup Timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        dt_start = datetime.combine(start_date, time.min)
        dt_end = datetime.combine(end_date, time.max)
        
        # 2. XỬ LÝ LỖI "Use naive datetimes":
        # Bước 1: Localize (gán múi giờ User) -> Bước 2: Đổi sang UTC -> Bước 3: Xóa info timezone (.replace(tzinfo=None))
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)

        domain = [
            ('date_order', '>=', dt_start_utc),
            ('date_order', '<=', dt_end_utc),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]

        # Tính tổng số đơn hàng
        total_orders = request.env['pos.order'].search_count(domain)
        
        return total_orders

    def get_pos_order_qty(self, start_date, end_date):
        # 1. Setup Timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        dt_start = datetime.combine(start_date, time.min)
        dt_end = datetime.combine(end_date, time.max)
        
        # 2. XỬ LÝ LỖI "Use naive datetimes":
        # Bước 1: Localize (gán múi giờ User) -> Bước 2: Đổi sang UTC -> Bước 3: Xóa info timezone (.replace(tzinfo=None))
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)

        domain = [
            ('date_order', '>=', dt_start_utc),
            ('date_order', '<=', dt_end_utc),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]
        
        # Tìm tất cả các order trong domain
        order_ids = request.env['pos.order'].search(domain).ids
        
        if not order_ids:
            return 0
            
        # Tính tổng số lượng sản phẩm bán ra từ pos.order.line
        domain_lines = [('order_id', 'in', order_ids)]
        
        result_lines = request.env['pos.order.line']._read_group(
            domain=domain_lines,
            aggregates=['qty:sum']
        )
        
        total_qty = result_lines[0][0] or 0
        
        return total_qty

    def get_payment_method_revenue(self, start_date, end_date):
        """Lấy doanh thu theo từng phương thức thanh toán"""
        # 1. Setup Timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        dt_start = datetime.combine(start_date, time.min)
        dt_end = datetime.combine(end_date, time.max)
        
        # 2. Convert to UTC
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)

        # 3. Lấy tất cả các đơn hàng trong khoảng thời gian
        domain_orders = [
            ('date_order', '>=', dt_start_utc),
            ('date_order', '<=', dt_end_utc),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]
        
        order_ids = request.env['pos.order'].search(domain_orders).ids
        
        if not order_ids:
            return []
        
        # 4. Lấy tất cả các payment của các đơn hàng này
        domain_payments = [('pos_order_id', 'in', order_ids)]
        
        # 5. Group by payment_method_id và tính tổng amount
        result = request.env['pos.payment']._read_group(
            domain=domain_payments,
            groupby=['payment_method_id'],
            aggregates=['amount:sum']
        )
        
        # 6. Format kết quả
        currency = request.env.company.currency_id
        payment_methods = []
        
        # Định nghĩa màu sắc cho các phương thức thanh toán
        colors = ['cyan-500', 'violet-500', 'amber-500', 'green-500', 'blue-500', 'pink-500', 'indigo-500', 'red-500']
        
        for idx, (payment_method, amount_sum) in enumerate(result):
            if payment_method:  # Bỏ qua nếu payment_method là False/None
                payment_methods.append({
                    'name': payment_method.name,
                    'amount': amount_sum or 0,
                    'formatted_amount': currency.format(amount_sum or 0),
                    'color': colors[idx % len(colors)]  # Lấy màu theo vòng lặp
                })
        
        return payment_methods

    def get_revenue_by_preset(self, start_date, end_date):
        """Phân loại đơn hàng theo preset (tại chỗ, mang về, delivery platforms)"""
        # 1. Setup Timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        dt_start = datetime.combine(start_date, time.min)
        dt_end = datetime.combine(end_date, time.max)
        
        # 2. Convert to UTC
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)

        # 3. Lấy tất cả các đơn hàng trong khoảng thời gian
        domain = [
            ('date_order', '>=', dt_start_utc),
            ('date_order', '<=', dt_end_utc),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]
        
        # 4. Group by preset_id, đếm số đơn và tính tổng doanh thu
        result = request.env['pos.order']._read_group(
            domain=domain,
            groupby=['preset_id'],
            aggregates=['__count', 'amount_total:sum']
        )
        
        # 5. Format kết quả
        currency = request.env.company.currency_id
        order_presets = []
        
        # Định nghĩa màu sắc cho các preset
        colors = ['green-500', 'blue-500', 'orange-500', 'purple-500', 'pink-500', 'indigo-500', 'red-500', 'yellow-500']
        
        for idx, (preset, count, revenue) in enumerate(result):
            if preset:  # Bỏ qua nếu preset là False/None
                order_presets.append({
                    'name': preset.name,
                    'count': count or 0,
                    'revenue': revenue or 0,
                    'formatted_revenue': currency.format(revenue or 0),
                    'color': colors[idx % len(colors)]  # Lấy màu theo vòng lặp
                })
        
        return order_presets