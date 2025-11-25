from odoo import http
from odoo.http import request
import pytz
from datetime import datetime, time
import json
import logging

_logger = logging.getLogger(__name__)


class TrcfScrapController(http.Controller):
    """
    Controller for managing inventory scrap/waste operations.
    Handles scrap record creation and listing with automatic stock adjustments.
    """

    @http.route('/trcf_fnb_inventory/scrap_list', type='http', auth='user', website=False)
    def scrap_list(self, **kw):
        """
        Display list of scrap records created today.
        
        Shows all scraps created today for the current company with their status,
        product information, quantities, and reasons.
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
        
        # Get today's scrap records
        scraps = request.env['stock.scrap'].sudo().search([
            ('create_date', '>=', today_start_utc),
            ('create_date', '<=', today_end_utc),
            '|',
            ('company_id', '=', current_company.id),
            ('company_id', '=', False)
        ], order='create_date desc')
        
        # Prepare scrap data for template
        scrap_list = []
        for scrap in scraps:
            # Convert create_date to user timezone
            create_date_utc = pytz.UTC.localize(scrap.create_date)
            create_date_local = create_date_utc.astimezone(tz)
            
            # Get location name
            location_name = scrap.location_id.display_name if scrap.location_id else '-'
            scrap_location_name = scrap.scrap_location_id.display_name if scrap.scrap_location_id else '-'
            
            scrap_list.append({
                'id': scrap.id,
                'name': scrap.name,
                'product_name': scrap.product_id.name,
                'product_qty': scrap.scrap_qty,
                'product_uom': scrap.product_uom_id.name,
                'state': scrap.state,
                'state_display': 'Hoàn thành' if scrap.state == 'done' else 'Nháp',
                'location': location_name,
                'scrap_location': scrap_location_name,
                'reason': scrap.origin or '-',  # Scrap reason stored in origin field
                'create_date': create_date_local.strftime('%H:%M:%S'),
            })
        
        
        values = {
            'scraps': scrap_list,
            'today': datetime.now(tz).strftime('%d/%m/%Y'),
        }
        
        return request.render('trcf_fnb_inventory.scrap_list_template', values)

    @http.route('/trcf_fnb_inventory/scrap_add', type='http', auth='user', website=False, methods=['GET', 'POST'])
    def scrap_add(self, **kw):
        """
        Display form to create new scrap record (GET) or process form submission (POST).
        
        GET: Shows scrap form with available products
        POST: Creates and processes scrap record with automatic stock adjustment
        """
        if request.httprequest.method == 'POST':
            return self._create_scrap_record(kw)
        
        # GET request - show form with available products
        return self._render_scrap_form()
    
    # ==================== Private Helper Methods ====================
    
    def _render_scrap_form(self, error=None, success=None):
        """
        Render the scrap form with available products.
        
        Args:
            error: Optional error message to display
            success: Optional success message to display
            
        Returns:
            Rendered template
        """
        current_company = request.env.company
        
        # Get all products (both storable and consumable can be scrapped)
        products = request.env['product.product'].sudo().search([
            ('active', '=', True),  # Only active products
            '|',
            ('company_id', '=', current_company.id),
            ('company_id', '=', False)
        ], order='name')
        
        
        # Prepare product data for template
        product_list = []
        for product in products:
            product_list.append({
                'id': product.id,
                'name': product.name,
                'uom_id': product.uom_id.id,
                'uom_name': product.uom_id.name,
                'qty_available': product.qty_available,
            })
        
        _logger.info(f"Loaded {len(product_list)} products for scrap form")
        
        # Get scrap reason tags from Odoo
        reason_tags = request.env['stock.scrap.reason.tag'].sudo().search([], order='sequence, name')
        reason_list = []
        for tag in reason_tags:
            reason_list.append({
                'id': tag.id,
                'name': tag.name,
            })
        
        _logger.info(f"Loaded {len(reason_list)} scrap reason tags")
        
        
        
        # Get scrap location (virtual location for scraps)
        # In Odoo, scrap locations typically have usage='inventory' and are virtual
        scrap_location = request.env['stock.location'].sudo().search([
            ('usage', '=', 'inventory'),
            ('name', 'ilike', 'scrap')
        ], limit=1)
        
        # If no scrap location found, try to get any inventory location
        if not scrap_location:
            scrap_location = request.env['stock.location'].sudo().search([
                ('usage', '=', 'inventory')
            ], limit=1)
        
        
        values = {
            'products': product_list,
            'reasons': reason_list,
            'scrap_location_id': scrap_location.id if scrap_location else False,
            'today': datetime.now().strftime('%d/%m/%Y'),
        }
        
        
        if error:
            values['error'] = error
        if success:
            values['success'] = success
        
        return request.render('trcf_fnb_inventory.scrap_form_template', values)
    
    def _create_scrap_record(self, form_data):
        """
        Create and process a scrap record from form data.
        
        Args:
            form_data: Form data from POST request
            
        Returns:
            Redirect to scrap list or error page
        """
        try:
            # Parse form data
            product_id = int(form_data.get('product_id'))
            scrap_qty = float(form_data.get('scrap_qty', 0))
            reason = form_data.get('reason', '').strip()
            
            # If reason is "Khác", use the custom reason text
            if reason == 'Khác':
                other_reason = form_data.get('other_reason', '').strip()
                reason = f"Khác: {other_reason}" if other_reason else 'Khác'
            
            
            # Validate data
            if scrap_qty <= 0:
                return self._render_scrap_form(error='Số lượng hủy phải lớn hơn 0')
            
            # Get product
            product = request.env['product.product'].sudo().browse(product_id)
            if not product.exists():
                return self._render_scrap_form(error='Sản phẩm không tồn tại')
            
            # Get default source location (stock)
            warehouse = request.env['stock.warehouse'].sudo().search([
                ('company_id', '=', request.env.company.id)
            ], limit=1)
            
            source_location = warehouse.lot_stock_id if warehouse else False
            
            # Get scrap location (virtual location for scraps)
            scrap_location = request.env['stock.location'].sudo().search([
                ('usage', '=', 'inventory'),
                ('name', 'ilike', 'scrap')
            ], limit=1)
            
            # If no scrap location found, try to get any inventory location
            if not scrap_location:
                scrap_location = request.env['stock.location'].sudo().search([
                    ('usage', '=', 'inventory')
                ], limit=1)
            
            if not scrap_location:
                return self._render_scrap_form(error='Không tìm thấy kho hủy hàng')
            
            # Create scrap record
            scrap_vals = {
                'product_id': product.id,
                'scrap_qty': scrap_qty,
                'product_uom_id': product.uom_id.id,
                'location_id': source_location.id if source_location else False,
                'scrap_location_id': scrap_location.id,
                'origin': reason or 'TRCF Scrap',  # Store reason in origin field
                'company_id': request.env.company.id,
            }
            
            
            scrap = request.env['stock.scrap'].sudo().create(scrap_vals)
            _logger.info(f"Created scrap {scrap.name} for product {product.name}, qty: {scrap_qty}")
            
            # Process scrap immediately (this will adjust stock)
            scrap.action_validate()
            _logger.info(f"Scrap {scrap.name} validated and stock adjusted")
            
            # Redirect to scrap list
            return request.redirect('/trcf_fnb_inventory/scrap_list')
            
        except ValueError as e:
            error_msg = 'Dữ liệu không hợp lệ. Vui lòng kiểm tra lại.'
            _logger.error(f"Validation error in scrap creation: {str(e)}")
            return self._render_scrap_form(error=error_msg)
            
        except Exception as e:
            error_msg = f'Lỗi khi tạo phiếu hủy: {str(e)}'
            _logger.error(f"Error creating scrap: {str(e)}", exc_info=True)
            return self._render_scrap_form(error=error_msg)
