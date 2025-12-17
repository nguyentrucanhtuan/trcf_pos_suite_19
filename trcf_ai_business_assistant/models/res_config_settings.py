# -*- coding: utf-8 -*-
"""
RES CONFIG SETTINGS - Cấu hình quy tắc pha chế
"""
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    # Sử dụng Char thay vì Text vì config_parameter chỉ hỗ trợ:
    # boolean, integer, float, char, selection, many2one, datetime
    drink_creativity_rules = fields.Char(
        string="Quy tắc pha chế",
        help="Các quy tắc mà AI sẽ tuân theo khi gợi ý món sáng tạo",
        config_parameter='trcf_ai.drink_creativity_rules'
    )
    
    drink_trend_period = fields.Integer(
        string="Trend period (ngày)",
        help="Số ngày để tính xu hướng món bán chạy",
        default=30,
        config_parameter='trcf_ai.drink_trend_period'
    )
    
    gemini_api_key = fields.Char(
        string="Google API Key",
        help="API Key để sử dụng Gemini AI",
        config_parameter='trcf.gemini_api_key'
    )
