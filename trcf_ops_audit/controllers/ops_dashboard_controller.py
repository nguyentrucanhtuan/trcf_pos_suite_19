# -*- coding: utf-8 -*-
import logging
from datetime import date

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TrcfOpsDashboardController(http.Controller):

    @http.route('/trcf_ops_audit/dashboard', type='http', auth='user', website=False)
    def ops_dashboard(self, **kw):
        """Dashboard kiểm soát vận hành — luôn hiển thị các mục audit."""

        env = request.env

        # =====================================================================
        # PHẦN 1: AUDIT CÔNG THỨC (BoM)
        # =====================================================================

        # Tất cả sản phẩm đang có mặt trên POS
        pos_products = env['product.template'].sudo().search([
            ('available_in_pos', '=', True),
            ('active', '=', True),
        ])

        direct_products = pos_products.filtered(lambda p: p.purchase_ok)
        manufactured_products = pos_products.filtered(lambda p: not p.purchase_ok)

        bom_product_ids = set(
            env['mrp.bom'].sudo().search([
                ('product_tmpl_id', 'in', manufactured_products.ids),
            ]).mapped('product_tmpl_id').ids
        )

        products_missing_bom = []
        for p in manufactured_products:
            if p.id in bom_product_ids:
                continue
            cost = p.standard_price or 0.0
            price = p.list_price or 0.0

            if price == 0:
                anomaly = 'no_price'
            elif cost == 0:
                anomaly = 'no_cost'
            elif cost >= price:
                anomaly = 'cost_over'
            else:
                anomaly = 'none'

            products_missing_bom.append({
                'id': p.id,
                'name': p.name,
                'categ': p.categ_id.name if p.categ_id else '—',
                'pos_categ': p.pos_categ_ids[0].name if p.pos_categ_ids else '—',
                'cost': cost,
                'price': price,
                'anomaly': anomaly,
                'bom_url': f'/odoo/manufacturing/bom/new?product_tmpl_id={p.id}',
                'product_url': f'/odoo/inventory/products/{p.id}',
            })

        total_price_anomaly = sum(1 for p in products_missing_bom if p['anomaly'] != 'none')
        total_pos = len(pos_products)
        total_direct = len(direct_products)
        total_manufactured = len(manufactured_products)
        total_ok = total_manufactured - len(products_missing_bom)
        total_missing = len(products_missing_bom)
        pct_complete = round(total_ok / total_manufactured * 100) if total_manufactured else 100

        # =====================================================================
        # PHẦN 2: STOCK MATRIX — Tồn kho theo Kho × Sản phẩm
        # =====================================================================

        # Lấy tất cả kho đang active
        warehouses = env['stock.warehouse'].sudo().search([('active', '=', True)])

        # Lấy sản phẩm storable (có theo dõi tồn kho)
        storable_products = env['product.product'].sudo().search([
            ('is_storable', '=', True),
            ('active', '=', True),
        ], order='name asc')

        # Lấy tất cả stock.quant cho các sản phẩm storable trong các vị trí nội bộ
        # type='internal' để chỉ tính kho nội bộ (không tính transit, khách hàng, v.v.)
        quants = env['stock.quant'].sudo().search([
            ('product_id', 'in', storable_products.ids),
            ('location_id.usage', '=', 'internal'),
        ])

        # Gom quant theo (warehouse_id, product_id) → tổng quantity
        # Tìm warehouse của mỗi location thông qua location_id.warehouse_id
        quant_map = {}  # {(warehouse_id, product_id): quantity}
        for q in quants:
            wh = q.location_id.warehouse_id
            if not wh:
                continue
            key = (wh.id, q.product_id.id)
            quant_map[key] = quant_map.get(key, 0.0) + q.quantity

        # Lọc chỉ những sản phẩm có ít nhất 1 quant trong bất kỳ kho nào
        # (hoặc có số âm) — tránh bảng quá rộng
        active_product_ids = set()
        for (wh_id, prod_id), qty in quant_map.items():
            active_product_ids.add(prod_id)
        # Cũng include sản phẩm bị âm dù không có quant
        active_storable = storable_products.filtered(lambda p: p.id in active_product_ids)

        # Đếm bất thường
        total_negative = 0
        total_zero_stock = 0

        # Build matrix rows: mỗi row là 1 sản phẩm, cột là từng kho
        stock_matrix = []
        for prod in active_storable:
            row_cells = []
            has_anomaly = False
            for wh in warehouses:
                qty = quant_map.get((wh.id, prod.id), 0.0)
                if qty < 0:
                    status = 'negative'
                    total_negative += 1
                    has_anomaly = True
                elif qty == 0:
                    status = 'zero'
                    total_zero_stock += 1
                else:
                    status = 'ok'
                row_cells.append({
                    'qty': qty,
                    'status': status,
                    'warehouse_id': wh.id,
                })
            stock_matrix.append({
                'product_name': prod.name,
                'product_id': prod.id,
                'cells': row_cells,
                'has_anomaly': has_anomaly,
            })

        # Danh sách tên kho cho header cột
        warehouse_names = [wh.name for wh in warehouses]
        warehouse_codes = [wh.code for wh in warehouses]

        values = {
            'today': date.today().strftime('%d/%m/%Y'),
            # Phần 1 - BoM
            'total_pos': total_pos,
            'total_direct': total_direct,
            'total_manufactured': total_manufactured,
            'total_ok': total_ok,
            'total_missing': total_missing,
            'total_price_anomaly': total_price_anomaly,
            'pct_complete': pct_complete,
            'products_missing_bom': products_missing_bom,
            # Phần 2 - Stock Matrix
            'stock_matrix': stock_matrix,
            'warehouse_names': warehouse_names,
            'warehouse_codes': warehouse_codes,
            'total_negative': total_negative,
            'total_zero_stock': total_zero_stock,
        }

        return request.render(
            'trcf_ops_audit.trcf_ops_dashboard_template',
            values
        )
