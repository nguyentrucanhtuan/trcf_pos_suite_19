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
            'expense_total': expense_stats['total_formatted'],
            'expense_by_payment_method': expense_stats['by_payment_method'],
            'purchase_total': purchase_stats['total_formatted'],
            'purchase_by_payment_method': purchase_stats['by_payment_method'],
            'cash_balance': cash_balance['formatted'],
            'cash_balance_detail': cash_balance['detail'],
            'sessions': sessions,
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
        
        # 6. Đếm số đơn hàng cho mỗi payment method
        payment_method_order_count = {}
        for order in request.env['pos.order'].browse(order_ids):
            for payment in order.payment_ids:
                pm_id = payment.payment_method_id.id
                if pm_id not in payment_method_order_count:
                    payment_method_order_count[pm_id] = set()
                payment_method_order_count[pm_id].add(order.id)
        
        # 7. Format kết quả
        currency = request.env.company.currency_id
        payment_methods = []
        
        # Định nghĩa màu sắc cho các phương thức thanh toán
        colors = ['cyan-500', 'violet-500', 'amber-500', 'green-500', 'blue-500', 'pink-500', 'indigo-500', 'red-500']
        
        for idx, (payment_method, amount_sum) in enumerate(result):
            if payment_method:  # Bỏ qua nếu payment_method là False/None
                order_count = len(payment_method_order_count.get(payment_method.id, set()))
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
                
                # 2. Thu từ bán hàng trong phiên
                sales_income = sum(
                    payment.amount
                    for order in session.order_ids.filtered(lambda o: o.state in ['paid', 'done', 'invoiced'])
                    for payment in order.payment_ids
                    if payment.payment_method_id == pm
                )
                
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
            })
        
        return session_list
