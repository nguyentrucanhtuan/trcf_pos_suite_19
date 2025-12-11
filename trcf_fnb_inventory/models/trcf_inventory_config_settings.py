# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TrcfInventoryConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # Purchase settings
    trcf_purchase_picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Loại phiếu nhập kho mặc định',
        domain="[('code', '=', 'incoming'), ('company_id', '=', company_id)]",
        help='Chọn loại phiếu nhập kho sẽ được sử dụng khi tạo đơn mua hàng. Kho đích sẽ được lấy từ cấu hình của loại phiếu này.'
    )
    trcf_allow_employee_select_purchase = fields.Boolean(
        string='Cho phép nhân viên chọn phiếu nhập kho',
        help='Nếu bật, nhân viên có thể chọn phiếu nhập kho. Nếu tắt, sử dụng giá trị mặc định.'
    )
    
    # Scrap settings
    trcf_scrap_location_id = fields.Many2one(
        'stock.location',
        string='Vị trí kho nguồn cho huỷ hàng',
        domain="[('usage', '=', 'internal'), ('company_id', 'in', [company_id, False])]",
        help='Kho mà hàng sẽ được lấy ra để huỷ (ví dụ: WH/Stock)'
    )
    
    trcf_scrap_dest_location_id = fields.Many2one(
        'stock.location',
        string='Vị trí kho đích cho hàng huỷ',
        domain="[('usage', '=', 'inventory'), ('company_id', 'in', [company_id, False])]",
        help='Kho ảo để chứa hàng đã huỷ (thường là Virtual Locations/Scrap)'
    )
    trcf_allow_employee_select_scrap = fields.Boolean(
        string='Cho phép nhân viên chọn kho huỷ hàng',
        help='Nếu bật, nhân viên có thể chọn kho nguồn và kho ảo. Nếu tắt, sử dụng giá trị mặc định.'
    )
    
    # Processing/Manufacturing settings
    trcf_processing_picking_type_id = fields.Many2one(
        'stock.picking.type',
        string='Loại phiếu sản xuất mặc định',
        domain="[('code', '=', 'mrp_operation'), ('company_id', '=', company_id)]",
        help='Chọn loại phiếu sản xuất sẽ được sử dụng khi tạo lệnh sản xuất. Kho nguồn và kho đích sẽ được lấy từ cấu hình của loại phiếu này.'
    )
    trcf_allow_employee_select_processing = fields.Boolean(
        string='Cho phép nhân viên chọn phiếu chế biến',
        help='Nếu bật, nhân viên có thể chọn phiếu chế biến. Nếu tắt, sử dụng giá trị mặc định.'
    )
    
    # Transfer settings
    trcf_transfer_source_location_id = fields.Many2one(
        'stock.location',
        string='Vị trí kho nguồn mặc định cho chuyển kho',
        domain="[('usage', '=', 'internal'), ('company_id', 'in', [company_id, False])]",
        help='Kho nguồn mặc định khi tạo phiếu chuyển kho'
    )
    
    trcf_transfer_dest_location_id = fields.Many2one(
        'stock.location',
        string='Vị trí kho đích mặc định cho chuyển kho',
        domain="[('usage', '=', 'internal'), ('company_id', 'in', [company_id, False])]",
        help='Kho đích mặc định khi tạo phiếu chuyển kho'
    )
    trcf_allow_employee_select_transfer = fields.Boolean(
        string='Cho phép nhân viên chọn kho chuyển',
        help='Nếu bật, nhân viên có thể chọn kho nguồn và kho đích. Nếu tắt, sử dụng giá trị mặc định.'
    )

    
    @api.model
    def get_values(self):
        res = super(TrcfInventoryConfigSettings, self).get_values()
        
        # Lấy giá trị purchase picking type
        picking_type_id = self.env['ir.config_parameter'].sudo().get_param(
            'trcf_fnb_inventory.trcf_purchase_picking_type_id',
            default=False
        )
        if picking_type_id:
            res['trcf_purchase_picking_type_id'] = int(picking_type_id)
        
        # Lấy giá trị scrap location
        scrap_location_id = self.env['ir.config_parameter'].sudo().get_param(
            'trcf_fnb_inventory.trcf_scrap_location_id',
            default=False
        )
        if scrap_location_id:
            res['trcf_scrap_location_id'] = int(scrap_location_id)
        
        # Lấy giá trị scrap destination location
        scrap_dest_location_id = self.env['ir.config_parameter'].sudo().get_param(
            'trcf_fnb_inventory.trcf_scrap_dest_location_id',
            default=False
        )
        if scrap_dest_location_id:
            res['trcf_scrap_dest_location_id'] = int(scrap_dest_location_id)
        
        # Lấy giá trị processing picking type
        processing_picking_type_id = self.env['ir.config_parameter'].sudo().get_param(
            'trcf_fnb_inventory.trcf_processing_picking_type_id',
            default=False
        )
        if processing_picking_type_id:
            res['trcf_processing_picking_type_id'] = int(processing_picking_type_id)
        
        # Lấy giá trị transfer source location
        transfer_source_location_id = self.env['ir.config_parameter'].sudo().get_param(
            'trcf_fnb_inventory.trcf_transfer_source_location_id',
            default=False
        )
        if transfer_source_location_id:
            res['trcf_transfer_source_location_id'] = int(transfer_source_location_id)
        
        # Lấy giá trị transfer destination location
        transfer_dest_location_id = self.env['ir.config_parameter'].sudo().get_param(
            'trcf_fnb_inventory.trcf_transfer_dest_location_id',
            default=False
        )
        if transfer_dest_location_id:
            res['trcf_transfer_dest_location_id'] = int(transfer_dest_location_id)
        
        # Lấy giá trị cho phép nhân viên chọn
        res['trcf_allow_employee_select_purchase'] = self.env['ir.config_parameter'].sudo().get_param(
            'trcf_fnb_inventory.trcf_allow_employee_select_purchase', 'False') == 'True'
        res['trcf_allow_employee_select_scrap'] = self.env['ir.config_parameter'].sudo().get_param(
            'trcf_fnb_inventory.trcf_allow_employee_select_scrap', 'False') == 'True'
        res['trcf_allow_employee_select_processing'] = self.env['ir.config_parameter'].sudo().get_param(
            'trcf_fnb_inventory.trcf_allow_employee_select_processing', 'False') == 'True'
        res['trcf_allow_employee_select_transfer'] = self.env['ir.config_parameter'].sudo().get_param(
            'trcf_fnb_inventory.trcf_allow_employee_select_transfer', 'False') == 'True'
        
        return res
    
    def set_values(self):
        super(TrcfInventoryConfigSettings, self).set_values()
        
        # Lưu purchase picking type
        self.env['ir.config_parameter'].sudo().set_param(
            'trcf_fnb_inventory.trcf_purchase_picking_type_id',
            self.trcf_purchase_picking_type_id.id if self.trcf_purchase_picking_type_id else False
        )
        
        # Lưu scrap location
        self.env['ir.config_parameter'].sudo().set_param(
            'trcf_fnb_inventory.trcf_scrap_location_id',
            self.trcf_scrap_location_id.id if self.trcf_scrap_location_id else False
        )
        
        # Lưu scrap destination location
        self.env['ir.config_parameter'].sudo().set_param(
            'trcf_fnb_inventory.trcf_scrap_dest_location_id',
            self.trcf_scrap_dest_location_id.id if self.trcf_scrap_dest_location_id else False
        )
        
        # Lưu processing picking type
        self.env['ir.config_parameter'].sudo().set_param(
            'trcf_fnb_inventory.trcf_processing_picking_type_id',
            self.trcf_processing_picking_type_id.id if self.trcf_processing_picking_type_id else False
        )
        
        # Lưu transfer source location
        self.env['ir.config_parameter'].sudo().set_param(
            'trcf_fnb_inventory.trcf_transfer_source_location_id',
            self.trcf_transfer_source_location_id.id if self.trcf_transfer_source_location_id else False
        )
        
        # Lưu transfer destination location
        self.env['ir.config_parameter'].sudo().set_param(
            'trcf_fnb_inventory.trcf_transfer_dest_location_id',
            self.trcf_transfer_dest_location_id.id if self.trcf_transfer_dest_location_id else False
        )
        
        # Lưu các giá trị cho phép nhân viên chọn
        self.env['ir.config_parameter'].sudo().set_param(
            'trcf_fnb_inventory.trcf_allow_employee_select_purchase',
            str(self.trcf_allow_employee_select_purchase)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'trcf_fnb_inventory.trcf_allow_employee_select_scrap',
            str(self.trcf_allow_employee_select_scrap)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'trcf_fnb_inventory.trcf_allow_employee_select_processing',
            str(self.trcf_allow_employee_select_processing)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'trcf_fnb_inventory.trcf_allow_employee_select_transfer',
            str(self.trcf_allow_employee_select_transfer)
        )
