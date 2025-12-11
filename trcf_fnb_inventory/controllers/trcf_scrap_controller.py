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
            
            # Get reason names from scrap_reason_tag_ids (Many2many)
            reason_names = ', '.join(scrap.scrap_reason_tag_ids.mapped('name')) if scrap.scrap_reason_tag_ids else '-'
            
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
                'reason': reason_names,
                'description': scrap.trcf_scrap_description or '-',
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
        IrConfigParam = request.env['ir.config_parameter'].sudo()
        
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
            # Check if product is a Kit (has phantom BoM)
            is_kit = product.is_kits

            # Get all phantom BoMs for this product if it's a Kit
            boms = []
            if is_kit:
                phantom_boms = request.env['mrp.bom'].sudo().search([
                    ('product_id', '=', product.id),
                    ('type', '=', 'phantom'),
                    '|',
                    ('company_id', '=', current_company.id),
                    ('company_id', '=', False)
                ])
                # If no specific product BoM, try template BoM
                if not phantom_boms:
                    phantom_boms = request.env['mrp.bom'].sudo().search([
                        ('product_tmpl_id', '=', product.product_tmpl_id.id),
                        ('product_id', '=', False),
                        ('type', '=', 'phantom'),
                        '|',
                        ('company_id', '=', current_company.id),
                        ('company_id', '=', False)
                    ])

                for bom in phantom_boms:
                    # Get components info
                    components = []
                    for line in bom.bom_line_ids:
                        components.append({
                            'name': line.product_id.name,
                            'qty': line.product_qty,
                            'uom': line.product_uom_id.name,
                        })

                    boms.append({
                        'id': bom.id,
                        'name': bom.code or f"BoM - {product.name}",
                        'components': components,
                    })

            product_list.append({
                'id': product.id,
                'name': product.name,
                'uom_id': product.uom_id.id,
                'uom_name': product.uom_id.name,
                'qty_available': product.qty_available,
                'is_kit': is_kit,
                'boms': boms,
            })
        
        
        _logger.info(f"Loaded {len(product_list)} products for scrap form")
        
        # Get scrap reason tags from Odoo's stock.scrap.reason.tag model
        scrap_reasons = request.env['stock.scrap.reason.tag'].sudo().search([], order='sequence, name')
        reason_list = []
        for reason in scrap_reasons:
            reason_list.append({
                'id': reason.id,
                'name': reason.name,
            })
        
        _logger.info(f"Loaded {len(reason_list)} scrap reason tags from database")
        
        
        
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
        
        # Get available source locations (internal locations)
        source_locations = request.env['stock.location'].sudo().search([
            ('usage', '=', 'internal'),
            '|',
            ('company_id', '=', current_company.id),
            ('company_id', '=', False)
        ], order='name')
        
        source_location_list = []
        for loc in source_locations:
            source_location_list.append({
                'id': loc.id,
                'name': loc.display_name,
            })
        
        _logger.info(f"Loaded {len(source_location_list)} source locations for scrap form")
        
        # Get available scrap locations (inventory/virtual locations)
        scrap_locations = request.env['stock.location'].sudo().search([
            ('usage', '=', 'inventory'),
            '|',
            ('company_id', '=', current_company.id),
            ('company_id', '=', False)
        ], order='name')
        
        scrap_location_list = []
        for loc in scrap_locations:
            scrap_location_list.append({
                'id': loc.id,
                'name': loc.display_name,
            })
        
        # Lấy setting cho phép nhân viên chọn và default locations
        allow_employee_select = IrConfigParam.get_param(
            'trcf_fnb_inventory.trcf_allow_employee_select_scrap', 'False') == 'True'
        default_source_location_id = IrConfigParam.get_param(
            'trcf_fnb_inventory.trcf_scrap_location_id', default=False)
        default_scrap_location_id = IrConfigParam.get_param(
            'trcf_fnb_inventory.trcf_scrap_dest_location_id', default=False)
        
        # Lấy thông tin default locations để hiển thị
        default_source_location_name = ''
        if default_source_location_id:
            default_src = request.env['stock.location'].sudo().browse(int(default_source_location_id))
            if default_src.exists():
                default_source_location_name = default_src.display_name
        
        default_scrap_location_name = ''
        if default_scrap_location_id:
            default_scrap = request.env['stock.location'].sudo().browse(int(default_scrap_location_id))
            if default_scrap.exists():
                default_scrap_location_name = default_scrap.display_name
        
        values = {
            'products': product_list,
            'reasons': reason_list,
            'source_locations': source_location_list,
            'scrap_locations': scrap_location_list,
            'scrap_location_id': scrap_location.id if scrap_location else False,
            'today': datetime.now().strftime('%d/%m/%Y'),
            'allow_employee_select': allow_employee_select,
            'default_source_location_id': int(default_source_location_id) if default_source_location_id else False,
            'default_source_location_name': default_source_location_name,
            'default_scrap_location_id': int(default_scrap_location_id) if default_scrap_location_id else False,
            'default_scrap_location_name': default_scrap_location_name,
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
            reason_id = int(form_data.get('reason_id', 0)) if form_data.get('reason_id') else False
            description = form_data.get('description', '').strip()
            bom_id = int(form_data.get('bom_id', 0)) if form_data.get('bom_id') else False

            # Validate data
            if scrap_qty <= 0:
                return self._render_scrap_form(error='Số lượng hủy phải lớn hơn 0')

            # Get product
            product = request.env['product.product'].sudo().browse(product_id)
            if not product.exists():
                return self._render_scrap_form(error='Sản phẩm không tồn tại')

            # Validate BoM for Kit products
            if product.is_kits and not bom_id:
                return self._render_scrap_form(error='Sản phẩm này là Kit, vui lòng chọn BoM (công thức sản xuất)')
            
            # Get source location from form
            source_location_id = int(form_data.get('source_location_id', 0)) if form_data.get('source_location_id') else False
            
            if not source_location_id:
                return self._render_scrap_form(error='Vui lòng chọn vị trí kho nguồn')
            
            # Fallback to warehouse stock location if not configured
            if not source_location_id:
                _logger.warning("No scrap source location configured in settings, using warehouse default")
                warehouse = request.env['stock.warehouse'].sudo().search([
                    ('company_id', '=', request.env.company.id)
                ], limit=1)
                source_location = warehouse.lot_stock_id if warehouse else False
                source_location_id = source_location.id if source_location else False
            
            # Get scrap destination location from settings
            scrap_location_id_str = request.env['ir.config_parameter'].sudo().get_param(
                'trcf_fnb_inventory.trcf_scrap_dest_location_id',
                default=False
            )
            scrap_location_id = int(scrap_location_id_str) if scrap_location_id_str else False
            
            # Fallback to finding scrap location if not configured
            if not scrap_location_id:
                _logger.warning("No scrap destination location configured in settings, searching for scrap location")
                scrap_location = request.env['stock.location'].sudo().search([
                    ('scrap_location', '=', True)
                ], limit=1)
                
                # If still not found, try inventory usage
                if not scrap_location:
                    scrap_location = request.env['stock.location'].sudo().search([
                        ('usage', '=', 'inventory'),
                        ('name', 'ilike', 'scrap')
                    ], limit=1)
                
                scrap_location_id = scrap_location.id if scrap_location else False
            
            if not scrap_location_id:
                return self._render_scrap_form(error='Không tìm thấy kho hủy hàng. Vui lòng cấu hình trong Settings.')
            
            _logger.info(f"Using source location ID: {source_location_id}, scrap location ID: {scrap_location_id}")
            
            # Create scrap record
            scrap_vals = {
                'product_id': product.id,
                'scrap_qty': scrap_qty,
                'product_uom_id': product.uom_id.id,
                'location_id': source_location_id,
                'scrap_location_id': scrap_location_id,
                'scrap_reason_tag_ids': [(6, 0, [reason_id])] if reason_id else False,  # Many2many field
                'trcf_scrap_description': description,  # Save description
                'company_id': request.env.company.id,
            }

            # Add BoM if product is Kit
            if product.is_kits and bom_id:
                scrap_vals['bom_id'] = bom_id
            

            # For Kit products, we need to scrap components individually
            if product.is_kits and bom_id:
                bom = request.env['mrp.bom'].sudo().browse(bom_id)
                if not bom.exists():
                    return self._render_scrap_form(error='BoM không tồn tại')

                _logger.info(f"Creating scrap for Kit product {product.name} with BoM {bom.display_name}")

                # Explode the BoM to get components
                factor = scrap_qty / bom.product_qty
                boms, bom_lines = bom.explode(product, factor)

                # Create scrap for each component
                created_scraps = []
                for bom_line, line_data in bom_lines:
                    component = bom_line.product_id
                    component_qty = line_data['qty']

                    # Skip if quantity is zero or product is service
                    if component_qty <= 0 or component.type == 'service':
                        continue

                    component_scrap_vals = {
                        'product_id': component.id,
                        'scrap_qty': component_qty,
                        'product_uom_id': bom_line.product_uom_id.id,
                        'location_id': source_location_id,
                        'scrap_location_id': scrap_location_id,
                        'scrap_reason_tag_ids': [(6, 0, [reason_id])] if reason_id else False,
                        'trcf_scrap_description': f"[Kit: {product.name}] {description}",
                        'company_id': request.env.company.id,
                        'origin': f"Kit {product.name}",
                    }

                    component_scrap = request.env['stock.scrap'].sudo().create(component_scrap_vals)
                    component_scrap.action_validate()
                    created_scraps.append(component_scrap)
                    _logger.info(f"Created and validated scrap for component {component.name}, qty: {component_qty}")

                _logger.info(f"Successfully scrapped Kit {product.name}: {len(created_scraps)} components processed")

            else:
                # Normal product - create single scrap
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
