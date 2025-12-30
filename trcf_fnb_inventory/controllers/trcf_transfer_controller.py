from odoo import http
from odoo.http import request
import pytz
from datetime import datetime, time
import json
import logging

_logger = logging.getLogger(__name__)


class TrcfTransferController(http.Controller):
    """
    Controller for managing internal warehouse transfers.
    Handles transfer creation, listing, and UOM conversion.
    """

    @http.route('/trcf_fnb_inventory/transfer_list', type='http', auth='user', website=False)
    def transfer_list(self, **kw):
        """
        Display list of internal transfers created today.
        
        Shows all internal pickings created today for the current company with their status,
        source/destination locations, and product information.
        """
        # Get current company and timezone
        current_company = request.env.company
        tz = pytz.timezone(request.env.user.tz or 'UTC')
        
        # Get today's date range in user's timezone
        today_start = datetime.combine(datetime.now(tz).date(), time.min)
        today_end = datetime.combine(datetime.now(tz).date(), time.max)
        
        # Convert to UTC for database query
        today_start_utc = tz.localize(today_start).astimezone(pytz.UTC).replace(tzinfo=None)
        today_end_utc = tz.localize(today_end).astimezone(pytz.UTC).replace(tzinfo=None)
        
        # Get today's internal transfers
        transfers = request.env['stock.picking'].sudo().search([
            ('create_date', '>=', today_start_utc),
            ('create_date', '<=', today_end_utc),
            ('picking_type_code', '=', 'internal'),
            '|',
            ('company_id', '=', current_company.id),
            ('company_id', '=', False)
        ], order='create_date desc')
        
        # Prepare transfer data for template
        transfer_list = []
        for transfer in transfers:
            # Convert create_date to user timezone
            create_date_utc = pytz.UTC.localize(transfer.create_date)
            create_date_local = create_date_utc.astimezone(tz)
            
            # Get location names
            source_location = transfer.location_id.display_name if transfer.location_id else '-'
            dest_location = transfer.location_dest_id.display_name if transfer.location_dest_id else '-'
            
            # Get state display
            state_display = dict(transfer._fields['state'].selection).get(transfer.state)
            
            # Count products
            product_count = len(transfer.move_ids)
            
            # Get product summary (first 3 products)
            product_summary = []
            for move in transfer.move_ids[:3]:
                product_summary.append({
                    'name': move.product_id.name,
                    'qty': move.product_uom_qty,
                    'uom': move.product_uom.name,
                })
            
            transfer_list.append({
                'id': transfer.id,
                'name': transfer.name,
                'source_location': source_location,
                'dest_location': dest_location,
                'state': transfer.state,
                'state_display': state_display,
                'create_date': create_date_local.strftime('%H:%M:%S'),
                'product_count': product_count,
                'product_summary': product_summary,
                'origin': transfer.origin or '',
            })
        
        values = {
            'transfers': transfer_list,
            'today': datetime.now(tz).strftime('%d/%m/%Y'),
        }
        
        return request.render('trcf_fnb_inventory.transfer_list_template', values)

    @http.route('/trcf_fnb_inventory/transfer_add', type='http', auth='user', website=False, methods=['GET', 'POST'])
    def transfer_add(self, **kw):
        """
        Display form to create new internal transfer (GET) or process form submission (POST).
        
        GET: Shows transfer form with available products and locations
        POST: Creates and processes internal transfer
        """
        if request.httprequest.method == 'POST':
            return self._create_transfer(kw)
        
        # GET request - show form
        return self._render_transfer_form()
    
    @http.route('/trcf_fnb_inventory/get_product_uoms', type='jsonrpc', auth='user')
    def get_product_uoms(self, product_id):
        """
        AJAX endpoint to get compatible UOMs for a product.
        
        Args:
            product_id: ID of the product to retrieve UOMs for
            
        Returns:
            dict: Success response with product info and compatible UOMs, or error message
        """
        try:
            product = request.env['product.product'].sudo().browse(int(product_id))
            
            if not product.exists():
                return {'error': 'Sản phẩm không tồn tại'}
            
            # Get selectable UOMs: product.uom_id + product.uom_ids
            base_uom = product.uom_id
            secondary_uoms = product.uom_ids
            
            uom_list = []
            
            # Primary UOM
            uom_list.append({
                'id': base_uom.id,
                'name': base_uom.name,
                'factor': base_uom.factor,
                'rounding': base_uom.rounding,
            })
            
            # Secondary UOMs (excluding primary if also in uom_ids)
            for uom in secondary_uoms:
                if uom.id != base_uom.id:
                    uom_list.append({
                        'id': uom.id,
                        'name': uom.name,
                        'factor': uom.factor,
                        'rounding': uom.rounding,
                    })
            
            # Calculate stock display
            # We don't have location here, so we return the base calculation
            # For dynamic updates, the frontend should call /trcf_fnb_inventory/get_location_stock
            qty_available = product.qty_available
            stock_display = f"{qty_available:.2f}".rstrip('0').rstrip('.') + f" {base_uom.name}"
            
            for uom in uom_list:
                if uom['id'] != base_uom.id and uom['factor'] > 0:
                    # Odoo logic: qty in uom = qty in base * (uom.factor / base.factor)
                    converted_qty = qty_available * (base_uom.factor / uom['factor'])
                    stock_display += f" - {converted_qty:.2f}".rstrip('0').rstrip('.') + f" ({uom['name']})"
            
            return {
                'success': True,
                'product': {
                    'id': product.id,
                    'name': product.name,
                    'default_uom_id': product.uom_id.id,
                    'default_uom_name': product.uom_id.name,
                },
                'uoms': uom_list,
                'stock_display': stock_display
            }
        except Exception as e:
            _logger.error(f"Error getting product UOMs: {str(e)}", exc_info=True)
            return {'error': f'Lỗi khi tải thông tin đơn vị: {str(e)}'}

    @http.route('/trcf_fnb_inventory/get_location_stock', type='json', auth='user', methods=['POST'])
    def get_location_stock(self, location_id, **kw):
        """Get product stocks and formatted stock_display for a specific location"""
        try:
            current_company = request.env.company
            location_id = int(location_id)
            
            # Search for storable products
            products = request.env['product.product'].sudo().search([
                ('active', '=', True),
                ('is_storable', '=', True),
                '|',
                ('company_id', '=', current_company.id),
                ('company_id', '=', False)
            ])
            
            # Context for stock calculation
            products_with_context = products.with_context(location=location_id)
            
            product_stocks = []
            for product in products_with_context:
                base_uom = product.uom_id
                qty_available = product.qty_available
                
                # Base stock display
                stock_display = f"{qty_available:.2f}".rstrip('0').rstrip('.') + f" {base_uom.name}"
                
                # Add secondary UOMs from uom_ids
                for uom in product.uom_ids:
                    if uom.id != base_uom.id and uom.factor > 0:
                        converted_qty = qty_available * (base_uom.factor / uom.factor)
                        stock_display += f" - {converted_qty:.2f}".rstrip('0').rstrip('.') + f" ({uom.name})"
                
                product_stocks.append({
                    'id': product.id,
                    'qty_available': qty_available,
                    'stock_display': stock_display
                })
                
            return {
                'success': True,
                'product_stocks': product_stocks
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ==================== Private Helper Methods ====================
    
    def _render_transfer_form(self, error=None):
        """
        Render the transfer form with available products and locations.
        
        Args:
            error: Optional error message to display
            
        Returns:
            Rendered template
        """
        current_company = request.env.company
        IrConfigParam = request.env['ir.config_parameter'].sudo()
        
        # Get internal locations (source and destination)
        internal_locations = request.env['stock.location'].sudo().search([
            ('usage', '=', 'internal'),
            '|',
            ('company_id', '=', current_company.id),
            ('company_id', '=', False)
        ], order='complete_name')
        
        location_list = []
        for loc in internal_locations:
            location_list.append({
                'id': loc.id,
                'name': loc.display_name,
                'complete_name': loc.complete_name,
            })
        
        # Get default locations from settings
        default_source_id = IrConfigParam.get_param('trcf_fnb_inventory.trcf_transfer_source_location_id', default=False)
        default_dest_id = IrConfigParam.get_param('trcf_fnb_inventory.trcf_transfer_dest_location_id', default=False)
        default_source_location_id = int(default_source_id) if default_source_id else False

        # Get all storable products (tracked products)
        products = request.env['product.product'].sudo().search([
            ('active', '=', True),
            ('is_storable', '=', True),  # Only products with "Theo dõi hàng tồn kho" checked
            '|',
            ('company_id', '=', current_company.id),
            ('company_id', '=', False)
        ], order='name')
        
        # Prepare products with context if default_source_location_id is present
        if default_source_location_id:
            products = products.with_context(location=default_source_location_id)

        # Prepare product data for template
        product_list = []
        for product in products:
            # Get selectable UOMs: product.uom_id + product.uom_ids
            base_uom = product.uom_id
            secondary_uoms = product.uom_ids
            
            uom_list = []
            
            # Primary UOM
            uom_list.append({
                'id': base_uom.id,
                'name': base_uom.name,
                'factor': base_uom.factor,
            })
            
            # Secondary UOMs (excluding primary if also in uom_ids)
            for uom in secondary_uoms:
                if uom.id != base_uom.id:
                    uom_list.append({
                        'id': uom.id,
                        'name': uom.name,
                        'factor': uom.factor,
                    })
            
            # Calculate stock display (multi-UoM)
            qty_available = product.qty_available
            stock_display = f"{qty_available:.2f}".rstrip('0').rstrip('.') + f" {base_uom.name}"
            
            for uom in uom_list:
                if uom['id'] != base_uom.id and uom['factor'] > 0:
                    # converted = base_qty * (base_factor / uom_factor)
                    converted_qty = qty_available * (base_uom.factor / uom['factor'])
                    stock_display += f" - {converted_qty:.2f}".rstrip('0').rstrip('.') + f" ({uom['name']})"

            product_list.append({
                'id': product.id,
                'name': product.name,
                'uom_id': product.uom_id.id,
                'uom_name': product.uom_id.name,
                'qty_available': qty_available,
                'stock_display': stock_display,
                'uoms': uom_list,
            })
        
        # Get allow_employee_select setting
        allow_employee_select = IrConfigParam.get_param(
            'trcf_fnb_inventory.trcf_allow_employee_select_transfer', 'False') == 'True'
        
        # Get location names for display
        source_location_name = ''
        dest_location_name = ''
        if default_source_id:
            source_location = request.env['stock.location'].sudo().browse(int(default_source_id))
            if source_location.exists():
                source_location_name = source_location.display_name
        if default_dest_id:
            dest_location = request.env['stock.location'].sudo().browse(int(default_dest_id))
            if dest_location.exists():
                dest_location_name = dest_location.display_name
        
        # Get internal picking type
        picking_type = request.env['stock.picking.type'].sudo().search([
            ('code', '=', 'internal'),
            ('company_id', '=', current_company.id)
        ], limit=1)
        
        values = {
            'products': product_list,
            'locations': location_list,
            'default_source_location_id': int(default_source_id) if default_source_id else False,
            'default_dest_location_id': int(default_dest_id) if default_dest_id else False,
            'source_location_name': source_location_name,
            'dest_location_name': dest_location_name,
            'picking_type_id': picking_type.id if picking_type else False,
            'today': datetime.now().strftime('%d/%m/%Y'),
            'allow_employee_select': allow_employee_select,
        }
        
        if error:
            values['error'] = error
        
        return request.render('trcf_fnb_inventory.transfer_form_template', values)
    
    def _create_transfer(self, form_data):
        """
        Create and process an internal transfer from form data.
        
        Args:
            form_data: Form data from POST request
            
        Returns:
            Redirect to transfer list or error page
        """
        try:
            # Get default locations from settings
            IrConfigParam = request.env['ir.config_parameter'].sudo()
            source_location_id = int(form_data.get('source_location_id', 0)) or int(IrConfigParam.get_param('trcf_fnb_inventory.trcf_transfer_source_location_id', default=0))
            dest_location_id = int(form_data.get('dest_location_id', 0)) or int(IrConfigParam.get_param('trcf_fnb_inventory.trcf_transfer_dest_location_id', default=0))
            picking_type_id = int(form_data.get('picking_type_id', 0))
            products_data = json.loads(form_data.get('products_data', '[]'))
            
            # Validate data
            if not source_location_id:
                return self._render_transfer_form(error='Vui lòng cấu hình kho nguồn mặc định trong Settings')
            
            if not dest_location_id:
                return self._render_transfer_form(error='Vui lòng cấu hình kho đích mặc định trong Settings')
            
            if source_location_id == dest_location_id:
                return self._render_transfer_form(error='Kho nguồn và kho đích không được giống nhau')
            
            if not products_data or len(products_data) == 0:
                return self._render_transfer_form(error='Vui lòng thêm ít nhất một sản phẩm')
            
            if not picking_type_id:
                return self._render_transfer_form(error='Không tìm thấy loại phiếu chuyển kho')
            
            # Create stock picking for internal transfer
            picking_vals = {
                'picking_type_id': picking_type_id,
                'location_id': source_location_id,
                'location_dest_id': dest_location_id,
                'origin': 'TRCF Transfer',
                'company_id': request.env.company.id,
                'move_type': 'direct',  # Deliver all products at once
            }
            
            picking = request.env['stock.picking'].sudo().create(picking_vals)
            _logger.info(f"Created transfer picking {picking.name}")
            
            # Create stock moves for each product
            for product_data in products_data:
                product_id = int(product_data.get('product_id', 0))
                qty = float(product_data.get('qty', 0))
                uom_id = int(product_data.get('uom_id', 0))
                
                if product_id and qty > 0:
                    product = request.env['product.product'].sudo().browse(product_id)
                    
                    move_vals = {
                        'product_id': product_id,
                        'product_uom_qty': qty,
                        'product_uom': uom_id if uom_id else product.uom_id.id,
                        'picking_id': picking.id,
                        'location_id': source_location_id,
                        'location_dest_id': dest_location_id,
                        'company_id': request.env.company.id,
                    }
                    
                    move = request.env['stock.move'].sudo().create(move_vals)
                    _logger.info(f"Created move for {product.name}, qty: {qty}")
            
            # Confirm the picking to make it ready
            picking.action_confirm()
            
            # Set quantities and validate immediately
            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
            
            # Validate the transfer
            picking.button_validate()
            
            _logger.info(f"Transfer {picking.name} validated successfully")
            
            # Redirect to transfer list
            return request.redirect('/trcf_fnb_inventory/transfer_list')
            
        except ValueError as e:
            error_msg = 'Dữ liệu không hợp lệ. Vui lòng kiểm tra lại.'
            _logger.error(f"Validation error in transfer creation: {str(e)}")
            return self._render_transfer_form(error=error_msg)
            
        except Exception as e:
            error_msg = f'Lỗi khi tạo phiếu chuyển kho: {str(e)}'
            _logger.error(f"Error creating transfer: {str(e)}", exc_info=True)
            return self._render_transfer_form(error=error_msg)
