from odoo import http
from odoo.http import request
import pytz
from datetime import datetime, time
import json

class TrcfPurchaseController(http.Controller):

    @http.route('/trcf_fnb_inventory/purchase_list', type='http', auth='user', website=False)
    def purchase_list(self, **kw):
        # Lấy timezone của user
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        # Tính toán khoảng thời gian của ngày hôm nay theo timezone user
        now_user = datetime.now(user_tz)
        start_of_day = user_tz.localize(datetime.combine(now_user.date(), time.min))
        end_of_day = user_tz.localize(datetime.combine(now_user.date(), time.max))
        
        # Chuyển sang UTC để query
        start_of_day_utc = start_of_day.astimezone(pytz.utc).replace(tzinfo=None)
        end_of_day_utc = end_of_day.astimezone(pytz.utc).replace(tzinfo=None)
        
        # Query purchase orders của công ty hiện tại - chỉ lấy những đơn đã xác nhận (trạng thái 'purchase') và tạo trong ngày
        company_id = request.env.company.id
        purchase_orders = request.env['purchase.order'].sudo().search([
            ('company_id', '=', company_id),
            ('state', '=', 'purchase'),  # Chỉ hiển thị đơn mua hàng đã xác nhận
            ('create_date', '>=', start_of_day_utc),  # Tạo từ đầu ngày
            ('create_date', '<=', end_of_day_utc)  # Đến cuối ngày
        ], order='create_date desc')  # Sắp xếp theo thời gian tạo gần nhất
        
        # Chuẩn bị dữ liệu để hiển thị
        orders_data = []
        for po in purchase_orders:
            # Tính tổng VAT
            total_vat = sum(line.price_tax for line in po.order_line)
            
            # Lấy payment status từ trcf_payment_status
            payment_status_display = dict(po._fields['trcf_payment_status'].selection).get(po.trcf_payment_status, 'Chưa thanh toán')
            
            # Xác định màu sắc theo payment status
            status_color = 'slate'
            if po.trcf_payment_status == 'paid':
                status_color = 'green'
            elif po.trcf_payment_status == 'unpaid':
                status_color = 'slate'
            
            # Lấy payment method name
            payment_method_name = po.trcf_payment_method_id.name if po.trcf_payment_method_id else '--'
            
            # Format ngày theo timezone user
            date_order_user = pytz.utc.localize(po.date_order).astimezone(user_tz)
            date_formatted = date_order_user.strftime('%d/%m/%Y %H:%M:%S')
            
            # Format payment date nếu có
            payment_date_formatted = ''
            if po.trcf_payment_date:
                payment_date_formatted = po.trcf_payment_date.strftime('%d/%m/%Y')
            
            orders_data.append({
                'id': po.id,
                'name': po.name,
                'partner_name': po.partner_id.name,
                'state': po.state,
                'payment_status': payment_status_display,
                'status_color': status_color,
                'payment_method': payment_method_name,
                'total_vat': total_vat,
                'amount_total': po.amount_total,
                'date_order': date_formatted,
                'payment_date': payment_date_formatted,
            })
        
        vals = {
            'purchase_orders': orders_data,
            'total_count': len(orders_data),
        }
        
        return request.render('trcf_fnb_inventory.purchase_list_template', vals)

    @http.route('/trcf_fnb_inventory/purchase_add', type='http', auth='user', website=False, methods=['GET', 'POST'], csrf=True)
    def purchase_add(self, **kw):
        if request.httprequest.method == 'POST':
            return self._handle_purchase_submit(kw)
        else:
            return self._render_purchase_form(kw)
    
    def _render_purchase_form(self, kw):
        """Render form với dữ liệu từ database"""
        
        # Lấy company hiện tại
        company_id = request.env.company.id
        
        # Load nhà cung cấp (suppliers)
        suppliers = request.env['res.partner'].sudo().search([
            ('supplier_rank', '>', 0)
        ], order='name')
        
        # Load sản phẩm có thể mua - chỉ lấy sản phẩm của công ty hiện tại hoặc không thuộc công ty nào
        products = request.env['product.product'].sudo().search([
            ('purchase_ok', '=', True),
            '|',  # OR operator
            ('company_id', '=', company_id),  # Sản phẩm của công ty hiện tại
            ('company_id', '=', False)  # Hoặc sản phẩm shared (không thuộc công ty nào)
        ], order='name')
        
        # Load đơn vị tính
        uoms = request.env['uom.uom'].sudo().search([], order='name')
        
        # Tạo mã tham chiếu tự động
        sequence = request.env['ir.sequence'].sudo().search([
            ('code', '=', 'purchase.order')
        ], limit=1)
        
        if sequence:
            reference = sequence.next_by_id()
        else:
            # Fallback nếu không có sequence
            reference = f"PN-{datetime.now().strftime('%Y%m%d')}-{request.env['purchase.order'].sudo().search_count([]) + 1:03d}"
        
        # Lấy ngày giờ hiện tại theo timezone user
        user_tz = pytz.timezone(request.env.user.tz or 'UTC')
        today = datetime.now(user_tz).strftime('%d/%m/%Y %H:%M:%S')
        
        # Load payment methods từ POS (chỉ của công ty hiện tại)
        payment_methods = []
        try:
            company_id = request.env.company.id
            pos_methods = request.env['pos.payment.method'].sudo().search([
                ('company_id', '=', company_id)
            ], order='name')
            payment_methods = [{'id': pm.id, 'name': pm.name} for pm in pos_methods]
        except:
            # Fallback nếu không có module POS
            payment_methods = [
                {'id': 0, 'name': 'Tiền mặt'},
                {'id': 0, 'name': 'Chuyển khoản'},
            ]
        
        vals = {
            'suppliers': suppliers,
            'products': products,
            'uoms': uoms,
            'reference': reference,
            'today': today,
            'payment_methods': payment_methods,
        }
        
        return request.render('trcf_fnb_inventory.purchase_form_template', vals)
    
    def _handle_purchase_submit(self, kw):
        """Xử lý submit form tạo purchase order"""
        
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Lấy dữ liệu từ form
            partner_id = int(kw.get('partner_id', 0))
            reference = kw.get('reference', '')
            notes = kw.get('notes', '')
            action = kw.get('action', 'draft')  # 'draft' hoặc 'confirm'
            
            # Lấy payment fields
            payment_method_id_str = kw.get('payment_method_id', '')
            payment_method_id = int(payment_method_id_str) if payment_method_id_str else False
            payment_status = kw.get('payment_status', 'unpaid')
            payment_date = kw.get('payment_date', '')
            
            # Sử dụng thời gian hiện tại làm date_order (tự động lấy từ create_date)
            date_order_dt = datetime.now()
            
            # Parse payment date (now includes time: DD/MM/YYYY HH:MM:SS)
            payment_date_dt = False
            if payment_date:
                try:
                    # Try parsing with time first (DD/MM/YYYY HH:MM:SS)
                    payment_date_dt = datetime.strptime(payment_date, '%d/%m/%Y %H:%M:%S')
                except:
                    try:
                        # Fallback to date only format (DD/MM/YYYY)
                        payment_date_dt = datetime.strptime(payment_date, '%d/%m/%Y')
                    except:
                        payment_date_dt = False
            
            # Lấy dữ liệu sản phẩm (từ JavaScript sẽ gửi dạng JSON hoặc multiple fields)
            products_data = kw.get('products_data', '[]')
            _logger.info(f"Received products_data (raw): {products_data}")
            
            if isinstance(products_data, str):
                products_data = json.loads(products_data)
            
            _logger.info(f"Parsed products_data: {products_data}")
            
            # Validate
            if not partner_id:
                return request.render('trcf_fnb_inventory.purchase_form_template', {
                    'error': 'Vui lòng chọn nhà cung cấp',
                })
            
            if not products_data or len(products_data) == 0:
                return request.render('trcf_fnb_inventory.purchase_form_template', {
                    'error': 'Vui lòng thêm ít nhất một sản phẩm',
                })
            
            
            # Tạo Purchase Order với company của user hiện tại
            po_vals = {
                'partner_id': partner_id,
                'company_id': request.env.company.id,  # Set company của user hiện tại
                'date_order': date_order_dt,
                'origin': reference,
                'note': notes,
                'trcf_payment_method_id': payment_method_id,
                'trcf_payment_status': payment_status,
                'trcf_payment_date': payment_date_dt,
            }
            
            purchase_order = request.env['purchase.order'].sudo().create(po_vals)
            _logger.info(f"Created purchase order: {purchase_order.id}")
            
            # Tạo Purchase Order Lines
            lines_created = 0
            for product_data in products_data:
                product_id = int(product_data.get('product_id', 0))
                uom_id = int(product_data.get('uom_id', 0))
                qty = float(product_data.get('qty', 0))
                price_unit = float(product_data.get('price_unit', 0))
                vat_percent = float(product_data.get('vat_percent', 0))
                
                _logger.info(f"Processing product: id={product_id}, qty={qty}, price={price_unit}")
                
                if product_id and qty > 0:
                    # Lấy thông tin sản phẩm
                    product = request.env['product.product'].sudo().browse(product_id)
                    
                    # Tạo line
                    line_vals = {
                        'order_id': purchase_order.id,
                        'product_id': product_id,
                        'name': product.name,
                        'product_qty': qty,
                        'product_uom_id': uom_id if uom_id else product.uom_id.id,
                        'price_unit': price_unit,
                        'date_planned': date_order_dt,
                    }
                    
                    _logger.info(f"Creating line with vals: {line_vals}")
                    
                    # Tạo line
                    po_line = request.env['purchase.order.line'].sudo().create(line_vals)
                    lines_created += 1
                    _logger.info(f"Created line: {po_line.id}")
                    
                    # Xử lý VAT nếu có
                    if vat_percent > 0:
                        # Tìm tax theo tỷ lệ
                        tax = request.env['account.tax'].sudo().search([
                            ('amount', '=', vat_percent),
                            ('type_tax_use', '=', 'purchase')
                        ], limit=1)
                        
                        if tax:
                            po_line.sudo().write({'taxes_id': [(6, 0, [tax.id])]})
                else:
                    _logger.warning(f"Skipping product: id={product_id}, qty={qty} (invalid)")
            
            _logger.info(f"Total lines created: {lines_created}")
            
            # Luôn xác nhận đơn hàng để chuyển sang trạng thái 'purchase' (đơn mua hàng)
            # Không còn trạng thái 'draft' (yêu cầu báo giá) nữa
            purchase_order.sudo().button_confirm()
            
            # Redirect về danh sách với thông báo thành công
            return request.redirect('/trcf_fnb_inventory/purchase_list?success=1&po_id=' + str(purchase_order.id))
            
        except Exception as e:
            # Log error và hiển thị thông báo
            import logging
            _logger = logging.getLogger(__name__)
            _logger.error(f"Error creating purchase order: {str(e)}")
            
            return self._render_purchase_form({
                'error': f'Có lỗi xảy ra: {str(e)}',
            })
