import pytz
from datetime import datetime, time, timedelta
from odoo import http
from odoo.http import request

class TrcfReportController(http.Controller):

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

        # Lấy thống kê chi phí và nhập hàng
        expense_stats = self.get_expense_stats(current_start, current_end)
        purchase_stats = self.get_purchase_stats(current_start, current_end)
        
        # Tính tiền mặt trong két
        cash_balance = self.calculate_cash_balance(payment_methods, expense_stats, purchase_stats)
        
        # Lấy chi tiết các phiên bán hàng
        sessions = self.get_session_details(current_start, current_end)
        
        # Lấy tổng kết từ đầu ngày đến hiện tại
        day_summary = self.get_day_summary(current_start, current_end)
        
        # Lấy báo cáo phiên đang mở
        open_sessions = self.get_open_session_summary(current_start, current_end)
        
        # Tổng hợp tất cả bất thường từ các phiên
        all_anomalies = []
        
        # Thu thập split payment orders từ open sessions
        for session in (open_sessions or []):
            for item in session.get('split_payment_orders', []):
                if item.get('type') == 'discount':
                    all_anomalies.append({
                        'type': 'discount',
                        'session_name': session['name'],
                        'order_name': item['order_name'],
                        'product_name': item['product_name'],
                        'discount_percent': item['discount_percent'],
                        'original_price': item['original_price'],
                        'final_price': item['final_price'],
                        'qty': item['qty'],
                        'severity': 'info',
                    })
                else:
                    all_anomalies.append({
                        'type': 'split_payment',
                        'session_name': session['name'],
                        'order_name': item['name'],
                        'payment_count': item['payment_count'],
                        'payment_methods': item['payment_methods'],
                        'amount': item['amount'],
                        'severity': 'warning',
                    })
        
        # Thu thập split payment orders từ closed sessions
        for session in (sessions or []):
            for item in session.get('split_payment_orders', []):
                if item.get('type') == 'discount':
                    all_anomalies.append({
                        'type': 'discount',
                        'session_name': session['name'],
                        'order_name': item['order_name'],
                        'product_name': item['product_name'],
                        'discount_percent': item['discount_percent'],
                        'original_price': item['original_price'],
                        'final_price': item['final_price'],
                        'qty': item['qty'],
                        'severity': 'info',
                    })
                else:
                    all_anomalies.append({
                        'type': 'split_payment',
                        'session_name': session['name'],
                        'order_name': item['name'],
                        'payment_count': item['payment_count'],
                        'payment_methods': item['payment_methods'],
                        'amount': item['amount'],
                        'severity': 'warning',
                    })
        
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
            'cash_balance': cash_balance['formatted'],
            'cash_balance_detail': cash_balance['detail'],
            'sessions': sessions,
            'day_summary': day_summary,
            'open_sessions': open_sessions,
            'anomalies': all_anomalies,
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
                # Đếm số đơn duy nhất cho payment method này
                payments = request.env['pos.payment'].sudo().search([
                    ('pos_order_id', 'in', order_ids),
                    ('payment_method_id', '=', payment_method.id)
                ])
                order_count = len(set(payments.mapped('pos_order_id').ids))
                
                payment_methods.append({
                    'name': payment_method.name,
                    'amount': amount_sum or 0,
                    'formatted_amount': currency.format(amount_sum or 0),
                    'count': order_count,
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

    def get_expense_stats(self, start_date, end_date):
        """Lấy thống kê chi phí theo phương thức thanh toán"""
        # 1. Setup Timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        dt_start = datetime.combine(start_date, time.min)
        dt_end = datetime.combine(end_date, time.max)
        
        # 2. Convert to UTC
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)

        # 3. Lấy tất cả chi phí đã thanh toán trong khoảng thời gian
        domain = [
            ('trcf_payment_date', '>=', dt_start_utc),
            ('trcf_payment_date', '<=', dt_end_utc),
            ('state', '=', 'paid'),  # Chỉ lấy chi phí đã thanh toán
        ]
        
        expenses = request.env['trcf.expense'].sudo().search(domain)
        
        # 4. Tính tổng và nhóm theo payment method
        total_amount = 0
        payment_method_stats = {}
        
        for expense in expenses:
            total_amount += expense.trcf_amount
            
            pm_name = expense.trcf_payment_method_id.name if expense.trcf_payment_method_id else 'N/A'
            if pm_name not in payment_method_stats:
                payment_method_stats[pm_name] = 0
            payment_method_stats[pm_name] += expense.trcf_amount
        
        # 5. Format kết quả
        currency = request.env.company.currency_id
        payment_method_list = []
        
        for pm, amount in payment_method_stats.items():
            payment_method_list.append({
                'name': pm,
                'amount': amount,
                'formatted_amount': currency.format(amount)
            })
        
        return {
            'total': total_amount,
            'total_formatted': currency.format(total_amount),
            'by_payment_method': payment_method_list
        }

    def get_purchase_stats(self, start_date, end_date):
        """Lấy thống kê nhập hàng theo phương thức thanh toán"""
        # 1. Setup Timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        dt_start = datetime.combine(start_date, time.min)
        dt_end = datetime.combine(end_date, time.max)
        
        # 2. Convert to UTC
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)

        # 3. Lấy tất cả purchase orders đã thanh toán trong khoảng thời gian
        domain = [
            ('date_order', '>=', dt_start_utc),
            ('date_order', '<=', dt_end_utc),
            ('state', 'in', ['purchase', 'done']),  # Chỉ lấy đơn đã xác nhận
            ('trcf_payment_status', '=', 'paid'),  # Chỉ lấy đơn đã thanh toán
        ]
        
        purchases = request.env['purchase.order'].sudo().search(domain)
        
        # 4. Tính tổng và nhóm theo payment method
        total_amount = 0
        payment_method_stats = {}
        
        for purchase in purchases:
            total_amount += purchase.amount_total
            
            pm_name = purchase.trcf_payment_method_id.name if purchase.trcf_payment_method_id else 'N/A'
            if pm_name not in payment_method_stats:
                payment_method_stats[pm_name] = 0
            payment_method_stats[pm_name] += purchase.amount_total
        
        # 5. Format kết quả
        currency = request.env.company.currency_id
        payment_method_list = []
        
        for pm, amount in payment_method_stats.items():
            payment_method_list.append({
                'name': pm,
                'amount': amount,
                'formatted_amount': currency.format(amount)
            })
        
        return {
            'total': total_amount,
            'total_formatted': currency.format(total_amount),
            'by_payment_method': payment_method_list
        }
    def calculate_cash_balance(self, payment_methods, expense_stats, purchase_stats):
        """Tính tiền mặt trong két = Tiền mặt POS - Tiền mặt chi phí - Tiền mặt mua hàng"""
        currency = request.env.company.currency_id
        
        # 1. Tìm tiền mặt từ POS (payment methods)
        cash_from_pos = 0
        for pm in payment_methods:
            # Kiểm tra nếu là tiền mặt (Cash, Tiền mặt, etc.)
            if pm['name'].lower() in ['cash', 'tiền mặt', 'tien mat']:
                cash_from_pos = pm['amount']
                break
        
        # 2. Tìm tiền mặt chi phí
        cash_expense = 0
        for exp_pm in expense_stats['by_payment_method']:
            if exp_pm['name'].lower() in ['cash', 'tiền mặt', 'tien mat']:
                cash_expense = exp_pm['amount']
                break
        
        # 3. Tìm tiền mặt mua hàng
        cash_purchase = 0
        for pur_pm in purchase_stats['by_payment_method']:
            if pur_pm['name'].lower() in ['cash', 'tiền mặt', 'tien mat']:
                cash_purchase = pur_pm['amount']
                break
        
        # 4. Tính số dư
        balance = cash_from_pos - cash_expense - cash_purchase
        
        return {
            'amount': balance,
            'formatted': currency.format(balance),
            'detail': {
                'pos_cash': cash_from_pos,
                'pos_cash_formatted': currency.format(cash_from_pos),
                'expense_cash': cash_expense,
                'expense_cash_formatted': currency.format(cash_expense),
                'purchase_cash': cash_purchase,
                'purchase_cash_formatted': currency.format(cash_purchase),
            }
        }

    def get_day_summary(self, start_date, end_date):
        """Lấy tổng kết từ đầu ngày đến hiện tại, lấy theo đơn hàng pos.order"""
        # 1. Setup Timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        # Lấy thời gian hiện tại
        now_user_tz = datetime.now(user_tz)
        
        # Nếu end_date là hôm nay, thì lấy từ đầu ngày đến hiện tại
        # Nếu không, lấy cả ngày
        dt_start = datetime.combine(start_date, time.min)
        if end_date == now_user_tz.date():
            # dt_end đã có timezone từ now_user_tz
            dt_end = now_user_tz  # Lưu để format thời gian sau
            dt_end_utc = now_user_tz.astimezone(pytz.utc).replace(tzinfo=None)
        else:
            # dt_end chưa có timezone, cần localize
            dt_end = datetime.combine(end_date, time.max)
            dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)
        
        # 2. Convert dt_start to UTC
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)

        # 3. Lấy tất cả các đơn hàng trong khoảng thời gian
        domain_orders = [
            ('date_order', '>=', dt_start_utc),
            ('date_order', '<=', dt_end_utc),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ]
        
        # Đếm tổng số đơn hàng (dùng search_count như get_pos_order_count)
        total_orders = request.env['pos.order'].sudo().search_count(domain_orders)
        
        if total_orders == 0:
            return None
        
        # Lấy các đơn hàng để tính toán chi tiết
        orders = request.env['pos.order'].sudo().search(domain_orders)
        
        # 4. Tính tổng doanh thu và số món
        total_revenue = sum(orders.mapped('amount_total'))
        total_qty = sum(orders.mapped('lines').mapped('qty'))
        
        # 5. Lấy số dư đầu ngày từ phiên đầu tiên trong ngày (nếu có)
        first_session = request.env['pos.session'].sudo().search([
            ('start_at', '>=', dt_start_utc),
            ('start_at', '<=', dt_end_utc),
        ], order='start_at asc', limit=1)
        
        # 6. Tính toán theo từng payment method
        currency = request.env.company.currency_id
        all_payment_methods = request.env['pos.payment.method'].sudo().search([])
        payment_method_data = []
        
        for pm in all_payment_methods:
            # 1. Số dư đầu ngày (chỉ cash có opening balance)
            opening_balance = 0
            if pm.is_cash_count and first_session and pm in first_session.payment_method_ids:
                opening_balance = first_session.cash_register_balance_start
            
            # 2. Thu từ bán hàng - Dùng _read_group để chính xác
            domain_payments = [
                ('pos_order_id', 'in', orders.ids),
                ('payment_method_id', '=', pm.id)
            ]
            
            # Tính tổng tiền
            result = request.env['pos.payment']._read_group(
                domain=domain_payments,
                aggregates=['amount:sum']
            )
            sales_income = result[0][0] if result and result[0] else 0
            
            # Đếm số đơn duy nhất
            payments = request.env['pos.payment'].sudo().search(domain_payments)
            unique_orders = payments.mapped('pos_order_id')
            order_count = len(unique_orders)
            
            # Tính tổng số món trong các đơn này
            total_qty_pm = sum(unique_orders.mapped('lines').mapped('qty'))
            
            # 3. Chi phí trong khoảng thời gian với payment method này
            expenses = request.env['trcf.expense'].sudo().search([
                ('trcf_payment_date', '>=', dt_start_utc),
                ('trcf_payment_date', '<=', dt_end_utc),
                ('state', '=', 'paid'),
                ('trcf_payment_method_id', '=', pm.id),
            ])
            total_expenses = sum(expenses.mapped('trcf_amount'))
            
            # 4. Mua hàng trong khoảng thời gian với payment method này
            purchases = request.env['purchase.order'].sudo().search([
                ('date_order', '>=', dt_start_utc),
                ('date_order', '<=', dt_end_utc),
                ('trcf_payment_status', '=', 'paid'),
                ('trcf_payment_method_id', '=', pm.id),
            ])
            total_purchases = sum(purchases.mapped('amount_total'))
            
            # 5. Số dư hiện tại
            closing_balance = opening_balance + sales_income - total_expenses - total_purchases
            
            # Chỉ thêm vào nếu có giao dịch
            if sales_income > 0 or total_expenses > 0 or total_purchases > 0 or opening_balance > 0:
                payment_method_data.append({
                    'name': pm.name,
                    'opening_balance': opening_balance,
                    'opening_balance_formatted': currency.format(opening_balance),
                    'sales_income': sales_income,
                    'sales_income_formatted': currency.format(sales_income),
                    'order_count': order_count,
                    'total_qty': int(total_qty_pm),
                    'expenses': total_expenses,
                    'expenses_formatted': currency.format(total_expenses),
                    'purchases': total_purchases,
                    'purchases_formatted': currency.format(total_purchases),
                    'closing_balance': closing_balance,
                    'closing_balance_formatted': currency.format(closing_balance),
                })
        
        # Format thời gian
        start_time = dt_start.strftime('%H:%M')
        end_time = dt_end.strftime('%H:%M')
        
        return {
            'start_time': start_time,
            'end_time': end_time,
            'total_revenue': total_revenue,
            'total_revenue_formatted': currency.format(total_revenue),
            'order_count': total_orders,
            'total_qty': int(total_qty),
            'payment_methods': payment_method_data,
        }

    def get_open_session_summary(self, start_date, end_date):
        """Lấy báo cáo cho các phiên đang mở (opened sessions)"""
        # 1. Setup Timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        # Lấy thời gian hiện tại
        now_user_tz = datetime.now(user_tz)
        now_utc = now_user_tz.astimezone(pytz.utc).replace(tzinfo=None)
        
        dt_start = datetime.combine(start_date, time.min)
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        
        # 2. Lấy tất cả các phiên đang mở trong khoảng thời gian
        domain = [
            ('start_at', '>=', dt_start_utc),
            ('state', '=', 'opened'),  # Chỉ lấy phiên đang mở
        ]
        
        sessions = request.env['pos.session'].sudo().search(domain, order='start_at desc')
        
        if not sessions:
            return []
        
        # 3. Format kết quả cho từng phiên
        currency = request.env.company.currency_id
        session_list = []
        
        for session in sessions:
            # Lấy các đơn hàng của phiên này
            orders = session.order_ids.filtered(lambda o: o.state in ['paid', 'done', 'invoiced'])
            
            # Tính tổng doanh thu và số món
            total_revenue = sum(orders.mapped('amount_total'))
            total_qty = sum(orders.mapped('lines').mapped('qty'))
            total_orders = len(orders)
            
            # Lấy tất cả payment methods của phiên
            payment_method_data = []
            
            for pm in session.payment_method_ids:
                # 1. Số dư đầu ca (chỉ cash có)
                opening_balance = session.cash_register_balance_start if pm.is_cash_count else 0
                
                # 2. Thu từ bán hàng - Dùng _read_group
                domain_payments = [
                    ('pos_order_id', 'in', orders.ids),
                    ('payment_method_id', '=', pm.id)
                ]
                
                # Tính tổng tiền
                result = request.env['pos.payment']._read_group(
                    domain=domain_payments,
                    aggregates=['amount:sum']
                )
                sales_income = result[0][0] if result and result[0] else 0
                
                # Đếm số đơn duy nhất
                payments = request.env['pos.payment'].sudo().search(domain_payments)
                unique_orders = payments.mapped('pos_order_id')
                order_count = len(unique_orders)
                
                # Tính tổng số món
                total_qty_pm = sum(unique_orders.mapped('lines').mapped('qty'))
                
                # 3. Chi phí từ lúc mở phiên đến hiện tại
                expenses = request.env['trcf.expense'].sudo().search([
                    ('trcf_payment_date', '>=', session.start_at),
                    ('trcf_payment_date', '<=', now_utc),
                    ('state', '=', 'paid'),
                    ('trcf_payment_method_id', '=', pm.id),
                ])
                total_expenses = sum(expenses.mapped('trcf_amount'))
                
                # 4. Mua hàng từ lúc mở phiên đến hiện tại
                purchases = request.env['purchase.order'].sudo().search([
                    ('date_order', '>=', session.start_at),
                    ('date_order', '<=', now_utc),
                    ('trcf_payment_status', '=', 'paid'),
                    ('trcf_payment_method_id', '=', pm.id),
                ])
                total_purchases = sum(purchases.mapped('amount_total'))
                
                # 5. Số dư hiện tại
                current_balance = opening_balance + sales_income - total_expenses - total_purchases
                
                payment_method_data.append({
                    'name': pm.name,
                    'opening_balance': opening_balance,
                    'opening_balance_formatted': currency.format(opening_balance),
                    'sales_income': sales_income,
                    'sales_income_formatted': currency.format(sales_income),
                    'order_count': order_count,
                    'total_qty': int(total_qty_pm),
                    'expenses': total_expenses,
                    'expenses_formatted': currency.format(total_expenses),
                    'purchases': total_purchases,
                    'purchases_formatted': currency.format(total_purchases),
                    'current_balance': current_balance,
                    'current_balance_formatted': currency.format(current_balance),
                })
            
            # Format thời gian
            start_at_local = pytz.utc.localize(session.start_at).astimezone(user_tz) if session.start_at else None
            current_time_local = now_user_tz.strftime('%H:%M')
            
            # Phát hiện đơn có nhiều phương thức thanh toán (split payment)
            split_payment_orders = []
            for order in orders:
                payment_count = len(order.payment_ids)
                if payment_count > 1:
                    payment_methods = ', '.join(order.payment_ids.mapped('payment_method_id.name'))
                    split_payment_orders.append({
                        'name': order.name,
                        'payment_count': payment_count,
                        'payment_methods': payment_methods,
                        'amount': order.amount_total,
                    })
                
                # Phát hiện discount trong order lines
                for line in order.lines:
                    if line.discount > 0:
                        split_payment_orders.append({
                            'type': 'discount',
                            'order_name': order.name,
                            'product_name': line.product_id.name if line.product_id else 'Unknown',
                            'discount_percent': line.discount,
                            'original_price': line.price_unit,
                            'final_price': line.price_unit * (1 - line.discount/100),
                            'qty': line.qty,
                        })
            
            session_list.append({
                'name': session.name,
                'user_name': session.user_id.name,
                'start_at': start_at_local.strftime('%H:%M') if start_at_local else 'N/A',
                'current_time': current_time_local,
                'total_revenue': total_revenue,
                'total_revenue_formatted': currency.format(total_revenue),
                'order_count': total_orders,
                'total_qty': int(total_qty),
                'payment_methods': payment_method_data,
                'split_payment_count': len(split_payment_orders),
                'split_payment_orders': split_payment_orders,
            })

        
        return session_list
    def get_session_details(self, start_date, end_date):
        """Lấy chi tiết các phiên bán hàng với breakdown tất cả payment methods"""
        # 1. Setup Timezone
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        dt_start = datetime.combine(start_date, time.min)
        dt_end = datetime.combine(end_date, time.max)
        
        # 2. Convert to UTC
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)

        # 3. Lấy tất cả các phiên đã đóng trong khoảng thời gian
        domain = [
            ('start_at', '>=', dt_start_utc),
            ('start_at', '<=', dt_end_utc),
            ('state', '=', 'closed'),  # Chỉ lấy phiên đã đóng
        ]
        
        sessions = request.env['pos.session'].sudo().search(domain, order='start_at desc')
        
        # 4. Format kết quả
        currency = request.env.company.currency_id
        session_list = []
        
        for session in sessions:
            # Tính tổng doanh thu
            total_revenue = sum(session.order_ids.filtered(lambda o: o.state in ['paid', 'done', 'invoiced']).mapped('amount_total'))
            
            # Tính số món bán ra
            total_qty = sum(session.order_ids.filtered(lambda o: o.state in ['paid', 'done', 'invoiced']).mapped('lines').mapped('qty'))
            
            # Lấy tất cả payment methods của phiên
            payment_method_data = []
            
            for pm in session.payment_method_ids:
                # 1. Số dư đầu ca (chỉ cash có)
                opening_balance = session.cash_register_balance_start if pm.is_cash_count else 0
                
                # 2. Thu từ bán hàng - Dùng _read_group
                paid_orders = session.order_ids.filtered(lambda o: o.state in ['paid', 'done', 'invoiced'])
                domain_payments = [
                    ('pos_order_id', 'in', paid_orders.ids),
                    ('payment_method_id', '=', pm.id)
                ]
                
                # Tính tổng tiền
                result = request.env['pos.payment']._read_group(
                    domain=domain_payments,
                    aggregates=['amount:sum']
                )
                sales_income = result[0][0] if result and result[0] else 0
                
                # Đếm số đơn duy nhất
                payments = request.env['pos.payment'].sudo().search(domain_payments)
                unique_orders = payments.mapped('pos_order_id')
                order_count = len(unique_orders)
                
                # Tính tổng số món
                total_qty_pm = sum(unique_orders.mapped('lines').mapped('qty'))
                
                # 3. Chi phí trong thời gian phiên với payment method này
                expenses = request.env['trcf.expense'].sudo().search([
                    ('trcf_payment_date', '>=', session.start_at),
                    ('trcf_payment_date', '<=', session.stop_at),
                    ('state', '=', 'paid'),
                    ('trcf_payment_method_id', '=', pm.id),
                ])
                total_expenses = sum(expenses.mapped('trcf_amount'))
                
                # 4. Mua hàng trong thời gian phiên với payment method này
                purchases = request.env['purchase.order'].sudo().search([
                    ('date_order', '>=', session.start_at),
                    ('date_order', '<=', session.stop_at),
                    ('trcf_payment_status', '=', 'paid'),
                    ('trcf_payment_method_id', '=', pm.id),
                ])
                total_purchases = sum(purchases.mapped('amount_total'))
                
                # 5. Số dư cuối ca
                closing_balance = opening_balance + sales_income - total_expenses - total_purchases
                
                payment_method_data.append({
                    'name': pm.name,
                    'opening_balance': opening_balance,
                    'opening_balance_formatted': currency.format(opening_balance),
                    'sales_income': sales_income,
                    'sales_income_formatted': currency.format(sales_income),
                    'order_count': order_count,
                    'total_qty': int(total_qty_pm),
                    'expenses': total_expenses,
                    'expenses_formatted': currency.format(total_expenses),
                    'purchases': total_purchases,
                    'purchases_formatted': currency.format(total_purchases),
                    'closing_balance': closing_balance,
                    'closing_balance_formatted': currency.format(closing_balance),
                })
            
            # Format thời gian
            start_at_local = pytz.utc.localize(session.start_at).astimezone(user_tz) if session.start_at else None
            stop_at_local = pytz.utc.localize(session.stop_at).astimezone(user_tz) if session.stop_at else None
            
            # Phát hiện đơn có nhiều phương thức thanh toán (split payment)
            split_payment_orders = []
            for order in paid_orders:
                payment_count = len(order.payment_ids)
                if payment_count > 1:
                    payment_methods = ', '.join(order.payment_ids.mapped('payment_method_id.name'))
                    split_payment_orders.append({
                        'name': order.name,
                        'payment_count': payment_count,
                        'payment_methods': payment_methods,
                        'amount': order.amount_total,
                    })
                
                # Phát hiện discount trong order lines
                for line in order.lines:
                    if line.discount > 0:
                        split_payment_orders.append({
                            'type': 'discount',
                            'order_name': order.name,
                            'product_name': line.product_id.name if line.product_id else 'Unknown',
                            'discount_percent': line.discount,
                            'original_price': line.price_unit,
                            'final_price': line.price_unit * (1 - line.discount/100),
                            'qty': line.qty,
                        })
            
            session_list.append({
                'name': session.name,
                'user_name': session.user_id.name,
                'start_at': start_at_local.strftime('%H:%M') if start_at_local else 'N/A',
                'stop_at': stop_at_local.strftime('%H:%M') if stop_at_local else 'N/A',
                'total_revenue': total_revenue,
                'total_revenue_formatted': currency.format(total_revenue),
                'order_count': session.order_count,
                'total_qty': int(total_qty),
                'payment_methods': payment_method_data,
                'split_payment_count': len(split_payment_orders),
                'split_payment_orders': split_payment_orders,
            })

        
        return session_list