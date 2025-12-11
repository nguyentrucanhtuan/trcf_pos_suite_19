# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
from datetime import datetime, timedelta


class TrcfPnlDashboardController(http.Controller):
    
    def _get_date_range(self, period, date_from, date_to):
        """Xác định khoảng thời gian dựa trên period"""
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if period == 'day':
            start_date = today
            end_date = today + timedelta(days=1)
            period_label = 'Hôm nay'
        elif period == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=7)
            period_label = 'Tuần này'
        elif period == 'month':
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1)
            period_label = 'Tháng này'
        elif period == 'custom' and date_from and date_to:
            start_date = datetime.strptime(date_from, '%Y-%m-%d')
            end_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            period_label = f'{date_from} - {date_to}'
        else:
            # Default: tháng này
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = today.replace(year=today.year + 1, month=1, day=1)
            else:
                end_date = today.replace(month=today.month + 1, day=1)
            period_label = 'Tháng này'
        
        return start_date, end_date, period_label
    
    def _get_revenue_data(self, start_date, end_date):
        """Lấy doanh thu từ pos.order"""
        PosOrder = request.env['pos.order'].sudo()
        orders = PosOrder.search([
            ('date_order', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')),
            ('date_order', '<', end_date.strftime('%Y-%m-%d %H:%M:%S')),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ])
        
        revenue = sum(order.amount_total for order in orders)
        order_count = len(orders)
        
        return revenue, order_count
    
    def _get_cogs_data(self, start_date, end_date):
        """Lấy COGS từ purchase.order với breakdown paid/unpaid"""
        PurchaseOrder = request.env['purchase.order'].sudo()
        purchases = PurchaseOrder.search([
            ('create_date', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')),
            ('create_date', '<', end_date.strftime('%Y-%m-%d %H:%M:%S')),
            ('state', 'in', ['purchase', 'done']),
        ])
        
        cogs_paid = 0
        cogs_unpaid = 0
        
        for purchase in purchases:
            total_amount = purchase.amount_total
            if hasattr(purchase, 'trcf_payment_status'):
                if purchase.trcf_payment_status == 'paid':
                    cogs_paid += total_amount
                else:
                    cogs_unpaid += total_amount
            else:
                cogs_unpaid += total_amount
        
        cogs = cogs_paid + cogs_unpaid
        return cogs, cogs_paid, cogs_unpaid
    
    def _get_operating_expenses_data(self, start_date, end_date, revenue):
        """Lấy chi phí hoạt động từ trcf.expense, group theo category"""
        Expense = request.env['trcf.expense'].sudo()
        expenses = Expense.search([
            ('create_date', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')),
            ('create_date', '<', end_date.strftime('%Y-%m-%d %H:%M:%S')),
            ('state', 'in', ['approved', 'paid']),
        ])
        
        # Group by category
        category_data = {}
        total_paid = 0
        total_unpaid = 0
        
        for expense in expenses:
            category_name = expense.trcf_category_id.name if expense.trcf_category_id else 'Khác'
            
            if category_name not in category_data:
                category_data[category_name] = {
                    'total': 0,
                    'paid': 0,
                    'unpaid': 0,
                    'margin': 0,
                }
            
            amount = expense.trcf_amount
            category_data[category_name]['total'] += amount
            
            if expense.state == 'paid':
                category_data[category_name]['paid'] += amount
                total_paid += amount
            else:  # approved but not paid
                category_data[category_name]['unpaid'] += amount
                total_unpaid += amount
        
        # Tính % so với doanh thu cho từng category
        if revenue > 0:
            for category_name in category_data:
                category_data[category_name]['margin'] = round(
                    (category_data[category_name]['total'] / revenue) * 100, 1
                )
        
        total_expenses = total_paid + total_unpaid
        return total_expenses, total_paid, total_unpaid, category_data
    
    def _get_cash_flow_data(self, start_date, end_date):
        """Lấy dữ liệu dòng tiền theo phương thức thanh toán"""
        PaymentCount = request.env['trcf.pos.session.payment.count'].sudo()
        Session = request.env['pos.session'].sudo()
        
        # Lấy các session trong khoảng thời gian
        sessions = Session.search([
            ('start_at', '>=', start_date.strftime('%Y-%m-%d %H:%M:%S')),
            ('start_at', '<', end_date.strftime('%Y-%m-%d %H:%M:%S')),
            ('state', 'in', ['closed']),
        ])
        
        # Lấy payment counts từ các sessions
        payment_counts = PaymentCount.search([
            ('session_id', 'in', sessions.ids),
        ])
        
        # Group by payment method
        payment_data = {}
        total_expected = 0
        total_counted = 0
        
        for pc in payment_counts:
            pm_name = pc.payment_method_name or 'Khác'
            
            if pm_name not in payment_data:
                payment_data[pm_name] = {
                    'expected': 0,
                    'counted': 0,
                    'difference': 0,
                    'variance_pct': 0,
                }
            
            payment_data[pm_name]['expected'] += pc.expected_amount
            payment_data[pm_name]['counted'] += pc.counted_amount
            payment_data[pm_name]['difference'] += pc.difference
            
            total_expected += pc.expected_amount
            total_counted += pc.counted_amount
        
        # Tính % chênh lệch cho từng payment method
        for pm_name in payment_data:
            expected = payment_data[pm_name]['expected']
            if expected > 0:
                payment_data[pm_name]['variance_pct'] = round(
                    (payment_data[pm_name]['difference'] / expected) * 100, 2
                )
        
        total_difference = total_counted - total_expected
        total_variance_pct = round((total_difference / total_expected) * 100, 2) if total_expected > 0 else 0
        
        return payment_data, total_expected, total_counted, total_difference, total_variance_pct
    
    def _calculate_revenue_change(self, revenue, start_date, end_date):
        """Tính % thay đổi doanh thu so với kỳ trước"""
        period_days = (end_date - start_date).days
        prev_start = start_date - timedelta(days=period_days)
        prev_end = start_date
        
        PosOrder = request.env['pos.order'].sudo()
        prev_orders = PosOrder.search([
            ('date_order', '>=', prev_start.strftime('%Y-%m-%d %H:%M:%S')),
            ('date_order', '<', prev_end.strftime('%Y-%m-%d %H:%M:%S')),
            ('state', 'in', ['paid', 'done', 'invoiced']),
        ])
        prev_revenue = sum(order.amount_total for order in prev_orders)
        
        if prev_revenue > 0:
            revenue_change = ((revenue - prev_revenue) / prev_revenue) * 100
        else:
            revenue_change = 100 if revenue > 0 else 0
        
        return revenue_change, prev_revenue
    
    def _calculate_pnl_metrics(self, revenue, cogs, operating_expenses, revenue_change, prev_revenue):
        """Tính các chỉ số P&L"""
        gross_profit = revenue - cogs
        profit_before_tax = gross_profit - operating_expenses
        
        # Tính thuế (giả định 20%)
        tax = profit_before_tax * 0.2 if profit_before_tax > 0 else 0
        net_profit = profit_before_tax - tax
        
        # Tính % so với doanh thu (margins)
        if revenue > 0:
            cogs_margin = (cogs / revenue) * 100
            opex_margin = (operating_expenses / revenue) * 100
            gross_margin = (gross_profit / revenue) * 100
            profit_before_tax_margin = (profit_before_tax / revenue) * 100
            net_margin = (net_profit / revenue) * 100
        else:
            cogs_margin = opex_margin = gross_margin = profit_before_tax_margin = net_margin = 0
        
        # Tính % thay đổi
        if prev_revenue > 0:
            gross_profit_change = ((gross_profit - (prev_revenue * 0.6)) / (prev_revenue * 0.6)) * 100
        else:
            gross_profit_change = 100 if gross_profit > 0 else 0
        
        net_profit_change = revenue_change
        
        return {
            'gross_profit': gross_profit,
            'profit_before_tax': profit_before_tax,
            'tax': tax,
            'net_profit': net_profit,
            'cogs_margin': round(cogs_margin, 1),
            'opex_margin': round(opex_margin, 1),
            'gross_margin': round(gross_margin, 1),
            'profit_before_tax_margin': round(profit_before_tax_margin, 1),
            'net_margin': round(net_margin, 1),
            'gross_profit_change': round(gross_profit_change, 1),
            'net_profit_change': round(net_profit_change, 1),
        }
    
    @http.route('/trcf_pnl/dashboard', type='http', auth='user', website=False)
    def pnl_dashboard(self, period='month', date_from=None, date_to=None, **kw):
        """Render P&L Dashboard with real POS data"""
        
        # 1. Xác định khoảng thời gian
        start_date, end_date, period_label = self._get_date_range(period, date_from, date_to)
        
        # 2. Lấy doanh thu
        revenue, order_count = self._get_revenue_data(start_date, end_date)
        
        # 3. Lấy COGS
        cogs, cogs_paid, cogs_unpaid = self._get_cogs_data(start_date, end_date)
        
        # 4. Lấy Operating Expenses (cần revenue để tính %)
        operating_expenses, opex_paid, opex_unpaid, category_data = self._get_operating_expenses_data(start_date, end_date, revenue)
        
        # 5. Tính % thay đổi doanh thu
        revenue_change, prev_revenue = self._calculate_revenue_change(revenue, start_date, end_date)
        
        # 6. Tính các chỉ số P&L
        pnl_metrics = self._calculate_pnl_metrics(revenue, cogs, operating_expenses, revenue_change, prev_revenue)
        
        # 7. Lấy Cash Flow theo payment method
        payment_flow, cf_expected, cf_counted, cf_difference, cf_variance = self._get_cash_flow_data(start_date, end_date)
        
        # 8. Tổng hợp dữ liệu
        pnl_data = {
            'revenue': revenue,
            'cogs': cogs,
            'cogs_paid': cogs_paid,
            'cogs_unpaid': cogs_unpaid,
            'operating_expenses': operating_expenses,
            'opex_paid': opex_paid,
            'opex_unpaid': opex_unpaid,
            'expense_categories': category_data,
            'revenue_change': round(revenue_change, 1),
            'order_count': order_count,
            **pnl_metrics,
        }
        
        return request.render('trcf_pnl_dashboard.pnl_dashboard_template', {
            'pnl': pnl_data,
            'payment_flow': payment_flow,
            'cf_total_expected': cf_expected,
            'cf_total_counted': cf_counted,
            'cf_total_difference': cf_difference,
            'cf_total_variance': cf_variance,
            'period': period,
            'period_label': period_label,
            'date_from': date_from or start_date.strftime('%Y-%m-%d'),
            'date_to': date_to or (end_date - timedelta(days=1)).strftime('%Y-%m-%d'),
        })
