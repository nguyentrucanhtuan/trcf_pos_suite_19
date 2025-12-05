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
            
            # Kiểm tra trạng thái nhập kho (receipt status)
            receipt_status = 'waiting'  # Default: chờ nhập kho
            receipt_status_display = 'Chờ nhập kho'
            receipt_color = 'yellow'
            can_receive = False
            
            # Kiểm tra picking liên quan
            if po.picking_ids:
                # Lấy picking đầu tiên (thường chỉ có 1 picking cho mỗi PO)
                picking = po.picking_ids[0]
                
                if picking.state == 'done':
                    # Đã nhập kho
                    receipt_status = 'done'
                    receipt_status_display = 'Đã nhập kho'
                    receipt_color = 'green'
                    can_receive = False
                elif picking.state in ('assigned', 'confirmed', 'waiting'):
                    # Chờ nhập kho
                    receipt_status = 'waiting'
                    receipt_status_display = 'Chờ nhập kho'
                    receipt_color = 'yellow'
                    can_receive = True
            
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
                # Receipt status fields
                'receipt_status': receipt_status,
                'receipt_status_display': receipt_status_display,
                'receipt_color': receipt_color,
                'can_receive': can_receive,
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
        
        # Load sản phẩm có thể mua - chỉ lấy sản phẩm lưu kho của công ty hiện tại hoặc không thuộc công ty nào
        products = request.env['product.product'].sudo().search([
            ('purchase_ok', '=', True),
            ('type', '=', 'consu'),  # Chỉ lấy sản phẩm lưu kho (consumable/goods)
            '|',  # OR operator
            ('company_id', '=', company_id),  # Sản phẩm của công ty hiện tại
            ('company_id', '=', False)  # Hoặc sản phẩm shared (không thuộc công ty nào)
        ], order='name')
        
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
            
            # Lấy picking_type_id từ settings
            picking_type_id_str = request.env['ir.config_parameter'].sudo().get_param(
                'trcf_fnb_inventory.trcf_purchase_picking_type_id', 
                default=False
            )
            
            picking_type_id = int(picking_type_id_str) if picking_type_id_str else False
            
            # Nếu không có cấu hình, fallback về picking type mặc định của company
            if not picking_type_id:
                _logger.warning("No default picking type configured for purchase orders, using company default")
                default_picking_type = request.env['stock.picking.type'].sudo().search([
                    ('code', '=', 'incoming'),
                    ('company_id', '=', request.env.company.id)
                ], limit=1)
                
                if default_picking_type:
                    picking_type_id = default_picking_type.id
                    _logger.info(f"Using fallback picking type: {default_picking_type.name} (ID: {picking_type_id})")
                else:
                    _logger.error("No incoming picking type found for company")
            else:
                _logger.info(f"Using configured picking type ID: {picking_type_id}")
            
            # Tạo Purchase Order với company của user hiện tại
            po_vals = {
                'partner_id': partner_id,
                'company_id': request.env.company.id,  # Set company của user hiện tại
                'picking_type_id': picking_type_id,  # Set picking type từ settings hoặc fallback
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
                tax_id = int(product_data.get('tax_id', 0))
                
                _logger.info(f"Processing product: id={product_id}, qty={qty}, price={price_unit}, tax_id={tax_id}")
                
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
                    
                    # Add tax if selected (tax_id > 0 means a tax was selected)
                    if tax_id > 0:
                        line_vals['tax_ids'] = [(6, 0, [tax_id])]
                    
                    _logger.info(f"Creating line with vals: {line_vals}")
                    
                    # Tạo line
                    po_line = request.env['purchase.order.line'].sudo().create(line_vals)
                    lines_created += 1
                    _logger.info(f"Created line: {po_line.id}")
                else:
                    _logger.warning(f"Skipping product: id={product_id}, qty={qty} (invalid)")
            
            _logger.info(f"Total lines created: {lines_created}")
            
            # Xác nhận đơn hàng để chuyển sang trạng thái 'purchase'
            # Picking sẽ được tạo tự động nhưng chưa validate (chờ xác nhận nhập kho)
            purchase_order.sudo().button_confirm()
            
            _logger.info(f"Purchase order {purchase_order.name} confirmed. Picking created but not validated yet.")
            
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
    
    @http.route('/trcf_fnb_inventory/purchase_receive/<int:po_id>', type='http', auth='user', website=False, methods=['POST'], csrf=True)
    def purchase_receive(self, po_id, **kw):
        """Xác nhận nhập kho cho purchase order"""
        
        import logging
        _logger = logging.getLogger(__name__)
        
        try:
            # Load purchase order
            purchase_order = request.env['purchase.order'].sudo().browse(po_id)
            
            if not purchase_order.exists():
                _logger.error(f"Purchase order {po_id} not found")
                return request.redirect('/trcf_fnb_inventory/purchase_list?error=po_not_found')
            
            _logger.info(f"Processing receipt for PO {purchase_order.name} (ID: {po_id})")
            
            # Kiểm tra picking
            if not purchase_order.picking_ids:
                _logger.error(f"No picking found for PO {purchase_order.name}")
                return request.redirect('/trcf_fnb_inventory/purchase_list?error=no_picking')
            
            # Validate tất cả picking liên quan
            for picking in purchase_order.picking_ids:
                _logger.info(f"Processing picking {picking.name} with state: {picking.state}")
                
                # Chỉ validate picking chưa done
                if picking.state not in ('done', 'cancel'):
                    # Set số lượng thực nhận = số lượng đặt
                    for move in picking.move_ids:
                        if move.state not in ('done', 'cancel'):
                            move.quantity = move.product_uom_qty
                            _logger.info(f"Set quantity for {move.product_id.name}: {move.quantity}")
                    
                    # Validate picking
                    try:
                        res = picking.button_validate()
                        
                        # Xử lý backorder wizard nếu có
                        if isinstance(res, dict) and res.get('res_model') == 'stock.backorder.confirmation':
                            backorder_wizard = request.env['stock.backorder.confirmation'].sudo().browse(res.get('res_id'))
                            backorder_wizard.process_cancel_backorder()
                        
                        _logger.info(f"Picking {picking.name} validated successfully")
                    except Exception as e:
                        _logger.error(f"Error validating picking {picking.name}: {str(e)}")
                        return request.redirect(f'/trcf_fnb_inventory/purchase_list?error=validation_failed&po_id={po_id}')
                else:
                    _logger.info(f"Picking {picking.name} already {picking.state}, skipping")
            
            _logger.info(f"Receipt completed for PO {purchase_order.name}")
            return request.redirect(f'/trcf_fnb_inventory/purchase_list?success=receipt_confirmed&po_id={po_id}')
            
        except Exception as e:
            _logger.error(f"Error processing receipt for PO {po_id}: {str(e)}")
            return request.redirect(f'/trcf_fnb_inventory/purchase_list?error=unknown&message={str(e)}')
