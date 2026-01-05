# -*- coding: utf-8 -*-
from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    trcf_gemini_api_key = fields.Char(
        string='Gemini API Key',
        config_parameter='trcf.gemini_api_key',
        help="Google API Key for Gemini models via Google ADK"
    )
