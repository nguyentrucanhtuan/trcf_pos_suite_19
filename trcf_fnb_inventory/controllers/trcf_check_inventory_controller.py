from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class TrcfCheckInventoryController(http.Controller):

    @http.route('/trcf_fnb_inventory/check_inventory_list', 
                type='http', auth='user', website=False)
    def check_inventory_list(self, **kw):
        """Display inventory check history"""
        # Load inventory check records
        checks = request.env['trcf.inventory.check'].sudo().search(
            [], 
            order='check_date desc',
            limit=50
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
            'templates': template_list,
            'current_user': request.env.user.name,
            'success': success_msg,
        })

    @http.route('/trcf_fnb_inventory/get_template_products', 
                type='json', auth='user')
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
                # Get system quantity from stock.quant
                quants = request.env['stock.quant'].sudo().search([
                    ('product_id', '=', line.product_id.id),
                    ('location_id', '=', template.location_id.id),
                ])
                system_qty = sum(quants.mapped('quantity'))
                
                products.append({
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name,
                    'uom_id': line.uom_id.id,
                    'uom_name': line.uom_id.name,
                    'system_qty': system_qty,
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
                        
                        # Set inventory quantity with context
                        quant.sudo().with_context(
                            inventory_name=check.name
                        ).write({
                            'inventory_quantity': actual_qty,
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
                'templates': template_list,
                'current_user': request.env.user.name,
                'error': f'Lỗi: {str(e)}',
            })
