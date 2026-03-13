# -*- coding: utf-8 -*-
import logging
from datetime import date, datetime

from odoo import fields, http
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
        # PHẦN 2: STOCK MATRIX — Tồn kho theo Kho × Sản phẩm (chia 2 bảng)
        # =====================================================================

        # Đọc setting kho quầy
        shop_wh_id_str = env['ir.config_parameter'].sudo().get_param(
            'trcf_ops_audit.trcf_ops_shop_warehouse_id', default=False
        )
        shop_wh_id = int(shop_wh_id_str) if shop_wh_id_str and shop_wh_id_str != 'False' else False

        # Lấy tất cả kho đang active
        warehouses = env['stock.warehouse'].sudo().search([('active', '=', True)])

        # Lấy sản phẩm storable (có theo dõi tồn kho)
        storable_products = env['product.product'].sudo().search([
            ('is_storable', '=', True),
            ('active', '=', True),
        ], order='name asc')

        # Lấy tất cả stock.quant trong các vị trí nội bộ
        quants = env['stock.quant'].sudo().search([
            ('product_id', 'in', storable_products.ids),
            ('location_id.usage', '=', 'internal'),
        ])

        # Gom quant theo (warehouse_id, product_id) → tổng quantity
        quant_map = {}  # {(warehouse_id, product_id): quantity}
        for q in quants:
            wh = q.location_id.warehouse_id
            if not wh:
                continue
            key = (wh.id, q.product_id.id)
            quant_map[key] = quant_map.get(key, 0.0) + q.quantity

        # Sản phẩm có ít nhất 1 quant
        active_product_ids = set()
        for (wh_id, prod_id), qty in quant_map.items():
            active_product_ids.add(prod_id)
        active_storable = storable_products.filtered(lambda p: p.id in active_product_ids)

        # Phân loại sản phẩm
        # Nguyên liệu mua hàng: purchase_ok = True (trên product.template)
        purchased_products = active_storable.filtered(
            lambda p: p.product_tmpl_id.purchase_ok
        )
        # Bán thành phẩm: purchase_ok = False AND sale_ok = False
        semi_finished_products = active_storable.filtered(
            lambda p: not p.product_tmpl_id.purchase_ok and not p.product_tmpl_id.sale_ok
        )

        # Build matrix helper
        def _build_matrix(products, product_type):
            """
            product_type: 'purchased' hoặc 'semi'
            Trả về (matrix, total_neg, warning_counts)
            """
            matrix = []
            total_neg = 0
            warn_counts = {
                'thieu_nhap_kho': 0,
                'thieu_chuyen_kho': 0,
                'thieu_che_bien': 0,
            }
            for prod in products:
                row_cells = []
                has_anomaly = False
                for wh in warehouses:
                    qty = quant_map.get((wh.id, prod.id), 0.0)
                    warning_type = ''
                    if qty < 0:
                        status = 'negative'
                        total_neg += 1
                        has_anomaly = True
                        # Xác định loại cảnh báo
                        if product_type == 'semi':
                            warning_type = 'thieu_che_bien'
                        elif shop_wh_id and wh.id == shop_wh_id:
                            warning_type = 'thieu_chuyen_kho'
                        else:
                            warning_type = 'thieu_nhap_kho'
                        warn_counts[warning_type] = warn_counts.get(warning_type, 0) + 1
                    elif qty == 0:
                        status = 'zero'
                    else:
                        status = 'ok'
                    row_cells.append({
                        'qty': qty,
                        'status': status,
                        'warehouse_id': wh.id,
                        'warning_type': warning_type,
                    })
                matrix.append({
                    'product_name': prod.name,
                    'product_id': prod.id,
                    'uom': prod.uom_id.name if prod.uom_id else '',
                    'cells': row_cells,
                    'has_anomaly': has_anomaly,
                })
            return matrix, total_neg, warn_counts

        stock_matrix_purchased, total_neg_purchased, warn_purchased = _build_matrix(
            purchased_products, 'purchased'
        )
        stock_matrix_semi, total_neg_semi, warn_semi = _build_matrix(
            semi_finished_products, 'semi'
        )

        # Danh sách tên kho cho header cột
        warehouse_names = [wh.name for wh in warehouses]
        warehouse_codes = [wh.code for wh in warehouses]

        # Tổng negative cũ (cho summary cards)
        total_negative = total_neg_purchased + total_neg_semi

        # =====================================================================
        # PHẦN 3: SCRAP — Huỷ sản phẩm (tháng hiện tại)
        # =====================================================================
        today = date.today()
        first_of_month = today.replace(day=1)

        scraps = env['stock.scrap'].sudo().search([
            ('state', '=', 'done'),
            ('date_done', '>=', fields.Datetime.to_string(
                datetime.combine(first_of_month, datetime.min.time())
            )),
        ])

        scrap_count = len(scraps)
        scrap_total_value = 0.0
        for sc in scraps:
            unit_cost = sc.product_id.standard_price or 0.0
            # Quy đổi scrap_qty về UoM gốc để tính giá trị
            qty_in_base_uom = sc.product_uom_id._compute_quantity(
                sc.scrap_qty, sc.product_id.uom_id
            )
            scrap_total_value += qty_in_base_uom * unit_cost

        # =====================================================================
        # PHẦN 4: KIỂM KÊ — Lấy từ trcf.inventory.check (tháng hiện tại)
        # =====================================================================
        inventory_checks = env['trcf.inventory.check'].sudo().search([
            ('state', '=', 'done'),
            ('check_date', '>=', fields.Datetime.to_string(
                datetime.combine(first_of_month, datetime.min.time())
            )),
        ])

        inventory_check_count = len(inventory_checks)
        # Tổng chênh lệch giá trị (total_difference_value < 0 = hao hụt)
        inventory_net_loss = 0.0
        inventory_total_system_value = 0.0
        for ic in inventory_checks:
            inventory_net_loss += abs(min(ic.total_difference_value, 0))  # chỉ tính hao hụt
            inventory_total_system_value += ic.total_system_value

        # % Hao hụt trung bình (dùng loss_percentage đã tính sẵn từ module)
        if inventory_checks:
            inventory_loss_rate = round(
                sum(ic.loss_percentage for ic in inventory_checks) / len(inventory_checks), 2
            )
        else:
            inventory_loss_rate = 0.0

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
            # Phần 2 - Stock Matrix (chia 2 bảng)
            'stock_matrix_purchased': stock_matrix_purchased,
            'stock_matrix_semi': stock_matrix_semi,
            'warehouse_names': warehouse_names,
            'warehouse_codes': warehouse_codes,
            'total_negative': total_negative,
            'total_neg_purchased': total_neg_purchased,
            'total_neg_semi': total_neg_semi,
            'warn_purchased': warn_purchased,
            'warn_semi': warn_semi,
            'shop_wh_configured': bool(shop_wh_id),
            # Phần 3 - Scrap
            'scrap_count': scrap_count,
            'scrap_total_value': scrap_total_value,
            # Phần 4 - Kiểm kê (từ trcf.inventory.check)
            'inventory_check_count': inventory_check_count,
            'inventory_net_loss': inventory_net_loss,
            'inventory_loss_rate': inventory_loss_rate,
            'inventory_total_system_value': inventory_total_system_value,
        }

        return request.render(
            'trcf_ops_audit.trcf_ops_dashboard_template',
            values
        )
