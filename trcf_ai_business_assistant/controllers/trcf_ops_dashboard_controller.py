# -*- coding: utf-8 -*-
import logging
from datetime import date

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class TrcfOpsDashboardController(http.Controller):

    @http.route('/trcf_ai/ops_dashboard', type='http', auth='user', website=False)
    def ops_dashboard(self, **kw):
        """Dashboard kiểm soát vận hành — luôn hiển thị các mục audit."""

        env = request.env

        # Tất cả sản phẩm đang có mặt trên POS
        pos_products = env['product.template'].sudo().search([
            ('available_in_pos', '=', True),
            ('active', '=', True),
        ])

        # Phân loại sản phẩm:
        #   - Mua thẳng  : purchase_ok=True  → bán trực tiếp, KHÔNG cần BoM
        #   - Sản xuất   : purchase_ok=False → phải có BoM để tồn kho trừ đúng
        direct_products = pos_products.filtered(lambda p: p.purchase_ok)
        manufactured_products = pos_products.filtered(lambda p: not p.purchase_ok)

        # BoM đã tồn tại cho sản phẩm sản xuất
        bom_product_ids = set(
            env['mrp.bom'].sudo().search([
                ('product_tmpl_id', 'in', manufactured_products.ids),
            ]).mapped('product_tmpl_id').ids
        )

        # Danh sách sản phẩm sản xuất CHƯA có BoM → cần cảnh báo
        # Kèm chi phí (standard_price) và giá bán (list_price) để phát hiện bất thường
        products_missing_bom = []
        for p in manufactured_products:
            if p.id in bom_product_ids:
                continue
            cost = p.standard_price or 0.0
            price = p.list_price or 0.0

            # Phát hiện bất thường:
            #   no_price  → giá bán = 0, chưa nhập giá
            #   no_cost   → chi phí = 0, chưa nhập giá vốn
            #   cost_over → chi phí >= giá bán, đang bán lỗ hoặc dữ liệu sai
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

        # Đếm số lượng có bất thường giá (để hiển thị thẻ cảnh báo riêng)
        total_price_anomaly = sum(1 for p in products_missing_bom if p['anomaly'] != 'none')

        total_pos = len(pos_products)
        total_direct = len(direct_products)
        total_manufactured = len(manufactured_products)
        total_ok = total_manufactured - len(products_missing_bom)
        total_missing = len(products_missing_bom)
        pct_complete = round(total_ok / total_manufactured * 100) if total_manufactured else 100

        values = {
            'today': date.today().strftime('%d/%m/%Y'),
            'total_pos': total_pos,
            'total_direct': total_direct,
            'total_manufactured': total_manufactured,
            'total_ok': total_ok,
            'total_missing': total_missing,
            'total_price_anomaly': total_price_anomaly,
            'pct_complete': pct_complete,
            'products_missing_bom': products_missing_bom,
        }

        return request.render(
            'trcf_ai_business_assistant.trcf_ops_dashboard_template',
            values
        )
