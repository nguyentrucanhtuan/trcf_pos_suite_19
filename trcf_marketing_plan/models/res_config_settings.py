# -*- coding: utf-8 -*-
"""
Settings cho Marketing Plan
Lưu ý: config_parameter chỉ hỗ trợ Char, không hỗ trợ Text
Vì vậy dùng get/set thủ công
"""
from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Customer Persona - dùng Char (short version sẽ hiển thị preview)
    marketing_customer_persona = fields.Char(
        string="Customer Persona",
        config_parameter='trcf.marketing.content.customer_persona',
        help="Chan dung khach hang muc tieu"
    )
    
    # Brand Key
    marketing_brand_key = fields.Char(
        string="Brand Key",
        config_parameter='trcf.marketing.content.brand_key',
        help="The manh va gia tri cot loi thuong hieu"
    )
    
    # Customer Journey
    marketing_customer_journey = fields.Char(
        string="Customer Journey",
        config_parameter='trcf.marketing.content.customer_journey',
        help="5 giai doan: Awareness, Consideration, Purchase, Retention, Advocacy"
    )
    
    # Business Goals
    marketing_goals_current = fields.Char(
        string="Business Goals",
        config_parameter='trcf.marketing.content.goals_current',
        help="Muc tieu kinh doanh hien tai"
    )
    
    # Gemini API Key
    marketing_gemini_api_key = fields.Char(
        string="Gemini API Key",
        config_parameter='trcf.marketing.content.gemini_api_key',
        help="Google Gemini API Key cho AI Agent"
    )
