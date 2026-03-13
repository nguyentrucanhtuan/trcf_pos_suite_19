# -*- coding: utf-8 -*-
from odoo import models, fields, api


class TrcfOpsAuditConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    trcf_ops_shop_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Kho quầy (Shop)',
        help='Chọn kho quầy — là kho lưu nguyên liệu với đơn vị nhỏ (gram). '
             'Các kho còn lại sẽ được coi là kho chính (đơn vị lớn: Kg, Thùng, Chai).',
    )

    @api.model
    def get_values(self):
        res = super().get_values()
        shop_wh_id = self.env['ir.config_parameter'].sudo().get_param(
            'trcf_ops_audit.trcf_ops_shop_warehouse_id', default=False
        )
        if shop_wh_id:
            res['trcf_ops_shop_warehouse_id'] = int(shop_wh_id)
        return res

    def set_values(self):
        super().set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'trcf_ops_audit.trcf_ops_shop_warehouse_id',
            self.trcf_ops_shop_warehouse_id.id if self.trcf_ops_shop_warehouse_id else False
        )
