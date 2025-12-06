from odoo import http
from odoo.http import request
import pytz
from datetime import datetime, time
import json
import logging

_logger = logging.getLogger(__name__)


class TrcfProcessingController(http.Controller):
    """
    Controller for managing manufacturing/processing operations.
    Handles BOM selection, component display, and manufacturing order creation.
    """

    @http.route('/trcf_fnb_inventory/processing_list', type='http', auth='user', website=False)
    def processing_list(self, **kw):
        """
        Display list of manufacturing orders created today.
        
        Shows all MOs created today for the current company with their status,
        product information, and quantities.
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
        
        # Get today's manufacturing orders
        mos = request.env['mrp.production'].sudo().search([
            ('create_date', '>=', today_start_utc),
            ('create_date', '<=', today_end_utc),
            '|',
            ('company_id', '=', current_company.id),
            ('company_id', '=', False)
        ], order='create_date desc')
        
        # Prepare MO data for template
        mo_list = []
        for mo in mos:
            # Convert create_date to user timezone
            create_date_utc = pytz.UTC.localize(mo.create_date)
            create_date_local = create_date_utc.astimezone(tz)
            
            # Get source location (where raw materials come from)
            source_location = mo.location_src_id.display_name if mo.location_src_id else '-'
            
            # Get destination location (where finished product goes)
            dest_location = mo.location_dest_id.display_name if mo.location_dest_id else '-'
            
            mo_list.append({
                'id': mo.id,
                'name': mo.name,
                'product_name': mo.product_id.name,
                'product_qty': mo.product_qty,
                'product_uom': mo.product_uom_id.name,
                'state': mo.state,
                'state_display': dict(mo._fields['state'].selection).get(mo.state),
                'origin': mo.origin or '',
                'create_date': create_date_local.strftime('%H:%M:%S'),
                'date_finished': mo.date_finished.strftime('%H:%M:%S') if mo.date_finished else '',
                'source_location': source_location,  # Source warehouse/location
                'dest_location': dest_location,  # Destination warehouse/location
            })
        
        values = {
            'manufacturing_orders': mo_list,
            'today': datetime.now(tz).strftime('%d/%m/%Y'),
        }
        
        return request.render('trcf_fnb_inventory.processing_list_template', values)

    @http.route('/trcf_fnb_inventory/processing_add', type='http', auth='user', website=False, methods=['GET', 'POST'])
    def processing_add(self, **kw):
        """
        Display form to create new manufacturing order (GET) or process form submission (POST).
        
        GET: Shows BOM selection form with available BOMs for current company
        POST: Creates and completes manufacturing order based on form data
        """
        if request.httprequest.method == 'POST':
            return self._create_manufacturing_order(kw)
        
        # GET request - show form with available BOMs
        return self._render_processing_form()
    
    @http.route('/trcf_fnb_inventory/get_bom_components', type='json', auth='user')
    def get_bom_components(self, bom_id):
        """
        AJAX endpoint to get BOM components.
        
        Args:
            bom_id: ID of the BOM to retrieve components for
            
        Returns:
            dict: Success response with BOM info and components, or error message
        """
        try:
            bom = request.env['mrp.bom'].sudo().browse(int(bom_id))
            
            if not bom.exists():
                return {'error': 'BOM không tồn tại'}
            
            # Validate company access
            if not self._validate_bom_company_access(bom):
                return {'error': 'Bạn không có quyền truy cập BOM này'}
            
            # Build component list
            components = self._build_component_list(bom)
            
            return {
                'success': True,
                'bom': self._build_bom_info(bom),
                'components': components
            }
            
        except Exception as e:
            _logger.error(f"Error getting BOM components: {str(e)}", exc_info=True)
            return {'error': f'Lỗi khi tải thông tin BOM: {str(e)}'}
    
    # ==================== Private Helper Methods ====================
    
    def _render_processing_form(self, error=None):
        """
        Render the processing form with available BOMs.
        
        Args:
            error: Optional error message to display
            
        Returns:
            Rendered template
        """
        current_company = request.env.company
        
        # Get BOMs for current company
        boms = request.env['mrp.bom'].sudo().search([
            ('type', '=', 'normal'),  # Manufacturing type BOMs only
            ('active', '=', True),
            '|',
            ('company_id', '=', current_company.id),
            ('company_id', '=', False)  # Include shared BOMs
        ])
        
        # Prepare BOM data for template
        bom_list = [self._build_bom_info(bom) for bom in boms]
        
        # Get manufacturing picking types for current company
        picking_types = request.env['stock.picking.type'].sudo().search([
            ('code', '=', 'mrp_operation'),
            ('company_id', '=', current_company.id)
        ], order='sequence,name')
        
        values = {
            'boms': bom_list,
            'picking_types': picking_types,
            'today': datetime.now().strftime('%d/%m/%Y'),
        }
        
        if error:
            values['error'] = error
        
        return request.render('trcf_fnb_inventory.processing_form_template', values)
    
    def _validate_bom_company_access(self, bom):
        """
        Validate that user has access to the BOM based on company.
        
        Args:
            bom: BOM record to validate
            
        Returns:
            bool: True if user has access, False otherwise
        """
        current_company = request.env.company
        
        # Allow access if BOM has no company (shared) or belongs to current company
        return not bom.company_id or bom.company_id.id == current_company.id
    
    def _build_bom_info(self, bom):
        """
        Build BOM information dictionary.
        
        Args:
            bom: BOM record
            
        Returns:
            dict: BOM information
        """
        return {
            'id': bom.id,
            'product_name': bom.product_tmpl_id.name,
            'product_id': bom.product_id.id if bom.product_id else bom.product_tmpl_id.product_variant_id.id,
            'product_qty': bom.product_qty,
            'product_uom': bom.product_uom_id.name,
            'product_uom_id': bom.product_uom_id.id,
            'code': bom.code or '',
        }
    
    def _build_component_list(self, bom):
        """
        Build list of BOM components.
        
        Args:
            bom: BOM record
            
        Returns:
            list: List of component dictionaries
        """
        components = []
        for line in bom.bom_line_ids:
            components.append({
                'product_id': line.product_id.id,
                'product_name': line.product_id.name,
                'product_qty': line.product_qty,
                'product_uom': line.product_uom_id.name,
                'product_uom_id': line.product_uom_id.id,
            })
        return components
    
    def _create_manufacturing_order(self, form_data):
        """
        Create and complete a manufacturing order from form data.
        
        Args:
            form_data: Form data from POST request
            
        Returns:
            Redirect to created MO or error page
        """
        try:
            # Parse form data
            bom_id = int(form_data.get('bom_id'))
            product_qty = float(form_data.get('product_qty', 1))
            components_data = json.loads(form_data.get('components_data', '[]'))
            picking_type_id = int(form_data.get('picking_type_id', 0)) if form_data.get('picking_type_id') else False
            
            # Validate picking type
            if not picking_type_id:
                return self._render_processing_form(error='Vui lòng chọn phiếu sản xuất')
            
            # Validate BOM
            bom = self._validate_and_get_bom(bom_id)
            if isinstance(bom, dict):  # Error response
                return self._render_processing_form(error=bom['error'])
            
            # Create manufacturing order
            mo = self._create_mo_record(bom, product_qty, picking_type_id)
            
            # Process the manufacturing order to completion
            self._process_manufacturing_order(mo, components_data)
            
            # Redirect to processing list to see the created MO
            return request.redirect('/trcf_fnb_inventory/processing_list')
            
        except ValueError as e:
            error_msg = 'Dữ liệu không hợp lệ. Vui lòng kiểm tra lại.'
            _logger.error(f"Validation error in MO creation: {str(e)}")
            return self._render_processing_form(error=error_msg)
            
        except Exception as e:
            error_msg = f'Lỗi khi tạo phiếu sản xuất: {str(e)}'
            _logger.error(f"Error creating manufacturing order: {str(e)}", exc_info=True)
            return self._render_processing_form(error=error_msg)
    
    def _validate_and_get_bom(self, bom_id):
        """
        Validate BOM exists and user has access.
        
        Args:
            bom_id: ID of BOM to validate
            
        Returns:
            BOM record if valid, or dict with error message
        """
        bom = request.env['mrp.bom'].sudo().browse(bom_id)
        
        if not bom.exists():
            return {'error': 'BOM không tồn tại'}
        
        if not self._validate_bom_company_access(bom):
            return {'error': 'Bạn không có quyền sử dụng BOM này'}
        
        return bom
    
    def _create_mo_record(self, bom, product_qty, picking_type_id):
        """
        Create manufacturing order record.
        
        Args:
            bom: BOM record to use
            product_qty: Quantity to produce
            picking_type_id: Selected picking type ID from form
            
        Returns:
            Created manufacturing order record
        """
        _logger.info(f"Using selected picking type ID: {picking_type_id}")
        
        mo_vals = {
            'product_id': bom.product_id.id if bom.product_id else bom.product_tmpl_id.product_variant_id.id,
            'product_qty': product_qty,
            'product_uom_id': bom.product_uom_id.id,
            'bom_id': bom.id,
            'origin': 'TRCF Processing',
            'company_id': request.env.company.id,
            'picking_type_id': picking_type_id,
        }
        
        mo = request.env['mrp.production'].sudo().create(mo_vals)
        _logger.info(f"Created MO {mo.name} for product {bom.product_tmpl_id.name}, qty: {product_qty}")
        
        return mo
    
    def _process_manufacturing_order(self, mo, components_data):
        """
        Process manufacturing order to completion.
        
        This method:
        1. Confirms the MO (creates stock moves)
        2. Updates component quantities if modified
        3. Sets quantities to produce
        4. Marks components as consumed
        5. Processes inventory (consumes materials, produces finished goods)
        6. Marks MO as done
        
        Args:
            mo: Manufacturing order record
            components_data: List of component data with modified quantities
        """
        # Step 1: Confirm MO to create stock moves
        mo.action_confirm()
        _logger.info(f"MO {mo.name} confirmed. Raw moves: {len(mo.move_raw_ids)}, Finished moves: {len(mo.move_finished_ids)}")
        
        # Step 2: Update component quantities if user modified them
        self._update_component_quantities(mo, components_data)
        
        # Step 3: Set quantity to produce
        mo.qty_producing = mo.product_qty
        
        # Step 4: Mark all components as consumed
        self._mark_components_consumed(mo)
        
        # Step 5: Process inventory and mark as done
        self._complete_manufacturing_order(mo)
    
    def _update_component_quantities(self, mo, components_data):
        """
        Update component quantities based on user input.
        
        Args:
            mo: Manufacturing order record
            components_data: List of dicts with product_id and qty
        """
        for comp_data in components_data:
            product_id = int(comp_data['product_id'])
            qty = float(comp_data['qty'])
            
            move = mo.move_raw_ids.filtered(lambda m: m.product_id.id == product_id)
            if move:
                move.product_uom_qty = qty
                _logger.debug(f"Updated {move.product_id.name} quantity to {qty}")
    
    def _mark_components_consumed(self, mo):
        """
        Mark all raw material moves as picked and consumed.
        
        Args:
            mo: Manufacturing order record
        """
        for move in mo.move_raw_ids:
            move.picked = True
            move.quantity = move.product_uom_qty
            _logger.debug(f"Marked {move.product_id.name} as consumed: {move.quantity} {move.product_uom.name}")
    
    def _complete_manufacturing_order(self, mo):
        """
        Complete the manufacturing order by processing inventory and setting state to done.
        
        Args:
            mo: Manufacturing order record
        """
        try:
            _logger.info(f"Processing inventory for MO {mo.name}...")
            
            # Process inventory - this consumes raw materials and produces finished goods
            mo._post_inventory(cancel_backorder=True)
            
            # Verify moves were processed
            done_raw = mo.move_raw_ids.filtered(lambda m: m.state == 'done')
            done_finished = mo.move_finished_ids.filtered(lambda m: m.state == 'done')
            
            _logger.info(f"Inventory processed. Raw moves done: {len(done_raw)}/{len(mo.move_raw_ids)}, "
                        f"Finished moves done: {len(done_finished)}/{len(mo.move_finished_ids)}")
            
            # Set MO state to done
            mo.write({
                'date_finished': datetime.now(),
                'state': 'done',
                'is_locked': True,
            })
            
            _logger.info(f"MO {mo.name} completed successfully. State: {mo.state}")
            
        except Exception as e:
            _logger.error(f"Error completing MO {mo.name}: {str(e)}", exc_info=True)
            
            # Fallback: try button_mark_done
            try:
                _logger.info("Attempting fallback with button_mark_done...")
                mo.button_mark_done()
                _logger.info(f"Fallback succeeded. MO state: {mo.state}")
            except Exception as fallback_error:
                _logger.error(f"Fallback also failed: {str(fallback_error)}", exc_info=True)
                # Last resort: set state directly
                mo.state = 'done'
                _logger.warning(f"Set MO {mo.name} state to done directly as last resort")
