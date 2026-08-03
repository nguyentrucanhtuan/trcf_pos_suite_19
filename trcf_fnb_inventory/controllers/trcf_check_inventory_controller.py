from odoo import http
from odoo.http import request
from datetime import datetime
import calendar
import logging
from ..i18n import get_translator

_logger = logging.getLogger(__name__)


class TrcfCheckInventoryController(http.Controller):

    @http.route('/trcf_fnb_inventory/check_inventory_list', 
                type='http', auth='user', website=False)
    def check_inventory_list(self, **kw):
        """Display inventory check history for current month"""
        # Get current month range
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day = calendar.monthrange(now.year, now.month)[1]
        month_end = now.replace(day=last_day, hour=23, minute=59, second=59, microsecond=0)

        # Load inventory check records for current month
        checks = request.env['trcf.inventory.check'].sudo().search(
            [
                ('check_date', '>=', month_start),
                ('check_date', '<=', month_end)
            ], 
            order='check_date desc'
        )
        
        check_list = []
        for check in checks:
            check_list.append({
                'id': check.id,
                'name': check.name,
                'user_name': check.user_id.name,
                'check_date': check.check_date,
                'warehouse_name': check.location_id.display_name,
                'template_name': check.template_id.name if check.template_id else '',
                'state': check.state,
                'total_difference_value': check.total_difference_value,
                'loss_percentage': check.loss_percentage,
            })
        
        return request.render('trcf_fnb_inventory.check_inventory_list_template', {
            't': get_translator(request),
            'checks': check_list,
        })

    @http.route('/trcf_fnb_inventory/check_inventory_add', 
                type='http', auth='user', website=False, methods=['GET', 'POST'])
    def check_inventory_add(self, **kw):
        """
        GET: Hiển thị form tạo phiếu kiểm với dropdown templates
        POST: Xử lý submit và cập nhật tồn kho
        """
        if request.httprequest.method == 'POST':
            return self._process_inventory_check(kw)
        
        # GET: Load templates
        templates = request.env['trcf.inventory.check.template'].sudo().search([])
        template_list = []
        for t in templates:
            template_list.append({
                'id': t.id,
                'name': t.name,
                'warehouse_id': t.location_id.id,
                'warehouse_name': t.location_id.display_name,
            })
        
        # Check for success message
        success_msg = None
        if kw.get('success'):
            success_msg = 'Phiếu kiểm kho đã được tạo và cập nhật tồn kho thành công!'
        
        return request.render('trcf_fnb_inventory.check_inventory_form_template', {
            't': get_translator(request),
            'templates': template_list,
            'current_user': request.env.user.name,
            'success': success_msg,
        })

    @http.route('/trcf_fnb_inventory/get_template_products', 
                type='jsonrpc', auth='user')
    def get_template_products(self, template_id, **kw):
        """
        AJAX endpoint: Trả về danh sách sản phẩm + tồn kho hệ thống
        """
        try:
            template = request.env['trcf.inventory.check.template'].sudo().browse(
                int(template_id))
            
            if not template.exists():
                return {'error': 'Template không tồn tại'}
            
            products = []
            for line in template.line_ids.sorted('sequence'):
                # Get system quantity from stock.quant (in product's default UoM)
                quants = request.env['stock.quant'].sudo().search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', template.location_id.id),
                ])
                base_qty = sum(quants.mapped('quantity'))
                
                # Convert from product's default UoM to template line's UoM
                base_uom = line.product_id.uom_id
                target_uom = line.uom_id
                if base_uom.id != target_uom.id:
                    system_qty = base_uom._compute_quantity(base_qty, target_uom)
                else:
                    system_qty = base_qty
                
                # Get Orderpoint (Min/Max) - Exact location as requested
                orderpoint = request.env['stock.warehouse.orderpoint'].sudo().search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', template.location_id.id),
                ], limit=1)
                
                def format_uom_display(qty_base, uom_base, uom_target):
                    """Helper to format 'QtyBase UomBase (QtyTarget UomTarget)'"""
                    if qty_base == 0.0:
                        return "0 " + uom_base.name
                        
                    if uom_base.id == uom_target.id:
                        return f"{qty_base:.2f}".rstrip('0').rstrip('.') + f" {uom_base.name}"
                    
                    qty_target = uom_base._compute_quantity(qty_base, uom_target)
                    return (f"{qty_base:.2f}".rstrip('0').rstrip('.') + f" {uom_base.name} "
                            f"({qty_target:.2f}".rstrip('0').rstrip('.') + f" {uom_target.name})")

                min_display = None
                max_display = None
                to_order_display = None
                min_qty_conv = None
                max_qty_conv = None
                
                if orderpoint:
                    orderpoint_min = orderpoint.product_min_qty
                    orderpoint_max = orderpoint.product_max_qty
                    min_display = format_uom_display(orderpoint_min, base_uom, target_uom)
                    max_display = format_uom_display(orderpoint_max, base_uom, target_uom)
                    
                    # Convert to template's UoM for JS comparison
                    if base_uom.id != target_uom.id:
                        min_qty_conv = base_uom._compute_quantity(orderpoint_min, target_uom)
                        max_qty_conv = base_uom._compute_quantity(orderpoint_max, target_uom)
                    else:
                        min_qty_conv = orderpoint_min
                        max_qty_conv = orderpoint_max
                    
                    # Calculate "To Order"
                    if base_qty < orderpoint_min:
                        to_order_qty = orderpoint_max - base_qty
                        to_order_display = format_uom_display(to_order_qty, base_uom, target_uom)

                products.append({
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name,
                    'uom_id': line.uom_id.id,
                    'uom_name': line.uom_id.name,
                    'system_qty_target': system_qty, # For diff calc
                    'system_display': format_uom_display(base_qty, base_uom, target_uom),
                    'system_qty_base': base_qty,     # For color comparison
                    'min_display': min_display,
                    'max_display': max_display,
                    'min_qty_base': orderpoint_min if orderpoint else None,
                    'max_qty_base': orderpoint_max if orderpoint else None,
                    'to_order_display': to_order_display,
                    'sequence': line.sequence,
                })
            
            return {
                'success': True,
                'warehouse_id': template.location_id.id,
                'warehouse_name': template.location_id.display_name,
                'products': products,
            }
            
        except Exception as e:
            _logger.error(f"Error loading template products: {str(e)}", exc_info=True)
            return {'error': str(e)}

    def _process_inventory_check(self, form_data):
        """
        Xử lý submit form: Tạo phiếu kiểm và cập nhật stock.quant
        """
        try:
            template_id = int(form_data.get('template_id'))
            template = request.env['trcf.inventory.check.template'].sudo().browse(
                template_id)
            
            if not template.exists():
                raise ValueError('Template không hợp lệ')
            
            # 1. Create trcf.inventory.check record
            check = request.env['trcf.inventory.check'].sudo().create({
                'template_id': template_id,
                'location_id': template.location_id.id,
                'note': form_data.get('note', ''),
            })
            
            _logger.info(f"Created inventory check: {check.name}")
            
            # 2. Create lines and prepare quants for adjustment
            quants_to_adjust = request.env['stock.quant']
            
            for key, value in form_data.items():
                if key.startswith('actual_qty_'):
                    product_id = int(key.replace('actual_qty_', ''))
                    actual_qty = float(value or 0)
                    system_qty = float(form_data.get(f'system_qty_{product_id}', 0))
                    uom_id = int(form_data.get(f'uom_id_{product_id}'))
                    
                    # Get product to get cost
                    product = request.env['product.product'].sudo().browse(product_id)

                    # Create line
                    request.env['trcf.inventory.check.line'].sudo().create({
                        'check_id': check.id,
                        'product_id': product_id,
                        'uom_id': uom_id,
                        'system_qty': system_qty,
                        'actual_qty': actual_qty,
                        'product_cost': product.standard_price,
                    })
                    
                    # Only adjust if there's a difference
                    if actual_qty != system_qty:
                        # Convert actual_qty from template UoM to product's default UoM
                        template_uom = request.env['uom.uom'].sudo().browse(uom_id)
                        product_uom = product.uom_id
                        
                        if template_uom.id != product_uom.id:
                            actual_qty_in_base_uom = template_uom._compute_quantity(actual_qty, product_uom)
                        else:
                            actual_qty_in_base_uom = actual_qty
                        
                        # Find or create quant
                        quant = request.env['stock.quant'].sudo().search([
                            ('product_id', '=', product_id),
                            ('location_id', '=', template.location_id.id),
                        ], limit=1)

                        if not quant:
                            quant = request.env['stock.quant'].sudo().create({
                                'product_id': product_id,
                                'location_id': template.location_id.id,
                            })
                        
                        # Set inventory quantity with context (in product's default UoM)
                        quant.sudo().with_context(
                            inventory_name=check.name
                        ).write({
                            'inventory_quantity': actual_qty_in_base_uom,
                            'inventory_quantity_set': True,
                        })
                        
                        quants_to_adjust |= quant
            
            # 3. Apply inventory adjustment
            if quants_to_adjust:
                quants_to_adjust.sudo().action_apply_inventory()
                _logger.info(f"Applied inventory for {len(quants_to_adjust)} quants")
            
            # 4. Mark as done
            check.sudo().write({'state': 'done'})
            
            # 5. Redirect to success page
            return request.redirect('/trcf_fnb_inventory/check_inventory_list?success=1')
            
        except Exception as e:
            _logger.error(f"Error processing inventory check: {str(e)}", exc_info=True)
            
            # Reload templates for error page
            templates = request.env['trcf.inventory.check.template'].sudo().search([])
            template_list = [{
                'id': t.id,
                'name': t.name,
                'warehouse_id': t.location_id.id,
                'warehouse_name': t.location_id.display_name,
            } for t in templates]
            
            return request.render('trcf_fnb_inventory.check_inventory_form_template', {
                't': get_translator(request),
                'templates': template_list,
                'current_user': request.env.user.name,
                'error': f'Lỗi: {str(e)}',
            })
