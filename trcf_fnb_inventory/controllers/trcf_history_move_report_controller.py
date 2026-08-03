import pytz
from datetime import datetime, time, timedelta
from odoo import http
from odoo.http import request
from ..i18n import get_translator

class TrcfHistoryMoveReportController(http.Controller):

    @http.route('/trcf_fnb_inventory/move_report', type='http', auth='user', website=False)
    def move_report(self, filter_type='today', date_from=None, date_to=None, search='', **kw):
        # 1. Lấy Timezone và thời gian
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        now_user_tz = datetime.now(user_tz)
        today = now_user_tz.date()

        # 2. Xác định mốc thời gian
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

        move_stats = self.get_move_stats(current_start, current_end, search=search)

        def format_qty(value):
            if not value: return "0"
            # Format: 1.000.000,5
            formatted = "{:,.2f}".format(value).rstrip('0').rstrip('.')
            return formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')

        vals = {
            't': get_translator(request),
            'filter_type': filter_type,
            'date_from': date_from,
            'date_to': date_to,
            'move_stats': move_stats,
            'today': today,
            'format_qty': format_qty,
            'search_query': search,
        }

        return request.render('trcf_fnb_inventory.move_report_template', vals)

    def get_move_stats(self, start_date, end_date, search=''):
        """Logic tính toán 4 luồng Nhập Xuất (Chỉ hiện SP theo dõi kho)"""
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        dt_start = datetime.combine(start_date, time.min)
        dt_end = datetime.combine(end_date, time.max)
        
        # Chuyển sang UTC để truy vấn DB
        dt_start_utc = user_tz.localize(dt_start).astimezone(pytz.utc).replace(tzinfo=None)
        dt_end_utc = user_tz.localize(dt_end).astimezone(pytz.utc).replace(tzinfo=None)

        # 1. Domain cơ bản cho SP có theo dõi kho
        product_domain = [('is_storable', '=', True)]
        if search:
            product_domain += [('name', 'ilike', search)]
        
        target_products = request.env['product.product'].sudo().search(product_domain)
        if not target_products:
            return []

        domain_base = [
            ('date', '>=', dt_start_utc),
            ('date', '<=', dt_end_utc),
            ('state', '=', 'done'),
            ('product_id', 'in', target_products.ids)
        ]

        # --- LOGIC TRUY VẤN NHÓM ---
        res_sales = request.env['stock.move'].sudo()._read_group(
            domain=domain_base + [('location_id.usage', '=', 'internal'), ('location_dest_id.usage', '=', 'customer')],
            groupby=['product_id'], aggregates=['quantity:sum']
        )
        res_consumed = request.env['stock.move'].sudo()._read_group(
            domain=domain_base + [('location_id.usage', '=', 'internal'), ('location_dest_id.usage', '=', 'production')],
            groupby=['product_id'], aggregates=['quantity:sum']
        )
        res_purchase = request.env['stock.move'].sudo()._read_group(
            domain=domain_base + [('location_id.usage', '=', 'supplier'), ('location_dest_id.usage', '=', 'internal')],
            groupby=['product_id'], aggregates=['quantity:sum']
        )
        res_in_prod = request.env['stock.move'].sudo()._read_group(
            domain=domain_base + [('location_id.usage', '=', 'production'), ('location_dest_id.usage', '=', 'internal')],
            groupby=['product_id'], aggregates=['quantity:sum']
        )
        res_scrap = request.env['stock.move'].sudo()._read_group(
            domain=domain_base + [('scrap_id', '!=', False)],
            groupby=['product_id'], aggregates=['quantity:sum']
        )

        stats = {}
        for p in target_products:
            stats[p.id] = {
                'name': p.name,
                'uom': p.uom_id.name,
                'sales_qty': 0,
                'consumed_qty': 0,
                'scrap_qty': 0,
                'purchase_qty': 0,
                'prod_in_qty': 0,
            }

        for p, q in res_sales: 
            if p and p.id in stats: stats[p.id]['sales_qty'] = q or 0
        for p, q in res_consumed: 
            if p and p.id in stats: stats[p.id]['consumed_qty'] = q or 0
        for p, q in res_purchase: 
            if p and p.id in stats: stats[p.id]['purchase_qty'] = q or 0
        for p, q in res_in_prod: 
            if p and p.id in stats: stats[p.id]['prod_in_qty'] = q or 0
        for p, q in res_scrap: 
            if p and p.id in stats: stats[p.id]['scrap_qty'] = q or 0

        stats_list = []
        for s in stats.values():
            if not search:
                if s['sales_qty'] or s['consumed_qty'] or s['scrap_qty'] or s['purchase_qty'] or s['prod_in_qty']:
                    stats_list.append(s)
            else:
                stats_list.append(s)

        # Sắp xếp mặc định theo lượng Xuất tổng (Bán + SX + Huỷ) giảm dần
        stats_list.sort(key=lambda x: (x['sales_qty'] + x['consumed_qty'] + x['scrap_qty']), reverse=True)

        return stats_list
